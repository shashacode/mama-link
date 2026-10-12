# MAMA-Link

**Detect danger. Find care. Mobilize help.**

MAMA-Link is a maternal-health support prototype for Nigeria. It combines deterministic symptom screening, care and support discovery, longitudinal history, low-data education, and a bounded multi-agent Microsoft Foundry workflow.

## 🏆 Microsoft Global Agent-a-thon winner

MAMA-Link, created by Flora Oladipupo, was selected as **one of 18 global winners** of the **September 2026 Microsoft Global Agent-a-thon**. It won in the **Architect** category for solutions built with Microsoft Foundry. The winners announcement highlights MAMA-Link's six-agent approach to helping pregnant women in underserved communities recognise emergencies, locate appropriate care, and navigate toward support.

[View the 2026 Microsoft Global Agent-a-thon winners announcement on LinkedIn](https://www.linkedin.com/feed/update/urn:li:ugcPost:7513858645458284544/)

## Live demo and solution walkthrough

- **Try the live application:** [Open Ask Mama Link](https://mama-link.onrender.com/#chat)
- **Watch the solution walkthrough:** [`mamaLinkVid.mp4`](https://github.com/shashacode/mama-link/blob/main/mamaLinkVid.mp4) is included in this repository and demonstrates how the solution works.

> **Safety notice:** This repository is a synthetic hackathon demonstration, not a clinically validated triage service. Use fictional information only. It does not contact a facility, dispatch emergency services, or replace a qualified healthcare professional.

## Project status — 12 October 2026

The project is ready for a synthetic hackathon demonstration. The current implementation includes:

- Sign-up/sign-in, personal pregnancy profiles, private account history, and an admin-only demo library.
- Structured symptom intake, browser-supported voice transcription for user review, longitudinal change detection, and consent-gated simulated referrals.
- Nationwide state/LGA selection, official Phase 1 Nigeria Healthcare Facility Registry lookup, a 100-case synthetic hotspot map, and verified Nigerian `112` emergency information.
- Low-data learning content, a downloadable offline guide, and navigation in English, Pidgin, Yoruba, Igbo, and Hausa.
- Optional reviewed JSON health-data imports. Native Apple Health and Android Health Connect connections remain future work.
- Six bounded Foundry workflow roles plus the Ask Mama Link education agent, using `gpt-4.1-mini` and explicit consent before sharing profile context.
- Privacy-minimised Application Insights telemetry and stored synthetic cloud-evaluation evidence.
- A Render Blueprint in [`render.yaml`](render.yaml) for deployment from this repository.

The prototype account system has not been independently security-audited. The default Render configuration also uses temporary SQLite storage at `/tmp/mama-link.sqlite3`, so accounts and history can be lost when the service restarts. Persistent storage, production identity controls, clinical review, partner verification, held-out/red-team evaluation, and operational testing are required before any real-world use.

See the [project assessment](docs/project-assessment.md), [personal experience and data flow](docs/personal-experience.md), and [Foundry setup](docs/foundry-setup.md) for detailed evidence and limitations.

## Run the web app

Open **http://127.0.0.1:8000** while the local server is running.

From the project folder:

```powershell
.\scripts\setup.ps1
.\scripts\start.ps1
```

If PowerShell blocks scripts, use these commands without changing execution policy:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn mama_link.api:app --host 127.0.0.1 --port 8000
```

The app includes nationwide state/place selection, text and browser-supported voice intake, longitudinal change detection, a 100-case synthetic hotspot map, official national facility-registry access, verified 112 emergency information, multilingual navigation, private account history, consent-gated simulated referrals, and an evaluation dashboard. Free-text and voice transcripts are accepted for human review, not interpreted or persisted. See the [nationwide expansion notes](docs/national-expansion.md).

The Phase 1 Nigeria Healthcare Facility Registry workbook is imported with `py scripts/import_facility_registry.py` into a compressed, read-only directory artifact. Find Care queries the real registry by state and LGA, showing registry status and coordinates; clinical capabilities, live availability, and contact validity are never inferred from the workbook.

## Deploy with Render

The repository includes a Render Blueprint that installs the runtime requirements, starts the FastAPI application, and checks `/api/health`.

1. In Render, create a new Blueprint and connect this GitHub repository.
2. Review the service settings in [`render.yaml`](render.yaml).
3. Add the optional Azure/Foundry settings from [`.env.example`](.env.example) if the hosted demo should use Ask Mama Link.
4. Replace the temporary SQLite path with persistent storage before relying on saved accounts or history.

The Blueprint enables secure cookies and permits `*.onrender.com` hosts. A repository configuration file alone does not prove that a live service is healthy; verify the deployed `/api/health` endpoint after each release.

## Run the command-line simulation

From this folder, with Python 3.10 or later:

```powershell
py -m mama_link cases
py -m mama_link demo --case MAT-005
py -m mama_link demo --case MAT-005 --consent
py -m mama_link evaluate
py -m unittest discover -s tests -v
```

On systems where Python is named `python`, substitute that for `py`. No third-party packages or Azure account are needed for the deterministic simulation.

`MAT-005` demonstrates the PRD's prolonged-labour scenario. The tools execute the supplied screening rules, filter fictional facilities by capability, match fictional support by service and coverage, and prepare a simulated referral. Consent changes only the simulated status. Nothing is sent.

## Current scope

- Runtime consumes only the existing runtime-safe dataset under `mama_link_dataset/maternal`.
- Fifteen synthetic rules execute with critical-over-warning precedence; see the [simulation rules and capability crosswalk](docs/screening-rules.md).
- Facility results require every requested capability and simulated available status.
- No patient coordinates exist: ranking uses LGA, not distance. No claim of nearest care is made.
- Local traces contain step names, timing, and status—not patient descriptions.
- Offline evaluation compares predictions with separate ground-truth labels and reports misses.

Verified with rules version `0.3-hackathon`: **45 tests pass**, **7/7 expected emergency cases detected**, **19/24 classifications match**, and **19/19 expected nonroutine cases have matching referral capabilities**. Five expected-normal cases remain unassessed; the absence of a matched rule does not establish medical safety. These are known synthetic fixture results, not clinical validation. See the [project assessment](docs/project-assessment.md) and [evaluation report](docs/evaluation-latest.json).

Run the full suite and refresh the report with:

```powershell
.\.venv\Scripts\python.exe scripts/verify.py
```

`requirements-lock.txt` records the exact verified environment, including the optional Azure packages. Use `pip install -r requirements-lock.txt` to reproduce it.

Try the newly covered cases with `py -m mama_link demo --case MAT-009` and `py -m mama_link demo --case MAT-018`.

This is a **synthetic software simulation**, not a clinical triage system. The rules do not cover all 24 scenarios. An unmatched case is `unassessed`, never a declaration of safety. The dataset's three labels also differ from the PRD's planned four-level risk scheme; that mapping needs an explicit design decision before implementation.

## Foundry agents, grounding, and monitoring

FastAPI and the local frontend are implemented. The Foundry pipeline orchestrates intake, triage, knowledge, referral, transport-support, and follow-up roles through the separate CLI; agent diagnostics are intentionally not exposed in the patient-facing interface. Five tool-backed agents must call their case-specific read-only tool and match an exact deterministic output; the knowledge agent must use File Search. The six-role workflow and Ask Mama Link chat agent were verified live against the `mama-link` project and `gpt-4.1-mini` on 24 September 2026 using fictional data.

An idempotent provisioning script is available at [`infra/provision-foundry.ps1`](infra/provision-foundry.ps1). It targets the existing Sweden Central hackathon resource group and validates the requested model before deploying it.

A review-pending WHO/UNFPA public-source corpus is indexed in Foundry File Search, and the `mama-link-knowledge` agent was verified against it. It is a retrieval prototype, not an approved clinical corpus. Application Insights is connected to the Foundry project with automatic HTTP/Azure SDK instrumentation disabled; the app emits aggregate metrics and metadata-only agent spans.

On 25 September 2026, the final selected Foundry evaluation runs completed all 24 synthetic interactions across the seven agents. Direct portal evaluators passed the knowledge and chat samples; client-local tool roles were verified using completed stored responses because Foundry cannot execute those Python tools directly. See the [cloud evaluation evidence](docs/foundry-evaluation-latest.json) for the exact denominators and results.

The original PRD and case/evaluation datasets are preserved; the screening rules are versioned separately within the dataset pack. No source code from the reference repository was copied.
