# MAMA-Link hackathon build path

**Current status:** The local web app, FastAPI, session history, seven Foundry agents, Application Insights connection and cloud evaluation baselines are implemented. This file preserves the staged build history; use [the project assessment](project-assessment.md), [Foundry setup](foundry-setup.md) and [Foundry evaluation evidence](foundry-evaluation-latest.json) for current status.

Source of product requirements: `MAMA-Link.md`. Learning structure: https://github.com/shashacode/FrontierWeekHack.

## Challenge 0 — Setup

Completed locally: Python package, runtime-safe data access, command-line demo and unit tests.

Completed: the existing Azure subscription, `mama-link` Foundry project and `gpt-4.1-mini` deployment are configured. Idempotent infrastructure scripts validate resources and preserve local secrets outside version control. Provisioning and model calls may incur Azure charges.

## Challenge 1 — Build agents

Completed locally: deterministic screening, capability filtering, support matching and referral preparation.

Completed: six workflow roles are connected through the orchestrator—intake, triage, knowledge, referral, transport support and follow-up—plus the separate Ask Mama Link chat agent. Five workflow agents use restricted read-only tools with exact authoritative-output validation; knowledge requires File Search. The model cannot override deterministic escalation, invent facility capabilities, diagnose, prescribe or infer consent.

The prototype executes the supplied seven rules plus two documented [simulation extensions](screening-rules.md). Review uncovered symptoms, missing values, postpartum handling, compound symptoms and unknown inputs with a qualified clinical reviewer before real use. Do not tune clinical logic simply to memorize the synthetic labels.

Implemented for demonstration: a provenance-labelled WHO/UNFPA corpus is indexed in Foundry File Search. It remains pending qualified clinical review and must not be presented as an approved clinical protocol.

## Challenge 2 — Monitor

Completed: Application Insights is connected to the Foundry project as `mamalink-appinsights`. Aggregate operation metrics and metadata-only spans identify each agent role and version. Events, traces, dependencies and metrics were observed for all seven agents. Automatic HTTP, FastAPI and Azure SDK content capture remains disabled; prompts, outputs, symptoms, notes, case IDs and tool payloads are excluded.

Remaining production work: an Azure administrator must grant the project managed identity Log Analytics Reader on Application Insights and its workspace for trace-filtered service-side evaluations. This does not block the current monitoring dashboards.

## Challenge 3 — Evaluate

Completed locally: offline rule-baseline report over separate ground truth; tests for emergency precedence, capability filtering, consent and answer isolation.

Initial verified baseline (2026-09-18): 8 unit tests pass; 12/24 fixture labels match; 5/7 expected critical cases are classified critical. MAT-009 is classified warning by the supplied fever rule, and MAT-018 is unassessed because the supplied rules omit its symptoms. Five expected-normal fixtures are deliberately unassessed rather than assumed safe. These results expose incomplete rule coverage; they are not a clinical validation score.

Verified after the `0.2-hackathon` extensions: 12 tests pass; 14/24 labels match; 7/7 expected critical cases are classified critical. MAT-009 and MAT-018 now complete capability-aware, consent-gated simulated referral. The other 22 classifications are unchanged. Ten fixtures remain unassessed: five expected warning and five expected normal. Tests also cover missing cluster components, the temperature boundary and severe breathlessness without chest pain.

Current verified baseline (2026-09-25): 45 automated tests pass; the local deterministic evaluation matches 19/24 labels, detects 7/7 expected emergencies and matches referral capabilities for 19/19 expected nonroutine cases. Separately, final selected Foundry evaluation runs passed 24/24 synthetic agent interactions across all seven agents. The modeled evaluation ceiling was 329,280 tokens, below the 500,000-token cap, and no optimiser was run.

Next: add an independently authored held-out set plus grounding, unsafe-advice, adversarial and prompt-injection evaluation approved by qualified reviewers. Existing baselines measure regression behaviour, not clinical performance.

## Challenge 4 — Workflow and demo

Completed locally: MAT-005 screening → capability matching → support matching → consent-gated simulated referral.

Completed for the hackathon: FastAPI endpoints, accessible web intake, explicit consent UI, synthetic symptom history, the six-role Foundry workflow and the separate chat agent. Agent diagnostics remain outside the patient-facing interface.

Next: authenticated hosting, approved knowledge content, verified operational partners and human-confirmed availability before any real referral or dispatch integration.

## Current demonstration sequence

1. Open the local web app and demonstrate a fictional symptom check.
2. Show the six workflow agents and separate Ask Mama Link agent in Foundry.
3. Explain the orchestrator, restricted tools, File Search and exact-output validation.
4. Show Foundry Monitor with privacy-minimised telemetry and named agent runs.
5. Show the completed evaluation runs and the 24/24 selected synthetic baseline.
6. Explain that local rule coverage remains 19/24 and that the prototype is not clinically validated.

This completes the synthetic hackathon milestone, not the clinical or production acceptance criteria.
