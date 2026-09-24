from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "MAMA-Link-Hackathon-Submission.docx"
PURPLE = "5B4BDB"
DARK = "17233C"
LIGHT = "F1F3FF"
GOLD = "E9A23B"
GRAY = "5F6673"


def shade(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd")) or OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    if shd.getparent() is None:
        tc_pr.append(shd)


def borders(table, color="D9D9D9"):
    tbl_pr = table._tbl.tblPr
    old = tbl_pr.find(qn("w:tblBorders"))
    if old is not None:
        tbl_pr.remove(old)
    node = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        item = OxmlElement(f"w:{edge}")
        item.set(qn("w:val"), "single")
        item.set(qn("w:sz"), "6")
        item.set(qn("w:color"), color)
        node.append(item)
    tbl_pr.append(node)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tag = OxmlElement("w:tblHeader")
    tag.set(qn("w:val"), "true")
    tr_pr.append(tag)


def set_cell_margin(cell, top=100, start=120, bottom=100, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}")) or OxmlElement(f"w:{name}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        if node.getparent() is None:
            tc_mar.append(node)


def set_width(cell, inches):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW")) or OxmlElement("w:tcW")
    tc_w.set(qn("w:w"), str(int(inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")
    if tc_w.getparent() is None:
        tc_pr.append(tc_w)


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    borders(t)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        shade(c, DARK)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)
        set_cell_margin(c)
        if widths:
            set_width(c, widths[i])
    set_repeat_header(t.rows[0])
    for row_index, values in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(values):
            if row_index % 2:
                shade(cells[i], "F7F8FC")
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            r.font.size = Pt(8.5)
            set_cell_margin(cells[i])
            if widths:
                set_width(cells[i], widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def add_field(paragraph, instruction):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = instruction
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, text, end])


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.add_run(text)
    return p


def numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.add_run(text)
    return p


def add_flow(doc, items):
    t = doc.add_table(rows=1, cols=len(items))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, item in enumerate(items):
        cell = t.cell(0, i)
        shade(cell, PURPLE if i % 2 == 0 else DARK)
        set_cell_margin(cell, 150, 80, 150, 80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(item)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(8)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.72)
sec.bottom_margin = Inches(0.72)
sec.left_margin = Inches(0.78)
sec.right_margin = Inches(0.78)

styles = doc.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"].font.size = Pt(10)
styles["Normal"].paragraph_format.space_after = Pt(6)
styles["Normal"].paragraph_format.line_spacing = 1.12
styles["Title"].font.name = "Aptos Display"
styles["Title"].font.size = Pt(30)
styles["Title"].font.bold = True
styles["Title"].font.color.rgb = RGBColor(0, 0, 0)
for name, size in (("Heading 1", 19), ("Heading 2", 14), ("Heading 3", 11)):
    s = styles[name]
    s.font.name = "Aptos Display"
    s.font.size = Pt(size)
    s.font.bold = True
    s.font.color.rgb = RGBColor(0, 0, 0)
    s.paragraph_format.space_before = Pt(12)
    s.paragraph_format.space_after = Pt(5)

header = sec.header.paragraphs[0]
header.text = "MAMA Link   Microsoft Foundry multi agent solution"
header.style = styles["Caption"]
header.runs[0].font.color.rgb = RGBColor.from_string(GRAY)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run("Hackathon submission   ")
add_field(footer, "PAGE")

# Cover
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(50)
p.add_run("MAMA LINK").bold = True
p.runs[0].font.size = Pt(16)
p.runs[0].font.color.rgb = RGBColor.from_string(PURPLE)
title = doc.add_paragraph(style="Title")
title.add_run("Multi Agent Maternal Health Coordination Solution")
sub = doc.add_paragraph()
sub.add_run("End to end solution design and production readiness plan").bold = True
sub.runs[0].font.size = Pt(16)
sub.runs[0].font.color.rgb = RGBColor.from_string(DARK)
doc.add_paragraph("Final activity submission for the Microsoft Foundry hackathon")
doc.add_paragraph("Prepared 18 September 2026")
doc.add_paragraph()
add_flow(doc, ["Recognize", "Assess", "Ground", "Refer", "Support", "Escalate"])
doc.add_paragraph()
p = doc.add_paragraph()
p.add_run("Submission position. ").bold = True
p.add_run("MAMA-Link is a working synthetic hackathon prototype with deployed Foundry agents, deterministic safety tools, File Search grounding, Application Insights monitoring, and a tested local web workflow. It is not clinically validated and is not deployed for real patient care.")
doc.add_page_break()

heading(doc, "Executive summary")
doc.add_paragraph("MAMA-Link addresses a coordination problem in maternal health: a person reporting danger signs may need risk recognition, appropriate facility capabilities, transport or social support, and a clear escalation path at the same time. The prototype coordinates these tasks through specialized agents while keeping safety-critical classification and referral selection under deterministic tools.")
doc.add_paragraph("The implemented solution uses three Microsoft Foundry prompt agents: a Triage Agent, a Referral Agent, and a Knowledge Agent. The first two must call restricted tools and their final structured outputs are checked against authoritative local workflow results. The Knowledge Agent searches a small WHO and UNFPA public-source corpus through Foundry File Search. Application Insights receives only aggregate operation count, status, and duration. The local application provides intake, classification, capability-aware matching, history, consent-gated simulated referral, and an evaluation dashboard.")
doc.add_paragraph("The evidence supports a hackathon demonstration: 25 automated tests pass; all 7 expected emergency fixtures are detected; 19 of 24 fixture classifications match; and all 19 expected nonroutine cases receive matching referral capabilities. Five expected-normal cases remain unassessed because no clinically approved low-risk completion protocol exists. The next production steps are independent clinical review, held-out cloud evaluation, authentication, live data agreements, and controlled deployment.")

heading(doc, "Contents")
for item in [
    "1  Business scenario and intended users", "2  Multi agent solution design",
    "3  Tools data and knowledge", "4  End to end workflow",
    "5  Observability strategy", "6  Evaluation strategy",
    "7  Governance reliability and safety", "8  Deployment and improvement lifecycle",
    "9  Demonstration plan", "10  Current evidence and remaining work", "Appendices"
]:
    doc.add_paragraph(item)
doc.add_page_break()

heading(doc, "1 Business scenario and intended users")
heading(doc, "1.1 Business problem", 2)
doc.add_paragraph("Maternal-health escalation often spans several disconnected decisions. A symptom report must be assessed consistently, an appropriate level of urgency must be communicated, a facility must be selected for required capabilities rather than proximity alone, and available support must be identified. Delays or unsupported assumptions at any step can prevent a person from reaching suitable care.")
doc.add_paragraph("MAMA-Link demonstrates how an AI-assisted coordination workflow can organize these steps while preserving explicit human consent and deterministic safety controls. The system does not diagnose, prescribe, declare a person safe, or send a real alert.")
heading(doc, "1.2 Intended users", 2)
table(doc, ["User", "Need", "Prototype support"], [
    ["Pregnant or postpartum person and family", "Understand escalation status and available care options", "Structured intake, plain status, educational links, consent-controlled simulated referral"],
    ["Community health worker", "Recognize risk and coordinate appropriate referral", "Rule-based assessment, capability matching, traceable results"],
    ["Facility or referral coordinator", "Receive consistent referral context", "Structured referral preparation; no live transmission in prototype"],
    ["NGO or transport partner", "Match assistance to service and coverage", "Fictional support registry and availability filtering"],
    ["Clinical and operational owner", "Review safety, quality and system performance", "Versioned rules, tests, evaluation report and privacy-safe monitoring"],
], [1.45, 2.5, 3.2])
heading(doc, "1.3 Business outcome", 2)
doc.add_paragraph("The target outcome is a shorter and more reliable path from a reported concern to an appropriate, consented care-coordination action. For the hackathon, success means demonstrating observable agent collaboration, grounded retrieval, correct tool use, repeatable evaluation, and clear safety limits.")

heading(doc, "2 Multi agent solution design")
heading(doc, "2.1 Specialized agents", 2)
table(doc, ["Agent", "Responsibility", "Boundary", "Implemented evidence"], [
    ["Triage Agent", "Request the deterministic screening result for one synthetic case", "Cannot change case ID, diagnose, prescribe, downgrade classification, or answer before tool use", "mama-link-triage v1; live smoke test returned critical for MAT-005"],
    ["Referral Agent", "Request risk and capability-aware facility matches", "Cannot invent a facility, mutate consent, dispatch, or reorder validated facility IDs", "mama-link-referral v1; live smoke test returned FAC-009, FAC-002 and FAC-004"],
    ["Knowledge Agent", "Retrieve educational content from the indexed corpus", "Must use File Search, cite the source URL, acknowledge missing content, and avoid patient-specific advice", "mama-link-knowledge v1; live UNFPA retrieval verified"],
], [1.1, 2.0, 2.45, 1.6])
heading(doc, "2.2 Why multiple agents", 2)
doc.add_paragraph("The roles have different authority, tools, data, and failure modes. Separating them reduces the scope of each prompt and makes tool permissions reviewable. A deterministic triage output cannot be silently replaced by a fluent model answer; facility selection can be checked independently; and educational retrieval can be updated without changing emergency rules. Each role can also be evaluated, versioned, monitored, and approved separately.")
doc.add_paragraph("A single general agent would hold broader permissions and mix classification, retrieval, facility selection, and communication in one response. That design would make failures harder to locate and increase the risk of unsupported clinical statements or invented resources.")
heading(doc, "2.3 Architecture", 2)
add_flow(doc, ["Web intake", "Local API", "Triage", "Knowledge", "Referral", "User result"])
doc.add_paragraph("The web application sends validated structured inputs to FastAPI. The authoritative local workflow applies versioned screening rules, derives required facility capabilities, matches fictional facilities and support organizations, and prepares a referral. Foundry agents demonstrate bounded orchestration over this workflow: the Triage and Referral Agents call read-only functions; the Knowledge Agent queries its vector store. User consent is required before the local application changes a referral from awaiting consent to simulated. No outbound notification integration exists.")

heading(doc, "3 Tools data and knowledge")
table(doc, ["Component", "Used by", "Purpose", "Control"], [
    ["screen_case function", "Triage Agent", "Return deterministic classification for one requested fixture", "Strict schema; exact case ID; read-only"],
    ["referral_plan function", "Referral Agent", "Return classification and ordered capable facilities", "Strict schema; read-only; validated final output"],
    ["Foundry File Search", "Knowledge Agent", "Retrieve WHO and UNFPA educational material", "One pinned vector store; pending clinical review label"],
    ["Synthetic maternal dataset", "Local workflow", "24 fictional scenarios for regression and demonstration", "No real patient data"],
    ["Facility and support registries", "Local workflow", "Match capabilities, service area and simulated availability", "Fictional records; no nearest-care claim"],
    ["SQLite session store", "Web application", "Save assessment history and consent state", "Browser-session isolation; raw notes excluded"],
], [1.45, 1.25, 2.55, 1.9])
heading(doc, "3.1 Knowledge provenance", 2)
doc.add_paragraph("The prototype corpus records source URL, retrieval date and review status for WHO maternal mortality material, a WHO maternal and newborn counselling handbook, and the UNFPA obstetric fistula page. The corpus is intentionally labelled pending clinical review. It supports a retrieval demonstration and must not be described as an approved clinical protocol until a qualified owner records approval, jurisdiction, version, permitted use, and review date.")

heading(doc, "4 End to end workflow")
heading(doc, "4.1 Sequence of interactions", 2)
for text in [
    "The user selects a synthetic fixture or enters structured fictional symptoms and measurements.",
    "FastAPI validates the request. Free-text notes are treated as untrusted human-review context and are not interpreted or persisted.",
    "The deterministic screening engine applies critical-over-warning precedence and returns classification, risk level, matched rules and required capabilities.",
    "The Triage Agent calls screen_case and may return only the validated classification.",
    "The Knowledge Agent searches its vector store for relevant educational material and returns source-linked information with the pending-review statement.",
    "The Referral Agent calls referral_plan. The local workflow filters facilities by state, simulated availability and every required capability, then matches support organizations by service and coverage.",
    "The application presents urgency, capable facilities, support options, evidence boundaries and a consent control.",
    "If the user consents to a selected facility, the local record changes to simulated status. Nothing is sent externally.",
    "The system records aggregate operation status and duration and exposes evaluation results to the dashboard."
]:
    numbered(doc, text)
heading(doc, "4.2 Information passed between agents", 2)
doc.add_paragraph("Agents exchange the minimum structured context required for their role: a synthetic case ID for triage and referral, deterministic classification and facility IDs in validated outputs, and an educational question for retrieval. Raw session cookies, free-text notes, telemetry secrets and consent mutation authority are never passed to Foundry agents.")
heading(doc, "4.3 Failure behavior", 2)
bullet(doc, "An agent response without its required tool call is rejected.")
bullet(doc, "A tool request for another case or another role's tool is rejected.")
bullet(doc, "A classification or facility list that differs from the authoritative workflow is rejected.")
bullet(doc, "The tool loop stops after five iterations.")
bullet(doc, "Unknown clinical input remains unassessed; it is never converted to a safety claim.")
bullet(doc, "Missing capable facilities produce an empty result rather than a fabricated fallback.")

heading(doc, "5 Observability strategy")
heading(doc, "5.1 Implemented monitoring", 2)
doc.add_paragraph("Application Insights is connected to a Log Analytics workspace with 30-day retention. The application emits an allow-listed counter and duration histogram using only operation name, status and elapsed milliseconds. Automatic FastAPI, requests, URL, Azure SDK and database instrumentation is disabled. This prevents raw symptoms, prompts, notes, case IDs, session IDs, request paths, tool payloads and secrets from entering telemetry.")
table(doc, ["Signal", "Purpose", "Diagnostic use"], [
    ["Operation count by status", "Measure successful, rejected and failed operations", "Detect regressions, rejection spikes and availability problems"],
    ["Operation duration", "Measure latency distribution", "Find slow releases and establish performance targets"],
    ["Agent tool-call status", "Show whether a required tool completed", "Identify orchestration or permission failures"],
    ["Classification and referral evaluation metrics", "Measure fixture behavior outside production telemetry", "Detect rule regressions without logging health content"],
], [1.7, 2.45, 3.05])
heading(doc, "5.2 Production observability plan", 2)
doc.add_paragraph("A production dashboard would add availability, p50/p95 latency, agent and tool error rates, bounded-loop failures, retrieval success, source-citation presence, consent outcomes, referral acknowledgement and deployment version. Health-content metrics should be computed in a separately governed analytics process using approved de-identification and minimum aggregation thresholds. Alerts would cover sustained failures, latency breaches, missing grounding, abnormal tool rejection rates and telemetry gaps.")

heading(doc, "6 Evaluation strategy")
heading(doc, "6.1 Current test assets", 2)
table(doc, ["Asset", "Scope", "Current result", "Limit"], [
    ["Automated tests", "Rules, API security, session isolation, consent, facilities and agent boundaries", "25 of 25 pass", "Regression tests over known implementation"],
    ["24-case fixture evaluation", "Classification and capability matching", "19/24 labels; 7/7 emergencies; 19/19 nonroutine referral capability matches", "Five normal fixtures remain unassessed"],
    ["Foundry agent smoke test", "Required tool use and exact output validation", "Triage and referral passed for MAT-005", "One known synthetic case"],
    ["File Search smoke test", "Grounded retrieval and source URL", "UNFPA query passed", "Small review-pending corpus"],
], [1.5, 2.45, 1.95, 1.35])
heading(doc, "6.2 Evaluation criteria", 2)
table(doc, ["Criterion", "Measure", "Proposed release gate"], [
    ["Task adherence", "Required tool called; schema exact; no role expansion", "100 percent on safety-critical suite"],
    ["Tool usage", "Correct tool and case; bounded completion", "100 percent valid calls"],
    ["Groundedness", "Claims supported by retrieved approved source", "No unsupported clinical claims"],
    ["Relevance and coherence", "Response answers the request clearly", "Human-reviewed threshold on held-out set"],
    ["Safety", "No diagnosis, prescription, reassurance, fabricated facility or false dispatch claim", "Zero critical violations"],
    ["Referral accuracy", "All required capabilities present", "100 percent on emergency cases"],
    ["Emergency recall", "Expected emergencies escalated", "100 percent on approved benchmark"],
    ["Latency and reliability", "p95 completion and successful run rate", "Target set after load test"],
], [1.55, 3.8, 1.95])
heading(doc, "6.3 Development lifecycle integration", 2)
doc.add_paragraph("Every rule, prompt, model, tool schema, corpus or facility-vocabulary change should create a versioned evaluation run. Pull-request checks run deterministic tests and the fixture evaluation. A staging gate runs held-out Foundry tests for grounding, safety, prompt injection, tool misuse and unavailable resources. Clinical and operational owners review failures and approve release evidence. After deployment, aggregate monitoring and sampled, authorized quality review feed new regression cases. Agent versions remain immutable so changes can be compared and rolled back.")

heading(doc, "7 Governance reliability and safety")
table(doc, ["Risk", "Implemented control", "Production requirement"], [
    ["Unsafe medical generation", "Deterministic rules; prompts prohibit diagnosis/prescription; exact output validation", "Clinical validation, content policy, red-team evidence and escalation ownership"],
    ["False reassurance", "No-match becomes unassessed, never low or safe", "Clinically approved low-risk protocol"],
    ["Fabricated facility", "Capability and availability filter over fictional registry", "Verified live directory, freshness SLA and fallback operations"],
    ["Unauthorized referral", "Explicit facility consent; simulated status; no dispatch tool", "Strong identity, auditable consent and authorized partner integration"],
    ["Sensitive-data leakage", "Synthetic fixtures; notes not persisted; minimal telemetry", "DPIA, retention policy, encryption, RBAC, private networking and incident response"],
    ["Prompt injection", "Case content treated as data; strict tools and schemas", "Adversarial suite, content isolation and continuous monitoring"],
    ["Model or service failure", "Local deterministic workflow remains authoritative", "Retries, timeouts, circuit breaker, operational fallback and rollback"],
], [1.45, 3.0, 2.85])
heading(doc, "7.1 Consistency and maintainability", 2)
doc.add_paragraph("Rules have a declared version and explicit precedence. Agent versions and vector-store identifiers are recorded in local ignored manifests. Infrastructure scripts are idempotent and validate existing Azure resources. Dependencies are bounded and an exact environment lock is maintained. Tests cover boundary conditions and cross-session access. Documentation records assumptions, known gaps, commands and acceptance evidence.")
heading(doc, "7.2 Human accountability", 2)
doc.add_paragraph("A production service requires named clinical, product, privacy, security and operations owners. Clinical owners approve screening and knowledge versions; operational owners verify facility and partner availability; privacy and security owners approve data flows; and release owners sign the evaluation record. The system supports decisions but does not replace professional judgement or emergency services.")

heading(doc, "8 Deployment and improvement lifecycle")
table(doc, ["Stage", "Action", "Evidence or gate"], [
    ["Develop", "Change code, prompt, tool, rule or corpus in version control", "Peer review and traceable change record"],
    ["Verify", "Run 25 tests and 24-case evaluation", "No regression in emergency detection or safety boundaries"],
    ["Evaluate", "Run held-out Foundry quality, grounding, safety and adversarial suite", "Approved release report"],
    ["Deploy", "Publish authenticated FastAPI service and frontend through controlled Azure environment", "Managed identity, secrets, TLS, RBAC and health checks"],
    ["Monitor", "Observe aggregate reliability, latency, tool failures and safety indicators", "Dashboard, alert ownership and incident runbook"],
    ["Improve", "Convert authorized findings into tests and versioned changes", "Agent comparison, approval and rollback path"],
], [1.05, 3.8, 2.45])
heading(doc, "8.1 Current deployment position", 2)
doc.add_paragraph("The Azure Foundry account, project, gpt-4.1-mini deployment, three agent roles, vector store, Application Insights component and Log Analytics workspace are provisioned in Sweden Central. The application itself remains loopback-only because production authentication and partner data agreements are not implemented. Judges can run the application locally and inspect the cloud resources with the signed-in Azure account.")

heading(doc, "9 Demonstration plan")
heading(doc, "9.1 Recommended six minute recording", 2)
table(doc, ["Time", "Screen", "Narration and proof"], [
    ["0:00–0:40", "Title and problem", "Explain the fragmented maternal referral problem and intended users."],
    ["0:40–1:30", "Architecture", "Show the three agent responsibilities, restricted tools, File Search and deterministic authority."],
    ["1:30–2:40", "Local web app", "Open MAT-005, run assessment, show critical status, capable facilities and support matching."],
    ["2:40–3:20", "Consent", "Choose a facility and demonstrate simulated referral. State clearly that nothing is sent."],
    ["3:20–4:20", "Foundry", "Show the three agent versions, tool use and grounded UNFPA retrieval with source URL."],
    ["4:20–5:10", "Evaluation", "Show 25 passing tests, 7/7 emergency detection and explain the five unassessed normal fixtures."],
    ["5:10–5:40", "Monitoring", "Show Application Insights and the privacy-safe metrics design."],
    ["5:40–6:00", "Reflection", "Explain how specialization, tools, evaluation and monitoring moved the idea toward production readiness."],
], [0.85, 1.35, 5.1])
heading(doc, "9.2 Suggested demonstration scenario", 2)
doc.add_paragraph("Use synthetic case MAT-005, based on the PRD's prolonged-labour scenario. The expected demonstration path is critical classification, emergency-obstetric capability matching, support matching, explicit facility consent and a simulated referral state. In Foundry, run the two-agent demo and the knowledge demo separately. This accurately reflects the current implementation: the local web workflow is complete, while the cloud knowledge agent has not yet been inserted into the web request path.")
heading(doc, "9.3 Recording checklist", 2)
for text in [
    "Use fictional information only and close terminals containing secrets.",
    "Start the local server and verify /api/health before recording.",
    "Keep the Foundry project, agent list, vector store, Application Insights and evaluation output ready in separate tabs.",
    "Show tool calls or structured outputs, not only the final user interface.",
    "State the prototype limits and pending clinical review without minimizing them.",
    "End with the production plan and the specific evidence required for release."
]:
    bullet(doc, text)

heading(doc, "10 Current evidence and remaining work")
table(doc, ["Hackathon requirement", "Status", "Evidence or next step"], [
    ["Business problem and users", "Complete", "Defined in this report and PRD"],
    ["At least two specialized agents", "Complete", "Three deployed Foundry agent roles"],
    ["Tools and knowledge", "Complete for prototype", "Two strict functions and File Search vector store"],
    ["Information flow", "Complete", "Implemented local workflow and bounded Foundry demonstrations"],
    ["Observability", "Complete for prototype", "Application Insights and privacy-safe custom metrics"],
    ["Evaluation strategy", "Complete; cloud suite pending", "Tests and fixture metrics exist; add held-out Foundry evaluation"],
    ["Governance and reliability", "Plan complete", "Controls implemented; clinical approval and production governance pending"],
    ["Deployable workflow", "Partial", "Local app and Azure agents available; authenticated public hosting pending"],
    ["Recorded presentation", "Ready to record", "Six-minute script and checklist included"],
], [2.0, 1.45, 3.85])
doc.add_paragraph("The submission demonstrates the required design and production-readiness thinking with working prototype evidence. It should not claim production or clinical readiness. The most valuable next engineering milestone is a held-out Foundry evaluation suite covering tool adherence, grounding, unsafe advice, injection attempts and missing-resource behavior, followed by authenticated staging deployment.")

heading(doc, "Appendix A Azure resources")
table(doc, ["Resource", "Configured value"], [
    ["Resource group", "foundry-hackathon-rg-0c39e178"],
    ["Foundry account", "mamalink-ai-258f106f5903"],
    ["Foundry project", "mama-link"],
    ["Region", "Sweden Central"],
    ["Model deployment", "gpt-4.1-mini, version 2025-04-14, Global Standard, capacity 10"],
    ["Prompt agents", "mama-link-triage v1; mama-link-referral v1; mama-link-knowledge v1"],
    ["Vector store", "mama-link-public-sources"],
    ["Application Insights", "mamalink-insights-258f106f5903"],
    ["Log Analytics", "mamalink-logs-258f106f5903; 30-day retention"],
], [2.0, 5.3])

heading(doc, "Appendix B Reproduction commands")
commands = [
    ".\\scripts\\setup.ps1",
    ".\\scripts\\start.ps1",
    ".\\.venv\\Scripts\\python.exe scripts\\verify.py",
    ".\\infra\\check-foundry.ps1",
    ".\\.venv\\Scripts\\python.exe -m mama_link.foundry doctor",
    ".\\.venv\\Scripts\\python.exe -m mama_link.foundry demo --case MAT-005",
    ".\\.venv\\Scripts\\python.exe -m mama_link.foundry knowledge-demo",
    ".\\infra\\provision-monitoring.ps1",
]
for cmd in commands:
    p = doc.add_paragraph()
    r = p.add_run(cmd)
    r.font.name = "Consolas"
    r.font.size = Pt(9)

heading(doc, "Appendix C References")
refs = [
    "Microsoft. File search tool for Microsoft Foundry agents. https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/file-search",
    "Microsoft. Function calling with Foundry agents. https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling",
    "Microsoft. Enable OpenTelemetry in Application Insights. https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable",
    "World Health Organization. Maternal mortality. https://www.who.int/news-room/fact-sheets/detail/maternal-mortality",
    "World Health Organization. Counselling for Maternal and Newborn Health Care. https://iris.who.int/bitstream/handle/10665/44016/9789241547628_eng.pdf",
    "United Nations Population Fund. Obstetric fistula. https://www.unfpa.org/obstetric-fistula",
    "MAMA-Link product requirements document and synthetic evaluation assets in the project repository.",
]
for ref in refs:
    bullet(doc, ref)

# Prevent heading widows and set metadata.
doc.core_properties.title = "MAMA Link Multi Agent Maternal Health Coordination Solution"
doc.core_properties.subject = "Microsoft Foundry hackathon final activity submission"
doc.core_properties.author = "MAMA-Link Project Team"
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)
