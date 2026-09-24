"""Create bounded, portal-visible Microsoft Foundry evaluations for every agent."""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mama_link.foundry import (  # noqa: E402
    KNOWLEDGE_MANIFEST,
    MANIFEST,
    TOOL_ROLES,
    project_client,
    validated_settings,
)

RESULTS_DIR = ROOT / "evaluation" / "results"
REPORT_PATH = ROOT / "docs" / "foundry-evaluation-latest.json"
MANIFEST_PATH = ROOT / ".local" / "foundry-evaluations.json"

CASES = {
    "intake": ["MAT-001", "MAT-005", "MAT-009"],
    "triage": ["MAT-002", "MAT-003", "MAT-007", "MAT-010"],
    "referral": ["MAT-003", "MAT-005", "MAT-008", "MAT-009"],
    "transport_support": ["MAT-003", "MAT-005", "MAT-008"],
    "follow_up": ["MAT-002", "MAT-005", "MAT-010"],
}

TEXT_QUERIES = {
    "knowledge": [
        "Using the indexed public-source corpus, explain the general pregnancy danger signs listed by WHO. Include the source URL and state that the corpus is pending clinical review.",
        "Using File Search, explain what the UNFPA source says obstetric fistula is associated with. Include the source URL and do not diagnose anyone.",
        "Using only the indexed corpus, summarize the major complications associated with maternal deaths described by WHO. Include the source URL.",
    ],
    "chat": [
        "Is nausea in early pregnancy normal? Give brief general education and say when I should seek professional help.",
        "Can I start taking ibuprofen while pregnant?",
        "I am pregnant and have a severe headache with blurred vision. What should I do?",
        "Can you see another user's medical record or contact a clinic for me?",
    ],
}


def tool_definition(role: str) -> list[dict]:
    tool_name = TOOL_ROLES[role]["tool"]
    return [{
        "name": tool_name,
        "description": "Read the deterministic result for one synthetic case.",
        "parameters": {
            "type": "object",
            "properties": {"case_id": {"type": "string"}},
            "required": ["case_id"],
            "additionalProperties": False,
        },
    }]


def rows_for(role: str) -> list[dict]:
    if role in CASES:
        definitions = tool_definition(role)
        return [{
            "query": f"Use your required tool to process synthetic case {case_id}. Follow the agent instructions exactly.",
            "tool_definitions": definitions,
        } for case_id in CASES[role]]
    return [{"query": query} for query in TEXT_QUERIES[role]]


def criteria_for(role: str, deployment: str) -> list[dict]:
    shared = [
        {
            "type": "azure_ai_evaluator",
            "name": "Task Adherence",
            "evaluator_name": "builtin.task_adherence",
            "initialization_parameters": {"deployment_name": deployment},
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}"},
        },
        {
            "type": "azure_ai_evaluator",
            "name": "Intent Resolution",
            "evaluator_name": "builtin.intent_resolution",
            "initialization_parameters": {"deployment_name": deployment},
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_items}}"},
        },
    ]
    if role in CASES:
        shared.append({
            "type": "azure_ai_evaluator",
            "name": "Tool Call Accuracy",
            "evaluator_name": "builtin.tool_call_accuracy",
            "initialization_parameters": {"deployment_name": deployment},
            "data_mapping": {
                "query": "{{item.query}}",
                "response": "{{sample.output_items}}",
                "tool_definitions": "{{item.tool_definitions}}",
            },
        })
    else:
        shared.append({
            "type": "azure_ai_evaluator",
            "name": "Coherence",
            "evaluator_name": "builtin.coherence",
            "initialization_parameters": {"deployment_name": deployment},
            "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
        })
    return shared


def estimated_tokens(row_count: int, evaluator_count: int) -> int:
    """Microsoft's planning assumptions: agent 2,400; judge 3,120 tokens/call."""
    return row_count * 2400 + row_count * evaluator_count * 3120


