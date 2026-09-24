# MAMA-Link hackathon build path

**Current status:** The local web app, FastAPI, session history and optional Foundry CLI have now been added. This file records the staged build history; use [the project assessment](project-assessment.md) and [Foundry setup](foundry-setup.md) for the current completion status and next actions.

Source of product requirements: `MAMA-Link.md`. Learning structure: https://github.com/shashacode/FrontierWeekHack.

## Challenge 0 — Setup

Completed locally: Python package, runtime-safe data access, command-line demo and unit tests.

Next: select an existing Azure subscription and Foundry project, deploy a suitable model, configure local Azure authentication and populate the endpoint/deployment settings in `.env.example`. Verify the SDK version and current Foundry examples before adding SDK dependencies. Provisioning and model calls may incur Azure charges.

## Challenge 1 — Build agents

Completed locally: deterministic screening, capability filtering, support matching and referral preparation.

Next: connect an intake/triage agent and a referral/resource agent to these tools. Start with these two roles, then separate the PRD's six specialist roles as the workflow grows. The model must not override a deterministic escalation, invent facility capabilities, diagnose, prescribe or infer consent. Free-text extraction must retain uncertainty and be confirmed before consequential actions.

The prototype executes the supplied seven rules plus two documented [simulation extensions](screening-rules.md). Review uncovered symptoms, missing values, postpartum handling, compound symptoms and unknown inputs with a qualified clinical reviewer before real use. Do not tune clinical logic simply to memorize the synthetic labels.

Create an approved-document corpus with provenance and review status for the knowledge agent. Until retrieval returns an approved source, show that clinical grounding is unavailable rather than generating unsupported clinical advice.

## Challenge 2 — Monitor

Completed locally: per-step timing and status in demo output.

Next: OpenTelemetry/Application Insights integration following the selected Foundry SDK. Track tool failures, latency, escalation and consent outcomes. Do not enable patient-message or tool-payload capture by default. Show a real Foundry trace only once integration has been exercised.

## Challenge 3 — Evaluate

Completed locally: offline rule-baseline report over separate ground truth; tests for emergency precedence, capability filtering, consent and answer isolation.

Initial verified baseline (2026-09-18): 8 unit tests pass; 12/24 fixture labels match; 5/7 expected critical cases are classified critical. MAT-009 is classified warning by the supplied fever rule, and MAT-018 is unassessed because the supplied rules omit its symptoms. Five expected-normal fixtures are deliberately unassessed rather than assumed safe. These results expose incomplete rule coverage; they are not a clinical validation score.

Verified after the `0.2-hackathon` extensions: 12 tests pass; 14/24 labels match; 7/7 expected critical cases are classified critical. MAT-009 and MAT-018 now complete capability-aware, consent-gated simulated referral. The other 22 classifications are unchanged. Ten fixtures remain unassessed: five expected warning and five expected normal. Tests also cover missing cluster components, the temperature boundary and severe breathlessness without chest pain.

Next: model evaluation using the supplied portal JSONL, plus referral capability correctness, grounding, prescription/diagnosis refusal, unknown-input behavior and privacy tests. Maintain a separate held-out set. Baseline misses are visible and are not evidence of clinical performance.

## Challenge 4 — Workflow and demo

Completed locally: MAT-005 screening → capability matching → support matching → consent-gated simulated referral.

Next: FastAPI endpoints, accessible web intake, approved knowledge retrieval, explicit consent UI, synthetic symptom history and authenticated deployment. Follow with Foundry orchestration and hosted tools. Confirm resource availability with humans before any real dispatch integration.

## First demo script

1. Run `py -m mama_link demo --case MAT-005`.
2. Show the matched rule and required emergency/surgical/blood capabilities.
3. Explain why the basic PHC cannot appear among the matches.
4. Show support matches and the `awaiting_consent` referral.
5. Run again with `--consent`; show `simulated` and `sent: false`.
6. Run evaluation and discuss uncovered scenarios transparently.

This completes the first local build milestone, not the full PRD acceptance criteria.
