"""Deterministic tools for the supplied synthetic fixtures, not clinical use."""
import json
from math import isfinite
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "mama_link_dataset" / "maternal"

SCREENING_GUIDANCE = {
    "R-001": ("Very high blood pressure after 20 weeks can be associated with a serious pregnancy complication.", "Seek emergency in-person care now."),
    "R-002": ("Raised blood pressure after 20 weeks needs assessment because it can be associated with pregnancy-related hypertension.", "Arrange a same-day clinical review and take the reading with you."),
    "R-003": ("A seizure during pregnancy can be a life-threatening emergency.", "Call 112 or go to emergency care now."),
    "R-004": ("Heavy bleeding in pregnancy or after birth can cause dangerous blood loss.", "Seek emergency care now and call 112 if immediate help is needed."),
    "R-005": ("Very long or blocked labour may need urgent obstetric intervention.", "Go to an emergency-capable maternity facility now."),
    "R-006": ("Continuous urine or stool leakage after birth needs assessment for a birth-related injury or infection.", "Arrange a clinical review soon, ideally within the next day."),
    "R-007": ("A temperature of 38 C or higher may occur with an infection, but the cause cannot be determined here.", "Arrange a same-day clinical review."),
    "R-008": ("Fever, foul-smelling discharge and severe weakness after birth may occur with a serious infection.", "Seek emergency in-person care now."),
    "R-009": ("Severe breathlessness can have a serious cause and needs urgent assessment.", "Seek emergency care now and call 112 if breathing is severely affected."),
    "R-010": ("Less fetal movement than usual needs prompt assessment because the baby may need checking.", "Contact a maternity provider or go for a same-day assessment now."),
    "R-011": ("Fatigue with unusual paleness can occur with anaemia or other conditions.", "Arrange a routine clinical review soon; seek urgent help if you rapidly worsen."),
    "R-012": ("A flagged glucose screen needs a clinician to interpret the result.", "Book a routine antenatal review and bring the screening result."),
    "R-013": ("Being unable to keep fluids down can lead to dehydration and may have an underlying cause.", "Arrange a same-day review; seek emergency help if you are faint or unable to drink."),
    "R-014": ("Clear fluid leakage may need assessment to check whether the waters have broken.", "Contact a maternity provider for a same-day assessment."),
    "R-015": ("Loss of consciousness can be a life-threatening emergency.", "Call 112 or go to emergency care now.")
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases():
    # Never load authoring labels or evaluation answers into the runtime.
    return read_json(DATA / "challenge-1-build/maternal_data_runtime.json")["cases"]


def get_case(case_id):
    for case in load_cases():
        if case["case_id"] == case_id:
            return case
    raise ValueError(f"Unknown synthetic case: {case_id}")


def matches(condition, values):
    results = []
    for key, expected in condition.items():
        if key == "any":
            results.append(any(matches(item, values) for item in expected))
        elif key.endswith("_gte"):
            value = values.get(key[:-4])
            results.append(isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)
                           and value >= expected)
        elif isinstance(expected, bool):
            results.append(values.get(key) is expected)
        else:
            results.append(key in values and values[key] == expected)
    return all(results)


def screen(case):
    ruleset = read_json(DATA / "data/screening_rules.json")
    values = dict(case.get("symptoms", {}))
    values["recent_glucose_screen_flagged"] = case.get("history", {}).get("recent_glucose_screen_flagged")
    for key, reading in case.get("readings", {}).items():
        values[key] = reading.get("value")
    values["gestational_age_weeks"] = values.get("gestational_age")
    values["temperature_c"] = values.get("temperature")
    values["postpartum"] = case.get("pregnancy_stage") == "postpartum"
    fired = [rule for rule in ruleset["rules"] if matches(rule["if"], values)]
    classification = max((r["classification"] for r in fired),
                         key={"warning": 1, "critical": 2}.get, default="unassessed")
    urgency = max((r["urgency"] for r in fired), key={"medium": 1, "high": 2}.get, default="unknown")
    risk_level = "emergency" if classification == "critical" else (
        "high" if urgency == "high" else "medium" if classification == "warning" else "unassessed")
    if fired:
        concern, next_step = SCREENING_GUIDANCE[fired[0]["rule_id"]]
        guidance = {"concern": concern, "next_step": next_step,
                    "urgency_label": "Emergency now" if classification == "critical" else
                    "Same-day review" if urgency == "high" else "Routine review"}
    else:
        guidance = {"concern": "No urgent pattern was detected from the selected symptoms and readings.",
                    "next_step": "Monitor how you feel and arrange routine care if symptoms persist, worsen or worry you.",
                    "urgency_label": "Lower urgency, but not a clean bill of health"}
    return {"classification": classification,
            "risk_level": risk_level, "urgency": urgency,
            "needs_referral": bool(fired),
            "rules_version": ruleset["version"],
            "matched_rules": [r["rule_id"] for r in fired],
            "reasons": [r["name"] for r in fired],
            "requires_human_review": True,
            "guidance": guidance,
            "message": (f"{guidance['urgency_label']}. {guidance['concern']} {guidance['next_step']} "
                        "Synthetic screening only: this does not diagnose a condition or confirm that everything is well.")
            if fired else (f"{guidance['urgency_label']}. {guidance['concern']} {guidance['next_step']} "
                           "Risk remains unassessed; human review is required.")}


