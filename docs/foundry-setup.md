# Connect the optional six-agent Foundry demo

The web app runs locally without Azure. The separate CLI orchestrates six bounded roles: intake, triage, knowledge, referral, transport support and follow-up. Ask Mama Link uses the Foundry model deployment configured by `AZURE_AI_MODEL_DEPLOYMENT_NAME`; this project's available deployment is `gpt-4.1-mini`. The environment value, saved chat-agent model and live Foundry deployment must agree. It follows Microsoft's [prompt-agent quickstart](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent) and [function-calling documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling) for Azure AI Projects 2.x.

The current six-role contract was verified live on 2026-09-24 against the `mama-link` project and `gpt-4.1-mini` using fictional case `MAT-005`. All five bounded tool agents returned their exact authoritative result and the knowledge agent used File Search. Ask Mama Link chat v2 was also verified through the localhost `/api/chat` path with explicit context-sharing consent.

## Prerequisites

An Azure subscription, an existing Foundry project, a deployed model supporting function calls, and permission to create agent versions and invoke the model. Choose a deployment in your own subscription; the app does not provision billable infrastructure automatically.

## Provision this project's Azure resources

The provisioning script targets the existing `foundry-hackathon-rg-0c39e178` resource group in Sweden Central. Its defaults are a `mamalink-ai-258f106f5903` Foundry resource, `mama-link` project, and `gpt-4.1-mini` deployment (version `2025-04-14`, Global Standard, capacity 10).

```powershell
.\infra\provision-foundry.ps1
.\infra\check-foundry.ps1
```

