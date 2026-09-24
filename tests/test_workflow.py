import copy
import unittest
from mama_link.core import get_case, load_cases, screen, run_workflow, find_facilities


class WorkflowTests(unittest.TestCase):
    def test_remaining_warning_cases_receive_review_and_referral(self):
        for identifier in ("MAT-013", "MAT-014", "MAT-015", "MAT-017", "MAT-024"):
            with self.subTest(identifier=identifier):
                result = run_workflow(identifier)
                self.assertEqual(result["risk"]["classification"], "warning")
                self.assertEqual(result["required_facility_capabilities"], ["maternal_assessment"])
                self.assertTrue(result["facilities"])

    def test_adolescent_support_and_unknown_input(self):
        self.assertTrue(any("adolescent_support" in r["service_types"] for r in run_workflow("MAT-021")["support"]))
        self.assertEqual(screen({"symptoms": {"seizure": 1}})["classification"], "unassessed")
        self.assertEqual(screen({"readings": {"temperature": {"value": float('inf')}}})["classification"], "unassessed")

    def test_previously_missed_emergencies_complete_referral_workflow(self):
        for case_id, rule_id, capabilities in [
            ("MAT-009", "R-008", {"emergency_obstetric_care", "maternal_infection_management"}),
            ("MAT-018", "R-009", {"emergency_obstetric_care"}),
        ]:
            with self.subTest(case_id=case_id):
                result = run_workflow(case_id)
                self.assertEqual(result["risk"]["classification"], "critical")
                self.assertIn(rule_id, result["risk"]["matched_rules"])
                self.assertEqual(set(result["required_facility_capabilities"]), capabilities)
                self.assertTrue(result["facilities"])
                for facility in result["facilities"]:
                    self.assertTrue(capabilities <= set(facility["capabilities"]))
                self.assertTrue(any("emergency_transport" in r["service_types"]
                                    for r in result["support"]))
                self.assertEqual(result["referral"]["status"], "awaiting_consent")
                self.assertFalse(result["referral"]["sent"])
                consented = run_workflow(case_id, consent=True)
                self.assertEqual(consented["referral"]["status"], "simulated")
                self.assertFalse(consented["referral"]["sent"])

    def test_postpartum_cluster_requires_each_condition(self):
        for missing in ("postpartum", "temperature", "foul_smelling_discharge", "severe_weakness"):
            with self.subTest(missing=missing):
                case = copy.deepcopy(get_case("MAT-009"))
                if missing == "postpartum":
                    case["pregnancy_stage"] = "third_trimester"
                elif missing == "temperature":
                    case["readings"]["temperature"]["value"] = None
                else:
                    case["symptoms"].pop(missing)
                self.assertNotIn("R-008", screen(case)["matched_rules"])

    def test_cluster_temperature_boundary_and_fever_only(self):
        case = copy.deepcopy(get_case("MAT-009"))
        case["readings"]["temperature"]["value"] = 38.0
        self.assertEqual(screen(case)["classification"], "critical")
        case["readings"]["temperature"]["value"] = 37.9
        self.assertNotIn("R-008", screen(case)["matched_rules"])
        self.assertEqual(screen(get_case("MAT-010"))["classification"], "warning")

    def test_breathlessness_does_not_require_chest_pain_or_case_id(self):
        self.assertEqual(screen({"symptoms": {"severe_breathlessness": True}})
                         ["classification"], "critical")
        self.assertEqual(screen({"symptoms": {"severe_breathlessness": False}})
                         ["classification"], "unassessed")
        self.assertEqual(screen({"symptoms": {}})["classification"], "unassessed")

    def test_obstructed_labour_routes_to_capable_hospital(self):
        result = run_workflow("MAT-005")
        self.assertEqual(result["risk"]["classification"], "critical")
        for facility in result["facilities"]:
            self.assertTrue({"c_section", "blood_services", "emergency_obstetric_care"}
                            <= set(facility["capabilities"]))
        self.assertTrue(result["facilities"])
        self.assertEqual(result["referral"]["status"], "awaiting_consent")

    def test_alert_is_never_sent_even_with_demo_consent(self):
        result = run_workflow("MAT-005", consent=True)
        self.assertEqual(result["referral"]["status"], "simulated")
        self.assertFalse(result["referral"]["sent"])

    def test_no_match_is_not_reassurance(self):
        self.assertEqual(screen(get_case("MAT-001"))["classification"], "unassessed")
        self.assertEqual(screen({})["classification"], "unassessed")
        self.assertEqual(screen({})["guidance"]["urgency_label"], "Lower urgency, but not a clean bill of health")

    def test_screening_result_explains_urgency_and_possible_concern(self):
        result = screen({"symptoms": {"heavy_bleeding": True}})
        self.assertEqual(result["guidance"]["urgency_label"], "Emergency now")
        self.assertIn("dangerous blood loss", result["guidance"]["concern"])
        self.assertIn("Emergency now", result["message"])

    def test_diastolic_alone_and_critical_precedence(self):
        case = copy.deepcopy(get_case("MAT-003"))
        case["readings"]["systolic_bp"]["value"] = 120
        self.assertEqual(screen(case)["classification"], "critical")

    def test_fistula_referral(self):
        result = run_workflow("MAT-011")
        self.assertEqual(result["facilities"][0]["facility_id"], "FAC-005")

    def test_no_capable_facility_no_fallback(self):
        self.assertEqual(find_facilities(["nonexistent_capability"], {"state": "Ondo"}), [])

    def test_runtime_has_no_answer_labels(self):
        for case in load_cases():
            self.assertFalse({"status", "condition_focus", "expected_output"} & case.keys())

    def test_all_fixtures_execute(self):
        for case in load_cases():
            result = run_workflow(case["case_id"])
            self.assertEqual(len(result["trace"]), 5)
            self.assertFalse(result["referral"]["sent"])


if __name__ == "__main__":
    unittest.main()
