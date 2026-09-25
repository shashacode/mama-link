# Project assessment — 2026-09-25

## Outcome

The project has a working local web/API prototype, a verified seven-agent Foundry solution, connected privacy-minimized monitoring and completed cloud evaluation baselines. It is ready for a synthetic hackathon demonstration, not for clinical use.

## PRD acceptance review

| Requirement | Status | Evidence / remaining work |
| --- | --- | --- |
| Symptom intake | Expanded prototype | 100 synthetic fixtures, nationwide state/place selection, validated structured intake and browser voice transcription with mandatory review. Notes are not interpreted or persisted. |
| Risk assessment | Partial | 15 rules; emergency, high and medium outputs plus unassessed. A clinically reviewed low-risk completion protocol is needed. |
| Approved clinical grounding | Prototype connected | WHO/UNFPA public-source summary indexed in Foundry File Search and retrieval verified; qualified clinical approval remains pending. |
| Emergency routing | Local implementation | All seven expected emergency fixtures enter referral preparation. |
| Facility matching | Local implementation | All 19 expected nonroutine cases have matching capabilities through the documented crosswalk. No patient coordinates or live capacity. |
| Support matching | Local implementation | Service/coverage/availability filtering and adolescent support; fictional registries. |
| Alerts | Simulation implemented | Selected-facility consent, session isolation, idempotence, and `sent: false`. |
| Symptom history | Local implementation | SQLite records per browser session, no raw notes, clear-history action. Production identity/RBAC absent. |
| Foundry agent/tool use | Verified cloud implementation | The orchestrator runs six workflow roles; Ask Mama Link is the seventh agent. Five tool agents use restricted case-specific tools and exact authoritative-output checks, knowledge requires File Search, and chat uses its saved Foundry version. |
| Evaluation | Baseline evidence, not validation | The local 24-case rule benchmark has 19 exact matches and 5 expected-normal cases returned as unassessed. Foundry selected runs contain 24 completed agent interactions, but only the 3 knowledge and 4 chat rows received direct evaluator passes; the five client-tool roles are recorded as skipped because Foundry cannot execute their local Python tools. Held-out, operational and clinical validation remain pending. |
| Safety | Partial | Unknown inputs stay unassessed; no dispatch tool exposed to models; no generated clinical advice in local app. Clinical validation and live model red-teaming pending. |
| Tracing / monitoring | Connected and verified | The Foundry project is connected to Application Insights. Metadata-only spans and aggregate metrics were observed for all seven agents; automatic request and Azure SDK instrumentation is disabled. |
| Deployment | Local only | Loopback web server. Authenticated public hosting not configured. |
| Geographic exploration | Expanded prototype | Interactive Nigeria schematic aggregates 100 synthetic cases and drills into places. The northern skew is a test fixture, not prevalence evidence. |
| Language access | Partial | Navigation/headline translations for English, Pidgin, Yoruba, Igbo and Hausa; full professional translation and clinical review pending. |
| Follow-up | Partial | Longitudinal change flags and support matching exist. Scheduling, acknowledgement and clinical follow-up workflows remain future work. |

## Evaluation definitions and selection

The submission uses three separate denominators. **Rule benchmark accuracy** is exact agreement between the deterministic runtime classification and the fixture label across all 24 labelled cases. **Foundry selected-run completion** means that the chosen synthetic interaction reached a stored response and passed the local contract checks; it is not the same as a Foundry evaluator pass. **Foundry evaluator pass** means a configured portal evaluator returned a pass for a row it could execute. Client-local tool roles are not directly executable by the Foundry evaluator and therefore must not be counted as evaluator passes.

The 24 local benchmark rows were selected from the first 24 synthetic fixtures because they retain the original labels and cover normal, warning and critical scenarios. The Foundry role samples were selected to exercise each of the seven agent contracts: intake 3, triage 4, knowledge 3, referral 4, transport support 3, follow-up 3 and chat 4. This is a bounded regression sample, not a random or held-out clinical sample.

## Evaluation interpretation

19/24 labels match, 7/7 expected critical cases detected, and 19/19 expected warning/critical cases have appropriate simulated referral capabilities. Five expected-normal cases intentionally remain unassessed. Those five lack a complete, clinically approved exclusion process; assigning low risk solely to reach 24/24 would misrepresent coverage.

