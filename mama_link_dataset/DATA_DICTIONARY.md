# Data Dictionary

## maternal_data.json / maternal_data_runtime.json
- `program`: product/program identifier.
- `dataset_type`: synthetic dataset marker.
- `cases`: array of synthetic maternal-health records.
- `case_id`: unique synthetic case identifier.
- `patient_alias`: non-identifying synthetic alias.
- `pregnancy_stage`: first_trimester, second_trimester, third_trimester, labour, or postpartum.
- `status`: labeled prototype target (`normal`, `warning`, `critical`) — omitted from runtime-safe file.
- `condition_focus`: scenario authoring label — omitted from runtime-safe file.
- `readings`: structured vital/context measurements.
- `symptoms`: boolean symptom flags used by tools and agents.
- `history`: optional structured context.
- `thresholds`: simplified prototype screening thresholds.

## facilities.json

The synthetic referral facility network used by deterministic capability matching.

## facility_registry.json.gz

Compressed import generated from `Nigeria_Healthcare_Facility_Registry_Phase_1.xlsx`.
It contains 42,063 nationwide registry directory records with facility identity,
location, ownership, level, operation/registration/license status and coordinates.
Contact fields come from the workbook's maternal-emergency verification queue and
remain unverified where the workbook says `Pending verification`. Empty capabilities
are intentional: registry names and levels are not treated as proof of clinical service.
Regenerate it with `py scripts/import_facility_registry.py` after replacing the workbook.
- `facility_id`: unique fictional facility ID.
- `capabilities`: array used by referral-tool filtering.
- `status`: simulated availability.
- `latitude` / `longitude`: demo geospatial coordinates.
- `c_section`, `blood_services`, `emergency_obstetric_care`, `fistula_services`: convenience booleans.

## support_resources.json
- `resource_id`: synthetic organization/service ID.
- `service_types`: support categories.
- `coverage`: simulated service area.
- `availability`: simulated operational status.
- `requires_human_confirmation`: whether tool action should require confirmation.

## evaluation_dataset.json
- `id`: evaluation row ID.
- `input`: text sent to the target agent.
- `expected_output.classification`: expected prototype class.
- `expected_output.red_flags`: expected relevant features.
- `expected_output.urgency`: low/medium/high.
- `expected_output.recommended_action`: expected action type.
- `expected_output.required_facility_capabilities`: capabilities referral agent should seek.
- `expected_output.prohibited_behavior`: safety behaviors the agent must avoid.

## eval_portal.jsonl
Each line has:
- `query`: agent input.
- `ground_truth`: JSON-encoded expected output, matching the FrontierWeekHack portal pattern.
