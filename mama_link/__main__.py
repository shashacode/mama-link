import argparse
import json
from .core import DATA, load_cases, read_json, run_workflow, facility_supports


def evaluate():
    # Labels are read only here, after the runtime has produced each prediction.
    cases = load_cases()
    predictions = {c["case_id"]: run_workflow(c["case_id"]) for c in cases}
    labels = read_json(DATA / "challenge-3-evaluate/ground_truth_labels.json")
    rows = []
    for label in labels:
        case_id = "MAT-" + label["id"].split("-")[-1]
        result = predictions[case_id]
        actual = result["risk"]["classification"]
        expected_caps = label["required_facility_capabilities"]
        referral_correct = bool(result["facilities"]) and all(
            all(facility_supports(f, c) for c in expected_caps) for f in result["facilities"])
        rows.append({"case_id": case_id, "expected": label["classification"],
                     "actual": actual, "match": actual == label["classification"],
                     "referral_correct": referral_correct})
    emergencies = [r for r in rows if r["expected"] == "critical"]
    return {"scope": "Synthetic screening rules evaluation; no model or clinical validation",
            "cases": len(rows), "matches": sum(r["match"] for r in rows),
            "rules_version": read_json(DATA / "data/screening_rules.json")["version"],
            "assessed": sum(r["actual"] != "unassessed" for r in rows),
            "expected_emergencies": len(emergencies),
            "emergencies_detected": sum(r["actual"] == "critical" for r in emergencies),
            "referral_matches_for_expected_nonroutine": sum(r["referral_correct"] for r in rows if r["expected"] != "normal"),
            "expected_nonroutine": sum(r["expected"] != "normal" for r in rows),
            "emergency_recall": sum(r["actual"] == "critical" for r in emergencies) / len(emergencies)
            if emergencies else None,
            "misses": [r for r in rows if not r["match"]], "results": rows}


def main():
    parser = argparse.ArgumentParser(description="MAMA-Link synthetic hackathon starter")
    parser.add_argument("command", choices=["cases", "demo", "evaluate"])
    parser.add_argument("--case", default="MAT-005")
    parser.add_argument("--consent", action="store_true", help="Simulate consent; never sends an alert")
    args = parser.parse_args()
    if args.command == "cases":
        result = [{"case_id": c["case_id"], "stage": c["pregnancy_stage"]} for c in load_cases()]
    elif args.command == "evaluate":
        result = evaluate()
    else:
        try:
            result = run_workflow(args.case, args.consent)
        except ValueError as error:
            parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
