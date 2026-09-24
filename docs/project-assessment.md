# Project assessment — 2026-09-18

## Outcome

The project now has a working local web/API prototype and optional cloud-agent integration code. It is ready for a synthetic local hackathon demonstration, not for clinical use or a complete Foundry submission.

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
| Foundry agent/tool use | Expanded implementation; cloud rerun pending | Six roles are orchestrated locally. Five tool agents use restricted case-specific tools and exact authoritative-output checks; knowledge requires File Search. Earlier triage/referral and knowledge paths were live-verified, while the current six-role contract still needs intentional bootstrap and a live smoke test. |
| Evaluation | Local implementation | 24 cases, classification and referral metrics; 25 regression tests. Cloud judge evaluations and held-out cases pending. |
| Safety | Partial | Unknown inputs stay unassessed; no dispatch tool exposed to models; no generated clinical advice in local app. Clinical validation and live model red-teaming pending. |
| Tracing / monitoring | Cloud prototype connected | Application Insights and a 30-day Log Analytics workspace are provisioned. Only aggregate operation count/status/duration are emitted; automatic request and Azure SDK instrumentation is disabled. |
| Deployment | Local only | Loopback web server. Authenticated public hosting not configured. |
| Geographic exploration | Expanded prototype | Interactive Nigeria schematic aggregates 100 synthetic cases and drills into places. The northern skew is a test fixture, not prevalence evidence. |
| Language access | Partial | Navigation/headline translations for English, Pidgin, Yoruba, Igbo and Hausa; full professional translation and clinical review pending. |
| Follow-up | Partial | Longitudinal change flags and support matching exist. Scheduling, acknowledgement and clinical follow-up workflows remain future work. |

## Evaluation interpretation

19/24 labels match, 7/7 expected critical cases detected, and 19/19 expected warning/critical cases have appropriate simulated referral capabilities. Five expected-normal cases intentionally remain unassessed. Those five lack a complete, clinically approved exclusion process; assigning low risk solely to reach 24/24 would misrepresent coverage.

Rules were developed with these known scenarios, so these are regression scores, not generalization or clinical performance measures. The new high/medium urgency mapping is a prototype addition, not a claim of agreement with the original dataset's urgency labels. Only classification and referral capabilities are scored by the local evaluator.

## Verified locally

- 43 automated tests cover rule precedence, missing values, numeric validation, warning pathways, referral matching, consent, repeated consent, cross-session access, cross-origin writes, prompt-like notes, every tool-agent contract, required knowledge File Search and six-role orchestration.
- Browser verification covers homepage layout, fixture and custom intake, care options, explicit simulated consent, saved history and the 24-row evaluation dashboard.
- Azure AI Projects 2.6.1 definitions were checked locally. A live Foundry smoke test passed on 2026-09-18: triage returned `critical`, and referral returned `FAC-009`, `FAC-002`, and `FAC-004` after tool use. No external referral was sent.
- Foundry File Search ingestion and a live grounded retrieval passed on 2026-09-18. The knowledge agent identified the UNFPA association with prolonged obstructed labour and returned the indexed source URL while retaining the pending-review label.
- The API health check reported `telemetry_enabled: true` after Application Insights provisioning. Raw request content, routes, identifiers, prompts, notes and tool payloads are outside the telemetry allow-list.

## External inputs needed

1. Clinically reviewed rules, low-risk completion requirements and approved source documents.
2. A chosen authenticated hosting destination and verified service partners for any real referral integration.

The Foundry resource, project, deployment, three agent roles, review-pending File Search corpus, and privacy-safe monitoring prototype are configured. The next cloud milestone is held-out cloud evaluation, followed by authenticated deployment.
