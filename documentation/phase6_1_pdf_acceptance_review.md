# Phase 6.1 PDF acceptance review

Date: 2026-07-26

## Acceptance outcome

The candidate-enabled download path now generates a deterministic two-page
report titled:

`FarmLite Feed and Production Decision-Support Report`

The default feature-disabled path still generates the previously approved v1
report and does not invoke or expose candidate behavior.

## Page structure

Page 1 contains the FarmLite header, generated timestamp, animal name and tag,
selected-cow summary, four primary results, ration breakdown, nutrition-rule
explanation, and the DMI-versus-ration clarification.

Page 2 contains Cow and Ration Warnings, AI Model Scope, Value Sources,
Technical Source Notes, Limitations, and the Advisory Disclaimer.

Both pages use the FarmLite palette, controlled section blocks, a consistent
footer, and `Page {n} of 2`.

## Value ownership

The PDF states:

- `Expected milk yield: FarmLite milk prediction model`
- `Dry-matter intake: Collected-data DMI model`
- `Heat Stress Index: Backend THI calculation`
- `Advisory ration: FarmLite nutrition rule engine`

Technical source attribution is restrained to:

`DMI research-data source: Mendeley Data, DOI: 10.17632/954f6g36sb.2`

The collected-data milk candidate is absent from the PDF data interface,
content builder, result list, source list, narrative, and renderer.

## Failure and null behavior

If DMI is unavailable, the report prints `Unavailable`; it never substitutes
zero, `null`, `undefined`, or `NaN`. Expected milk and the advisory ration are
still populated from the successful v1 recommendation. THI is printed only
from the backend response.

## Automated acceptance evidence

The Phase 6.1 suite verifies:

- one milk result and one DMI result in the candidate-enabled data shape;
- no candidate milk field or candidate milk wording in PDF code;
- approved title, units, ownership labels, source note, explanation, and
  disclaimer;
- exactly two pages with controlled data;
- a real jsPDF ArrayBuffer larger than 3,000 bytes with DMI;
- a real two-page jsPDF ArrayBuffer larger than 2,500 bytes without DMI; and
- safe null formatting.

All 32 Phase 6.1 tests pass. A visual PDF renderer was not installed in this
environment, so typography and print-driver-specific rendering remain for
authenticated Phase 7 system review.