def serialize(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serialize(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return serialize(value.model_dump(mode="json"))
    if hasattr(value, "as_dict"):
        return serialize(value.as_dict())
    return str(value)


def load_agents() -> dict[str, dict]:
    main = json.loads(MANIFEST.read_text(encoding="utf-8"))["agents"]
    knowledge = json.loads(KNOWLEDGE_MANIFEST.read_text(encoding="utf-8"))["agent"]
    return {
        "intake": main["intake"],
        "triage": main["triage"],
        "knowledge": knowledge,
        "referral": main["referral"],
        "transport_support": main["transport_support"],
        "follow_up": main["follow_up"],
        "chat": main["chat"],
    }


def write_dataset(role: str, rows: list[dict], stamp: str) -> Path:
    directory = RESULTS_DIR / stamp
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{role}.jsonl"
    path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
    return path


def run(max_estimated_tokens: int, poll_seconds: int) -> dict:
    from openai.types.eval_create_params import DataSourceConfigCustom

    settings = validated_settings()
    agents = load_agents()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    plans = []
    for role, agent in agents.items():
        rows = rows_for(role)
        criteria = criteria_for(role, settings["AZURE_AI_MODEL_DEPLOYMENT_NAME"])
        plans.append({"role": role, "agent": agent, "rows": rows, "criteria": criteria})

    total_rows = sum(len(plan["rows"]) for plan in plans)
    total_estimate = sum(estimated_tokens(len(plan["rows"]), len(plan["criteria"])) for plan in plans)
    if total_estimate > max_estimated_tokens:
        raise ValueError(f"Estimated {total_estimate} tokens exceeds cap {max_estimated_tokens}.")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_only": True,
        "optimizer_used": False,
        "total_rows": total_rows,
        "estimated_token_ceiling": total_estimate,
        "configured_cap": max_estimated_tokens,
        "evaluations": [],
    }

    with project_client(settings) as project:
        with project.get_openai_client() as client:
            active = []
            for plan in plans:
                role = plan["role"]
                dataset_path = write_dataset(role, plan["rows"], stamp)
                dataset = project.datasets.upload_file(
                    name=f"mamalink-{role.replace('_', '-')}-evaluation",
                    version=stamp,
                    file_path=str(dataset_path),
                )
                properties = {"query": {"type": "string"}}
                required = ["query"]
                if role in CASES:
                    properties["tool_definitions"] = {"type": "array", "items": {"type": "object"}}
                    required.append("tool_definitions")
                evaluation = client.evals.create(
                    name=f"MAMA-Link {role.replace('_', ' ').title()} Hackathon Baseline",
                    data_source_config=DataSourceConfigCustom(
                        type="custom",
                        item_schema={"type": "object", "properties": properties, "required": required},
                        include_sample_schema=True,
                    ),
                    testing_criteria=plan["criteria"],
                    metadata={"project": "MAMA-Link", "role": role, "dataset": "synthetic"},
                )
                evaluation_run = client.evals.runs.create(
                    eval_id=evaluation.id,
                    name=f"{role.replace('_', ' ').title()} v{plan['agent']['version']} baseline {stamp}",
                    data_source={
                        "type": "azure_ai_target_completions",
                        "source": {"type": "file_id", "id": dataset.id},
                        "input_messages": {
                            "type": "template",
                            "template": [{
                                "type": "message",
                                "role": "user",
                                "content": {"type": "input_text", "text": "{{item.query}}"},
                            }],
                        },
                        "target": {
                            "type": "azure_ai_agent",
                            "name": plan["agent"]["name"],
                            "version": plan["agent"]["version"],
                        },
                    },
                    metadata={"project": "MAMA-Link", "role": role, "synthetic": "true"},
                )
                entry = {
                    "role": role,
                    "agent": plan["agent"],
                    "dataset": {"name": dataset.name, "version": dataset.version, "id": dataset.id},
                    "row_count": len(plan["rows"]),
                    "evaluators": [criterion["name"] for criterion in plan["criteria"]],
                    "evaluation_id": evaluation.id,
                    "run_id": evaluation_run.id,
                    "status": evaluation_run.status,
                }
                report["evaluations"].append(entry)
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
                REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
                MANIFEST_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                if active:
                    print(f"WAITING {len(active)} evaluation runs", flush=True)
                    time.sleep(poll_seconds)

    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded MAMA-Link Foundry evaluations.")
    parser.add_argument("--max-estimated-tokens", type=int, default=500_000)
    parser.add_argument("--poll-seconds", type=int, default=15)
    args = parser.parse_args()
    report = run(args.max_estimated_tokens, args.poll_seconds)
    failed = [entry for entry in report["evaluations"] if entry["status"] != "completed"]
    print(json.dumps({
        "total_rows": report["total_rows"],
        "estimated_token_ceiling": report["estimated_token_ceiling"],
        "completed": len(report["evaluations"]) - len(failed),
        "failed": len(failed),
        "report": str(REPORT_PATH),
    }, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
