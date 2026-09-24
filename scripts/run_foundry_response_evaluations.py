"""Score completed local-tool agent interactions in Microsoft Foundry."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from azure.ai.projects.models import TestingCriterionAzureAIEvaluator  # noqa: E402
from mama_link import telemetry  # noqa: E402
from mama_link.foundry import MANIFEST, project_client, run_agent, validated_settings  # noqa: E402
from scripts.run_foundry_evaluations import CASES, REPORT_PATH, estimated_tokens, serialize  # noqa: E402


def response_criteria(deployment: str) -> list:
    return [
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="Intent Resolution",
            evaluator_name="builtin.intent_resolution",
            initialization_parameters={"model": deployment},
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="Tool Call Accuracy",
            evaluator_name="builtin.tool_call_accuracy",
            initialization_parameters={"model": deployment},
        ),
        TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name="Tool Input Accuracy",
            evaluator_name="builtin.tool_input_accuracy",
            initialization_parameters={"model": deployment},
        ),
    ]


def run(max_combined_estimated_tokens: int, poll_seconds: int, roles: list[str]) -> dict:
    settings = validated_settings()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    selected_cases = {role: CASES[role] for role in roles}
    retry_estimate = sum(estimated_tokens(len(case_ids), 3) for case_ids in selected_cases.values())
    prior_completed = report.get("completed_response_evaluations", [])
    prior_retry_estimate = report.get("retry_estimated_token_ceiling", 0)
    # The first completed-response pass replaces target rows that Foundry skipped; it does not
    # expand the original 24-row plan. Later role-specific reruns are additional work.
    combined_estimate = report.get("estimated_token_ceiling", 0)
    if prior_completed:
        combined_estimate += prior_retry_estimate + retry_estimate
    if combined_estimate > max_combined_estimated_tokens:
        raise ValueError(
            f"Combined estimate {combined_estimate} exceeds cap {max_combined_estimated_tokens}."
        )

    telemetry.configure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    completed_responses: dict[str, list[str]] = {}
    response_runs = []

    with project_client(settings) as project:
        with project.get_openai_client() as client:
            for role, case_ids in selected_cases.items():
                reference = manifest["agents"][role]
                response_ids = []
                for case_id in case_ids:
                    result = run_agent(client, reference, role, case_id)
                    if not result.get("response_id"):
                        raise RuntimeError(f"{role}/{case_id} did not return a stored response ID.")
                    response_ids.append(result["response_id"])
                    print(f"CAPTURED {role}/{case_id}", flush=True)
                completed_responses[role] = response_ids

            criteria = response_criteria(settings["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
            active = []
            for role, response_ids in completed_responses.items():
                reference = manifest["agents"][role]
                evaluation = client.evals.create(
                    name=f"MAMA-Link {role.replace('_', ' ').title()} Completed Workflow Baseline",
                    data_source_config={"type": "azure_ai_source", "scenario": "responses"},
                    testing_criteria=criteria,
                    metadata={
                        "project": "MAMA-Link",
                        "role": role,
                        "agent_name": reference["name"],
                        "agent_version": reference["version"],
                        "dataset": "synthetic",
                        "method": "completed_responses",
                    },
                )
                evaluation_run = client.evals.runs.create(
                    eval_id=evaluation.id,
                    name=f"{role.replace('_', ' ').title()} completed workflow {stamp}",
                    data_source={
                        "type": "azure_ai_responses",
                        "item_generation_params": {
                            "type": "response_retrieval",
                            "data_mapping": {"response_id": "{{item.resp_id}}"},
                            "source": {
                                "type": "file_content",
                                "content": [
                                    {"item": {"resp_id": response_id}}
                                    for response_id in response_ids
                                ],
                            },
                        },
                    },
                    metadata={
                        "project": "MAMA-Link",
                        "role": role,
                        "agent_name": reference["name"],
                        "agent_version": reference["version"],
                        "synthetic": "true",
                    },
                )
                entry = {
                    "role": role,
                    "agent": reference,
                    "method": "completed_responses",
                    "row_count": len(response_ids),
                    "evaluators": ["Intent Resolution", "Tool Call Accuracy", "Tool Input Accuracy"],
                    "evaluation_id": evaluation.id,
                    "run_id": evaluation_run.id,
                    "status": evaluation_run.status,
                }
                response_runs.append(entry)
                active.append((entry, evaluation.id, evaluation_run.id))
                print(f"STARTED {role}: eval={evaluation.id} run={evaluation_run.id}", flush=True)

            while active:
                remaining = []
                for entry, evaluation_id, run_id in active:
                    current = client.evals.runs.retrieve(eval_id=evaluation_id, run_id=run_id)
                    entry["status"] = current.status
                    if current.status in {"completed", "failed", "canceled"}:
                        entry["report_url"] = getattr(current, "report_url", None)
                        entry["result_counts"] = serialize(getattr(current, "result_counts", None))
                        entry["per_model_usage"] = serialize(getattr(current, "per_model_usage", None))
                        entry["per_testing_criteria_results"] = serialize(
                            getattr(current, "per_testing_criteria_results", None)
                        )
                        entry["error"] = serialize(getattr(current, "error", None))
                        print(f"FINISHED {entry['role']}: {current.status} {entry['result_counts']}", flush=True)
                    else:
                        remaining.append((entry, evaluation_id, run_id))
                active = remaining
                if active:
                    print(f"WAITING {len(active)} completed-response runs", flush=True)
                    time.sleep(poll_seconds)

    if prior_completed:
        selected = set(selected_cases)
        superseded = [entry for entry in prior_completed if entry["role"] in selected]
        if superseded:
            report.setdefault("superseded_evaluations", []).extend(superseded)
        response_runs = [entry for entry in prior_completed if entry["role"] not in selected] + response_runs
        report["retry_estimated_token_ceiling"] = prior_retry_estimate + retry_estimate
    else:
        report["retry_estimated_token_ceiling"] = 0
    report["completed_response_evaluations"] = response_runs
    report.pop("additional_estimated_token_ceiling", None)
    report["effective_estimated_token_ceiling"] = combined_estimate
    report.pop("combined_estimated_token_ceiling", None)
    report["configured_cap"] = max_combined_estimated_tokens
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    telemetry.force_flush()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate completed MAMA-Link tool-agent responses.")
    parser.add_argument("--max-combined-estimated-tokens", type=int, default=500_000)
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--roles", nargs="+", choices=sorted(CASES), default=sorted(CASES))
    args = parser.parse_args()
    report = run(args.max_combined_estimated_tokens, args.poll_seconds, args.roles)
    runs = report["completed_response_evaluations"]
    failed_runs = [entry for entry in runs if entry["status"] != "completed"]
    print(json.dumps({
        "effective_estimated_token_ceiling": report["effective_estimated_token_ceiling"],
        "completed_runs": len(runs) - len(failed_runs),
        "failed_runs": len(failed_runs),
        "report": str(REPORT_PATH),
    }, indent=2))
    return 1 if failed_runs else 0


if __name__ == "__main__":
    raise SystemExit(main())
