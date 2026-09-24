# MAMA-Link

## Personal preview update — 21 September 2026

The local app now has sign-up/sign-in, personal pregnancy profiles, private account
history, an admin-only demo library, optional reviewed health-app imports, a
low-data learning area with a downloadable offline guide, and Foundry chat with
explicit context-sharing consent. See [the current implementation and data flow](docs/personal-experience.md).

Apple Health and Android Health Connect are the default provider choices. Their
native live connections remain pending; sample and supported JSON imports work.
The project currently exposes a `gpt-4.1-mini` deployment. Ask Mama Link is clearly
labelled as an education assistant and now refuses to present a local fallback as
an agent answer when its saved agent version is unavailable or stale. A medically
trained specialist deployment is not yet configured. Keep this preview on localhost
and use fictional details.

The older milestone notes below describe the pre-personalisation baseline.

Detect danger. Find care. Mobilize help.

Python starter for the maternal-health hackathon project described in [MAMA-Link.md](MAMA-Link.md). Follows the **setup → build → monitor → evaluate → workflow** learning sequence of [FrontierWeekHack](https://github.com/shashacode/FrontierWeekHack).

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

The app includes nationwide state/place selection, text and browser-supported voice intake, longitudinal change detection, a 100-case synthetic hotspot map, official national facility-registry access, verified 112 emergency information, multilingual navigation, browser-session history, consent-gated simulated referrals and an evaluation dashboard. Keep it on localhost: production authentication is not implemented. Use fictional information only. Free-text and voice transcripts are accepted for human review, not interpreted or persisted. See [the nationwide expansion notes](docs/national-expansion.md).

The Phase 1 Nigeria Healthcare Facility Registry workbook is imported with `py scripts/import_facility_registry.py` into a compressed, read-only directory artifact. Find Care queries the real registry by state and LGA, showing registry status and coordinates; clinical capabilities, live availability, and contact validity are never inferred from the workbook.

## Run the command-line simulation

From this folder, with Python 3.10 or later:

```powershell
py -m mama_link cases
py -m mama_link demo --case MAT-005
py -m mama_link demo --case MAT-005 --consent
py -m mama_link evaluate
py -m unittest discover -s tests -v
```

On systems where Python is named `python`, substitute that for `py`. No third-party packages or Azure account are needed for this first milestone.

`MAT-005` demonstrates the PRD's prolonged-labour scenario. The tools execute the supplied screening rules, filter fictional facilities by capability, match fictional support by service and coverage, and prepare a simulated referral. Consent changes only the simulated status. Nothing is sent.

## Current scope

- Runtime consumes only the existing runtime-safe dataset under `mama_link_dataset/maternal`.
- Fifteen synthetic rules execute with critical-over-warning precedence; see the [simulation rules and capability crosswalk](docs/screening-rules.md).
- Facility results require every requested capability and simulated available status.
- No patient coordinates exist: ranking uses LGA, not distance. No claim of nearest care is made.
- Local trace contains step names, timing and status, not patient descriptions.
- Offline evaluation compares predictions with separate ground-truth labels and reports misses.

Verified with rules version `0.3-hackathon`: **45 tests pass**, **7/7 expected emergency cases detected**, **19/24 classifications match**, and **19/19 expected nonroutine cases have matching referral capabilities**. Five expected-normal cases remain unassessed; no matched rule does not establish medical safety. These are known synthetic fixture results, not clinical validation. See [the project assessment](docs/project-assessment.md) and [evaluation report](docs/evaluation-latest.json).

Run the full suite and refresh the report with:

```powershell
.\.venv\Scripts\python.exe scripts/verify.py
```

`requirements-lock.txt` records the exact verified environment, including the optional Azure packages. Use `pip install -r requirements-lock.txt` to reproduce it.

Try the newly covered cases with `py -m mama_link demo --case MAT-009` and `py -m mama_link demo --case MAT-018`.

This is a **synthetic software simulation**, not a clinical triage system. The rules do not cover all 24 scenarios. An unmatched case is `unassessed`, never a declaration of safety. The dataset's three labels also differ from the PRD's planned four-level risk scheme; that mapping needs an explicit design decision before implementation.

FastAPI and the local frontend are implemented. The Foundry pipeline orchestrates intake, triage, knowledge, referral, transport-support and follow-up roles through the separate CLI; agent diagnostics are intentionally not exposed in the patient-facing interface. Five tool-backed agents must call their case-specific read-only tool and match an exact deterministic output; the knowledge agent must use File Search. The current six-role contract and Ask Mama Link chat agent were verified live against the `mama-link` project and `gpt-4.1-mini` on 2026-09-24 using fictional data. See [Foundry setup](docs/foundry-setup.md).

An idempotent provisioning script is available at `infra/provision-foundry.ps1`. It targets the existing Sweden Central hackathon resource group and validates the requested model before deploying it.

A review-pending WHO/UNFPA public-source corpus is now indexed in Foundry File Search and a `mama-link-knowledge` agent was verified against it. It is a retrieval prototype, not an approved clinical corpus. Application Insights is also provisioned with automatic HTTP/Azure SDK instrumentation disabled; the app emits only aggregate operation count, status, and duration. Clinical approval, cloud model evaluation and authenticated deployment remain pending. The web app still uses the deterministic local workflow. See [the project assessment](docs/project-assessment.md) for the full PRD status.

The original PRD and case/evaluation datasets are preserved; the screening rules are versioned separately within the dataset pack. No source code from the reference repository was copied.