The model deployment can incur usage charges. Global Standard inference can process prompts outside the resource region. The script checks Azure CLI 2.80+, confirms the existing resource group, reuses matching resources, verifies model availability before deployment, and refuses to overwrite `.env`. It does not grant access to other users or deploy a public application.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-foundry.txt
Copy-Item .env.example .env
```

Fill in the project endpoint and model deployment name in `.env`. Do not overwrite an existing `.env`. No API key is needed for this Entra identity flow.

Ask Mama Link uses the standard Foundry deployment above. Emergency and medication questions continue to use local deterministic guidance before any model call.

```powershell
az login
.\.venv\Scripts\python.exe -m mama_link.foundry doctor
.\.venv\Scripts\python.exe -m mama_link.foundry bootstrap
.\.venv\Scripts\python.exe -m mama_link.foundry demo --case MAT-005
```

`doctor` checks configuration, package, manifest-role and contract-version readiness locally; it does not authenticate or prove connectivity. `bootstrap` creates five tool-agent versions (intake, triage, referral, transport support and follow-up) plus the chat agent, then records their references and output-contract version in `.local/foundry-agents.json`. Run it again only when a new version is intended. The knowledge agent remains separately provisioned by `bootstrap-knowledge` because that command creates and populates a vector store.

To publish only the five workflow agents while preserving a working chat version, use `bootstrap-tools`. This is the preferred command when the six-role output contract changes but Ask Mama Link does not:

```powershell
.\.venv\Scripts\python.exe -m mama_link.foundry bootstrap-tools
```

If only Ask Mama Link's saved model is stale, publish just a new chat-agent version:

```powershell
.\.venv\Scripts\python.exe -m mama_link.foundry bootstrap-chat
```

This preserves the other agent references and records the chat model in the manifest. It creates persistent Azure state and model use can incur charges, so run it only when a new chat version is intended. Until the manifest and configured deployment match, the web UI reports the online assistant as unavailable instead of silently presenting a generic local paragraph as an agent response.

`demo` runs all six roles in order. It makes billable model calls and sends only the selected synthetic case/tool results plus a general educational File Search query derived from matched synthetic topics. Temporary conversations are deleted afterward. Agent versions remain in the project for inspection.

Tool execution is restricted to the requested case and role. No dispatch, consent mutation, filesystem or general-purpose execution tool is available to the model. The bounded function-call loop rejects answers without tool use and any intake, classification, facility, support or follow-up output that differs from the authoritative local result. Knowledge answers are rejected unless the response contains a File Search call. The web UI continues to use the deterministic local workflow, even if a `.env` is present.

## Monitoring and evaluation status

Application Insights is connected to the Foundry project as `mamalink-appinsights`. Metadata-only agent spans and aggregate metrics are reaching the linked 30-day Log Analytics workspace. On 2026-09-25 the workspace contained events, traces, dependencies and metrics for all seven named agents: intake, triage, knowledge, referral, transport support, follow-up and Ask Mama Link chat. Prompts, model outputs, symptoms, notes, case IDs and profile data are not recorded by the app's manual telemetry.

The Foundry Evaluation portal now contains a bounded, synthetic baseline for every agent. The final selected runs passed all 24 cases:

| Agent | Evaluation method | Passed |
| --- | --- | ---: |
| Intake | Completed stored responses | 3/3 |
| Triage | Completed stored responses | 4/4 |
| Knowledge | Direct Foundry agent target | 3/3 |
| Referral | Completed stored responses | 4/4 |
| Transport support | Completed stored responses | 3/3 |
| Follow-up | Completed stored responses | 3/3 |
| Ask Mama Link chat | Direct Foundry agent target | 4/4 |

Foundry can invoke hosted chat and File Search agents directly. It cannot execute the five client-local Python function tools, so direct target runs for those agents correctly show skipped rows. Their scored baseline instead runs each restricted local tool workflow to completion, retains its Foundry response ID, and evaluates that stored interaction for intent resolution, tool-call accuracy and tool-input accuracy. This preserves the actual tool trace while avoiding a misleading empty evaluation.

The versioned evidence, evaluation/run IDs and portal report links are in [`foundry-evaluation-latest.json`](foundry-evaluation-latest.json). The effective modeled ceiling for the retained baseline plus the corrected triage rerun was 329,280 tokens, below the configured 500,000-token cap; actual billing depends on Azure usage records. No optimizer was run.

Reproduce the baselines only after an intentional agent, prompt, model or tool-contract change:

```powershell
.\.venv\Scripts\python.exe scripts\run_foundry_evaluations.py --max-estimated-tokens 500000
.\.venv\Scripts\python.exe scripts\run_foundry_response_evaluations.py --max-combined-estimated-tokens 500000
```

The current Azure user can operate the project but cannot create role assignments. For trace-filtered service-side evaluations, an Azure RBAC administrator still needs to grant the project managed identity (`e35299f3-74d8-4635-9a51-bc3c179f0258`) **Log Analytics Reader** on both the Application Insights resource and its Log Analytics workspace. This does not block the connected monitoring dashboards or the completed evaluations above.

## Remaining production milestones

1. Have a qualified clinical owner review and approve the prototype corpus in `knowledge/public-sources`; it remains explicitly marked pending review.
2. Add held-out grounding, unsafe-advice and adversarial tests. Current synthetic baselines demonstrate software behaviour, not clinical performance.
3. Keep the telemetry allow-list metadata-only and review it whenever instrumentation changes.
4. Add authenticated hosting, approved data handling, verified facility availability and independently authorized notification integrations before external clinical use.

## Knowledge and monitoring commands

The live project contains a `mama-link-knowledge` v1 prompt agent and the
`mama-link-public-sources` vector store. Rebuild and smoke-test them with:

```powershell
.\.venv\Scripts\python.exe -m mama_link.foundry bootstrap-knowledge
.\.venv\Scripts\python.exe -m mama_link.foundry knowledge-demo
```

Each bootstrap creates a new vector store and agent version, so use it only when
the corpus or agent definition changes. File Search and model calls can incur
Azure charges.

Application Insights and its 30-day Log Analytics workspace are provisioned by:

```powershell
.\infra\provision-monitoring.ps1
```

The script is idempotent, creates the Foundry project connection when missing, and writes the connection string to ignored `.env` without printing it. Restart the web process after provisioning. Creating the connection does not grant the managed identity the separate Log Analytics Reader role described above.

Live cloud-agent, monitoring and evaluation success is claimed only for the dated synthetic baseline. Clinical approval and public deployment are not claimed.