### Local classification confusion matrix

Rows are expected labels and columns are runtime classifications. `Unassessed` is a safety-preserving abstention, not a correct normal result.

| Expected \\ Actual | Normal | Warning | Critical | Unassessed | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Normal | 0 | 0 | 0 | 5 | 5 |
| Warning | 0 | 12 | 0 | 0 | 12 |
| Critical | 0 | 0 | 7 | 0 | 7 |
| **Total** | **0** | **12** | **7** | **5** | **24** |

The five failure/abstention examples are MAT-001, MAT-006, MAT-016, MAT-020 and MAT-021. Each expected `normal` case returned `unassessed` because the prototype has no clinically approved minimum-data and exclusion protocol for a low-risk completion. This is preferable to false reassurance, but it means normal-case coverage is zero and overall exact-match rate is 19/24 (79.2%). Emergency recall is 7/7 (100%) on this known synthetic regression set; it is not a clinical sensitivity estimate.

### Operational reliability measures

The prototype currently records privacy-minimised operation counts and duration histograms in Application Insights. The following release metrics are defined but not yet reported from a representative load or low-connectivity test:

| Measure | Definition | Current status / release gate |
| --- | --- | --- |
| End-to-end latency | Time from API request acceptance to final validated response, reported as p50/p95/p99 | Instrumentation exists for operation duration; representative baseline pending |
| Cost per completed case | Azure model and evaluator token cost divided by cases that return a validated final result | Token ceiling is modelled, but realised billing cost is not yet measured |
| Agent failure rate | Agent invocations ending in timeout, exception, invalid output or contract rejection divided by invocations | Not yet reported by role; add role-level counters and failure reasons |
| Tool failure rate | Tool calls that error, time out or return invalid data divided by tool calls | Not yet reported; client-local tools need explicit counters |
| Recovery rate | Failed first attempt that reaches a valid result after retry, fallback or abstention divided by failed first attempts | Not yet exercised under a defined fault-injection plan |
| Low-connectivity reliability | Completion, safe-abstention and recovery rates under delayed or unavailable cloud calls | Pending offline/network fault-injection test |

These operational measures are required alongside model and rule scores before any claim of service readiness. A future evaluation report should publish the values by agent role, tool, network condition and release version.

Rules were developed with these known scenarios, so these are regression scores, not generalization or clinical performance measures. The new high/medium urgency mapping is a prototype addition, not a claim of agreement with the original dataset's urgency labels. Only classification and referral capabilities are scored by the local evaluator.

## Verified locally

- 45 automated tests cover rule precedence, missing values, numeric validation, warning pathways, referral matching, consent, repeated consent, cross-session access, cross-origin writes, prompt-like notes, every tool-agent contract, required knowledge File Search and six-role orchestration.
- Browser verification covers homepage layout, fixture and custom intake, care options, explicit simulated consent, saved history and the 24-row evaluation dashboard.
- Azure AI Projects 2.6.1 definitions were checked locally. The current six-role workflow and chat agent passed live smoke tests on 2026-09-24. No external referral was sent.
- Foundry File Search ingestion and grounded retrieval are live. The knowledge agent uses the indexed, review-pending WHO/UNFPA corpus.
- On 2026-09-25, final selected Foundry runs passed intake 3/3, triage 4/4, knowledge 3/3, referral 4/4, transport support 3/3, follow-up 3/3 and chat 4/4. Tool-agent scoring uses completed stored responses because Foundry cannot execute client-local Python functions.
- Application Insights showed events, traces, dependencies and metrics, with named metadata for all seven agents. Raw request content, routes, identifiers, prompts, notes and tool payloads remain outside the app's telemetry allow-list.

## External inputs needed

1. Clinically reviewed rules, low-risk completion requirements and approved source documents.
2. A chosen authenticated hosting destination and verified service partners for any real referral integration.

The Foundry resource, project, deployment, seven agent roles, review-pending File Search corpus, privacy-safe monitoring and synthetic cloud evaluations are configured. Remaining work is clinical review, held-out/red-team evaluation, an administrator-granted Log Analytics Reader role for trace-filtered service-side evaluation, and authenticated deployment.
