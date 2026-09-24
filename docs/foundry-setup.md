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

## Remaining cloud milestones

1. Inspect and retain the 2026-09-24 live smoke-test traces for the current six-role contract; rerun only after an intentional agent or model change.
2. Have a qualified clinical owner review and approve the prototype corpus in `knowledge/public-sources`. The current WHO/UNFPA summary is indexed for demonstration and explicitly marked pending review.
3. Keep the Application Insights allow-list limited to aggregate operation count, status, and duration. Raw symptoms, prompts, notes, request paths, case IDs, session IDs, and tool payloads are excluded.
4. Run the supplied `eval_portal.jsonl` in Foundry and add held-out grounding, unsafe-advice and adversarial tests. Local fixture scores do not measure model quality.

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

The script is idempotent and writes the connection string to ignored `.env`
without printing it. Restart the web process after provisioning.
5. Add authenticated hosting, approved data handling, verified facility availability and independently authorized notification integrations before external clinical use.

No live cloud success, clinical approval, or public deployment is claimed by the local readiness report.
