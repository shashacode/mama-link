# MAMA-Link Evaluation Methodology

## Purpose

This document keeps three different claims separate:

1. **Local rule benchmark:** deterministic runtime classification against 24 labelled synthetic fixtures.
2. **Foundry selected-run completion:** selected agent interactions reached a stored response and passed the application's bounded contract checks.
3. **Foundry evaluator pass:** a configured Foundry evaluator directly executed and passed a row.

None of these is clinical validation, generalisation, or production reliability evidence.

## Dataset and selection

- The local benchmark contains 24 synthetic cases: 5 expected normal, 12 warning and 7 critical.
- The first 24 runtime fixtures retain the original benchmark labels and are used for regression only.
- Foundry samples cover intake (3), triage (4), knowledge (3), referral (4), transport support (3), follow-up (3) and chat (4).
- The sample is intentionally bounded and scenario-driven. It is not random, held out, population representative or clinically approved.
- Client-local Python tools cannot be executed by the Foundry evaluator. Their rows are therefore stored and checked by the application, while the portal evaluator records them as skipped.

## Local benchmark result

| Expected \\ Actual | Normal | Warning | Critical | Unassessed | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Normal | 0 | 0 | 0 | 5 | 5 |
| Warning | 0 | 12 | 0 | 0 | 12 |
| Critical | 0 | 0 | 7 | 0 | 7 |
| **Total** | **0** | **12** | **7** | **5** | **24** |

Exact match is 19/24 (79.2%). Emergency recall is 7/7 on this synthetic regression set. The five abstentions are MAT-001, MAT-006, MAT-016, MAT-020 and MAT-021. They are expected normal but remain unassessed because no clinically approved low-risk exclusion protocol exists.

## Failure examples

The normal-case abstentions are the current failure examples. They show a coverage gap rather than an emergency false negative: the runtime refuses to declare low risk when the approved exclusion process is missing. The corrective action is clinical review of minimum data, exclusions and messaging, followed by a new regression version. The system must not be changed merely to force 24/24.

## Operational reliability plan

The next evaluation version must report the following per release and per agent role:

- end-to-end latency p50, p95 and p99;
- model/evaluator token usage and realised cost per validated case;
- agent failure rate, including timeout, exception, invalid output and contract rejection;
- tool failure rate, including timeout, invalid result and unavailable dependency;
- recovery rate after retry, fallback or safe abstention;
- completion, safe-abstention and recovery rates under delayed or unavailable network connectivity.

Application Insights already receives privacy-minimised operation counts and duration histograms. Role-level failure and recovery counters, token/cost attribution and controlled network fault injection remain implementation work. Until those measurements exist, the project should be described as a synthetic functional demonstration with an operational measurement plan, not a reliable clinical service.

## Release interpretation

The phrase “24 of 24 passed” must always be qualified as “24 of 24 selected synthetic interactions completed the application's contract checks.” It must not be presented as 24/24 classification accuracy, 24/24 direct Foundry evaluator passes, or clinical validation.