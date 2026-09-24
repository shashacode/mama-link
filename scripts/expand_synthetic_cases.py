"""Deterministically expand the 24 synthetic fixtures to 100 geographically varied cases."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "mama_link_dataset/maternal"
runtime_path = DATA / "challenge-1-build/maternal_data_runtime.json"
authoring_path = DATA / "challenge-1-build/maternal_data.json"
locations = json.loads((DATA / "data/nigeria_locations.json").read_text(encoding="utf-8"))["states"]
evaluation = json.loads((ROOT / "evaluation_dataset.json").read_text(encoding="utf-8"))
expected_class = {
    item["id"].replace("eval-", "MAT-"): item["expected_output"]["classification"]
    for item in evaluation
}

# Evidence-informed synthetic scenario weights. The 2024 NDHS reports that
# teenage pregnancy ranges from 1% in Oyo to 32% in Kebbi, while UNICEF reports
# persistent early-pregnancy and care-access challenges in the North-West. These
# weights create a plausible demo distribution; they are not state prevalence.
state_counts = {
    "Kebbi": 8, "Sokoto": 7, "Katsina": 7, "Zamfara": 6, "Kano": 6,
    "Jigawa": 5, "Kaduna": 5, "Borno": 6, "Yobe": 5, "Bauchi": 5,
    "Adamawa": 4, "Gombe": 3, "Taraba": 3, "Niger": 2, "Plateau": 2,
    "Nasarawa": 1, "FCT": 1,
}
location_by_name = {state["name"]: state for state in locations}
expanded_locations = [location_by_name[name] for name, count in state_counts.items() for _ in range(count)]
assert len(expanded_locations) == 76
benchmark_hotspot_states = [
    "Kebbi", "Sokoto", "Katsina", "Zamfara", "Kano", "Jigawa", "Kaduna",
    "Borno", "Yobe", "Bauchi", "Adamawa", "Gombe", "Taraba", "Niger",
    "Lagos", "Oyo", "Osun", "Ogun", "Ondo", "Edo", "Delta", "Rivers",
    "Enugu", "Akwa Ibom",
]


def expand(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    base = payload["cases"][:24]
    cases = copy.deepcopy(base)
    for position, case in enumerate(cases):
        state = location_by_name[benchmark_hotspot_states[position]]
        case["hotspot_location"] = {
            "state": state["name"],
            "lga": state["places"][position % len(state["places"])],
        }
    critical = [case for case in base if expected_class[case["case_id"]] == "critical"]
    warning = [case for case in base if expected_class[case["case_id"]] == "warning"]
    normal = [case for case in base if expected_class[case["case_id"]] == "normal"]
    # Interleave risk levels so no state is portrayed as uniformly critical.
    # The weighted state counts, rather than a fabricated state-specific rate,
    # drive the geographic concentration shown by the prototype.
    risk_pattern = ("critical", "warning", "critical", "warning", "normal",
                    "critical", "warning", "warning", "critical", "normal")
    pools = {"critical": critical, "warning": warning, "normal": normal}
    pool_positions = {name: 0 for name in pools}
    for index in range(24, 100):
        risk = risk_pattern[(index - 24) % len(risk_pattern)]
        pool = pools[risk]
        source = copy.deepcopy(pool[pool_positions[risk] % len(pool)])
        pool_positions[risk] += 1
        state = expanded_locations[index - 24]
        source["case_id"] = f"MAT-{index + 1:03d}"
        source["patient_alias"] = f"synthetic_mat-{index + 1:03d}"
        source["location"] = {
            "state": state["name"],
            "lga": state["places"][index % len(state["places"])],
            "community": f"Synthetic community {index + 1}"
        }
        source["hotspot_location"] = {"state": state["name"], "lga": source["location"]["lga"]}
        source["age"] = 15 + ((index * 7) % 20)
        cases.append(source)
    payload["cases"] = cases
    payload["dataset_type"] = "synthetic_hackathon_demo_100_cases"
    payload["synthetic_geographic_basis"] = {
        "as_of": "2024",
        "method": "Evidence-informed scenario weights for hackathon testing; not observed case counts or prevalence.",
        "sources": [
            "Nigeria Demographic and Health Survey 2024 Summary Report",
            "UNICEF Nigeria Situation Analysis of Children and Adolescents 2024",
        ],
    }
    base_disclaimer = payload.get("disclaimer", "").split(" Geographic distribution is")[0]
    payload["disclaimer"] = (base_disclaimer +
        " Geographic distribution is intentionally north-heavy for scenario testing and is not prevalence evidence.")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


expand(runtime_path)
expand(authoring_path)
print("Expanded runtime and authoring datasets to 100 synthetic cases.")
