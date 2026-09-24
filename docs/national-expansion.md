# Nationwide prototype expansion

MAMA-Link now offers state and major-place selection for all 36 Nigerian states
and the FCT. The place list supports prototype navigation; it is not an official
administrative-boundary dataset.

## Facility information

The Find Care screen links to the Federal Ministry of Health and Social Welfare's
[Nigeria Health Facility Registry](https://hfr.fmohconnect.gov.ng/facilitieslist).
The registry covers hospitals and clinics across all states and the FCT and is
the verification source for facility address, contact, services and operating
status. Its read-only API requires an approved key, so this repository does not
copy or pretend to synchronize the full registry. Apply at the registry's
[developer page](https://www.hfr.fmohconnect.gov.ng/developers) before adding a
live server-side integration. Never put the API key in browser JavaScript.

The existing offline facility records remain fictional demonstration data. The
interface labels them for verification and never claims that they are nearest,
open or currently capable.

## Emergency information

The emergency panel uses **112**, assigned by the Nigerian Communications
Commission as the national Emergency Communication Centre number for emergency
services. Connection and local response availability may vary. MAMA-Link does
not dispatch an ambulance or notify a facility.

## Synthetic cases and hotspot map

The runtime dataset contains 100 synthetic cases. The first 24 retain their
original benchmark labels. Cases 25–100 reuse known synthetic clinical patterns
and distribute them across selected places, with an intentional northern skew
for hotspot-interface testing. This distribution is not observational data,
does not estimate prevalence, and must not be used to characterize any state,
ethnic group or community.

The `/api/hotspots` endpoint aggregates only those fictional cases. The web app
joins those aggregates to 37 state/FCT polygons from the 2019 OSGOF boundary
layer published through the [UN OCHA GIS service](https://gis.unocha.org/server/rest/services/Hosted/NGA_Administrative_Bounderies/FeatureServer/layers).
The checked-in GeoJSON uses three-decimal coordinate precision and a server-side
0.02-degree simplification so it loads quickly. Selecting a state polygon reveals
its synthetic totals and place breakdown. Colour intensity is `critical × 3 +
warning`; it is a test-data count and not a prevalence rate.

## Language and voice access

The interface provides a first-pass navigation and headline translation for
English, Nigerian Pidgin, Yoruba, Igbo and Hausa. Clinical and legal review by
fluent speakers remains required before public deployment. Browser speech
recognition supports English, Pidgin through Nigerian English, Yoruba, Igbo and
Hausa where the user's browser exposes those language models. Every transcript
must be reviewed before submission; free text remains excluded from automated
classification and persistence.

## Longitudinal anomaly detection

Each new synthetic assessment is compared with the latest assessment in the
same browser session. The prototype flags configured changes in systolic blood
pressure, diastolic blood pressure, temperature, heart rate, or multiple newly
reported symptoms. It is deterministic change detection, not a trained model,
diagnosis or assurance of safety. The assessment workflow continues to use the
versioned screening rules as its authoritative classifier.

### Evidence-informed scenario weighting

The 100-case map sample is weighted toward northern states using the Nigeria DHS 2024 finding that teenage pregnancy ranged from 1% in Oyo to 32% in Kebbi, together with UNICEF evidence on early pregnancy, child marriage and healthcare-access barriers in northern Nigeria. The 24 benchmark fixtures retain their clinical workflow locations for repeatable referral tests and carry a separate hotspot_location used only by the synthetic analytics layer. This prevents the original Ondo-based benchmark suite from distorting the national demonstration. These are scenario weights, not copied surveillance counts, state prevalence estimates or predictions.

Sources: [Nigeria DHS 2024 Summary](https://dhsprogram.com/pubs/pdf/SR294/SR294.pdf); [UNICEF Nigeria Situation Analysis 2024](https://www.unicef.org/nigeria/reports/situation-analysis-children-and-adolescents-nigeria-2024); [UNICEF Northwest adolescent girls evidence](https://www.unicef.org/nigeria/stories/better-outcomes-every-girl).