def required_capabilities(result):
    rules = set(result["matched_rules"])
    capabilities = set()
    if result["classification"] == "critical":
        capabilities.add("emergency_obstetric_care")
    if rules & {"R-001", "R-002", "R-003"}:
        capabilities.add("hypertension_management")
    if "R-004" in rules:
        capabilities.add("blood_services")
    if "R-005" in rules:
        capabilities.update(["c_section", "blood_services"])
    # An emergency takes priority over a separate specialist follow-up.
    if "R-006" in rules and result["classification"] != "critical":
        capabilities.add("fistula_assessment")
    if "R-008" in rules:
        capabilities.add("maternal_infection_management")
    if rules & {"R-007", "R-010", "R-011", "R-012", "R-013", "R-014"} and not capabilities:
        capabilities.add("maternal_assessment")
    return sorted(capabilities)


def facility_supports(facility, capability):
    # Explicit demo crosswalk; never add capabilities to the source registry.
    if capability == "maternal_assessment":
        return bool(set(facility["capabilities"]) & {
            "antenatal_care", "postpartum_care", "emergency_obstetric_care"})
    return capability in facility["capabilities"]


def find_facilities(capabilities, location):
    if not capabilities or not location.get("state"):
        return []
    facilities = read_json(DATA / "data/facilities.json")["facilities"]
    # Dataset has no patient coordinates: do not invent distances or claim nearest.
    return sorted([f for f in facilities if f["status"] == "available"
                   and f["state"] == location["state"]
                   and all(facility_supports(f, c) for c in capabilities)],
                  key=lambda f: (f["lga"] != location.get("lga"), f["facility_id"]))


def find_support(services, location):
    resources = read_json(DATA / "data/support_resources.json")["resources"]
    area = {location.get("state"), location.get("lga")} - {None}
    return [r for r in resources if r["availability"] == "available"
            and area.intersection(r["coverage"])
            and set(services).intersection(r["service_types"])]


def detect_anomalies(case, prior_records=None):
    """Flag unusual longitudinal changes for review; this is not a diagnosis."""
    prior_records = prior_records or []
    current = {k: v.get("value") for k, v in case.get("readings", {}).items()
               if isinstance(v, dict) and isinstance(v.get("value"), (int, float))}
    flags = []
    if prior_records:
        previous_case = prior_records[0].get("case", {})
        previous = {k: v.get("value") for k, v in previous_case.get("readings", {}).items()
                    if isinstance(v, dict) and isinstance(v.get("value"), (int, float))}
        thresholds = {"systolic_bp": 20, "diastolic_bp": 15, "temperature": 1.0,
                      "heart_rate": 25}
        for key, change in thresholds.items():
            if key in current and key in previous and abs(current[key] - previous[key]) >= change:
                flags.append({"type": "measurement_change", "measurement": key,
                              "previous": previous[key], "current": current[key],
                              "message": f"Unusual change in {key.replace('_', ' ')}; human review required."})
        old_symptoms = {k for k, v in previous_case.get("symptoms", {}).items() if v}
        new_symptoms = {k for k, v in case.get("symptoms", {}).items() if v} - old_symptoms
        if len(new_symptoms) >= 2:
            flags.append({"type": "symptom_change", "new_symptoms": sorted(new_symptoms),
                          "message": "Multiple newly reported symptoms; human review required."})
    return {"status": "review_required" if flags else "no_longitudinal_anomaly_detected",
            "flags": flags, "records_compared": min(len(prior_records), 1),
            "message": "Prototype change detection only. Absence of a flag does not establish safety."}


def run_workflow(case_id, consent=False):
    case = get_case(case_id)
    return assess_case(case, consent=consent)


def assess_case(case, consent=False, prior_records=None):
    """Run structured input. Free text is retained for human review, never guessed."""
    case_id = case.get("case_id", "custom-demo")
    trace = []

    def step(name, function, *args):
        start = perf_counter()
        result = function(*args)
        trace.append({"step": name, "status": "completed",
                      "duration_ms": round((perf_counter() - start) * 1000, 3)})
        return result

    risk = step("maternal_risk_tool", screen, case)
    capabilities = required_capabilities(risk)
    location = case.get("location", {})
    facilities = step("facility_search", find_facilities, capabilities, location)
    services = ["referral_navigation"]
    if risk["classification"] == "critical":
        services += ["emergency_transport", "transport_subsidy"]
    if "fistula_assessment" in capabilities:
        services += ["fistula_referral", "rehabilitation"]
    if isinstance(case.get("age"), (int, float)) and case["age"] < 18:
        services += ["adolescent_support", "social_worker_referral"]
    support = step("support_search", find_support, services, location)
    anomaly = step("longitudinal_anomaly_detection", detect_anomalies, case, prior_records)
    eligible = risk["classification"] != "unassessed" and bool(facilities)
    alert_status = ("simulated" if consent else "awaiting_consent") if eligible else "not_prepared"
    trace.append({"step": "referral_preparation", "status": alert_status})
    return {"mode": "synthetic_local_simulation", "case_id": case_id, "risk": risk,
            "free_text_status": "requires_human_review" if case.get("notes") else "not_provided",
            "required_facility_capabilities": capabilities, "facilities": facilities,
            "ranking_note": "Same LGA first, then facility ID. Distance and live availability unknown.",
            "support": support,
            "anomaly": anomaly,
            "knowledge": {"status": "not_connected", "sources": [],
                          "message": "Approved document retrieval is pending Foundry File Search setup."},
            "referral": {"status": alert_status, "sent": False,
                         "facility_id": facilities[0]["facility_id"] if eligible else None,
                         "message": "Demo only. No person, facility or transport provider was contacted."},
            "trace": trace}
