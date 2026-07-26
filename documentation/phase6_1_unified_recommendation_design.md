# Phase 6.1 unified recommendation design

Date: 2026-07-26

## Product decision

FarmLite presents one operational milk-yield estimate to the farmer. The
farmer-facing value is the existing FarmLite v1 milk prediction because that
value already belongs to the established recommendation flow and remains the
input used by the existing nutrition rules.

The collected-data milk candidate is retained only for backend compatibility,
automated tests, controlled model comparison, and future evaluation. It is not
rendered, included in the farmer PDF, averaged with the operational result, or
used to change the ration.

The collected-data milk candidate remains implemented for controlled technical evaluation. It uses genetic group and THI category and is not used as the farmer-facing milk prediction.

## Unified information hierarchy

The separate research-results panel has been removed. After a successful v1
recommendation, the right column uses the heading:

`FarmLite Recommendation for {animalName}`

The primary grid contains:

| Card | Value owner | Farmer-facing source |
|---|---|---|
| Expected Milk Yield | Existing FarmLite milk prediction model | `Source: FarmLite milk prediction model` |
| Predicted Dry-Matter Intake | Collected-data DMI model through API v2 | `Source: Collected-data DMI model` |
| Heat Stress Index | Backend THI calculation and category mapping | `Source: Backend THI calculation` |
| Advisory Daily Ration | Existing FarmLite nutrition rule engine | `Source: FarmLite nutrition rule engine` |

Milk and DMI are estimates. THI is backend-calculated. Ration quantity,
roughage, concentrate, mineral mix, water advice, feeding frequency,
confidence, and ration warnings remain rule-engine outputs.

## Input ownership

Animal name, tag, breed, age, and weight are shown from the selected livestock
record and are not duplicated as editable fields.

The normal Feeding Inputs section contains lactation stage, health status,
days in milk, previous-week average yield, body-condition score, ambient
temperature, humidity, and—when the controlled frontend feature is
enabled—Genetic Group.

The genetic-group display labels map only to the existing API values:

| Display label | Submitted value |
|---|---|
| Local cattle | `Local` |
| 50% Holstein Friesian cross | `HF50` |
| 62.5% Holstein Friesian cross | `HF62.5` |
| 75% Holstein Friesian cross | `HF75` |
| 87.5% Holstein Friesian cross | `HF87.5` |
| Unknown / Not sure | field omitted |

Breed never supplies or infers genetic group. Selecting Unknown / Not sure
allows valid weather to reach the backend for THI while the DMI value remains
unavailable.

## DMI and ration boundary

The UI and candidate-enabled PDF share this clarification:

> Predicted dry-matter intake and advisory ration quantity are different measures. Dry-matter intake represents feed material after moisture is excluded. The advisory ration is generated separately by the FarmLite nutrition rule engine. FarmLite does not convert the DMI prediction into roughage, concentrate or fresh-feed quantities.

No moisture conversion, as-fed conversion, subtraction, reconciliation, or
change to the ration rules is performed.

## Feature flags and failure behavior

The existing frontend and backend flags remain independent and default off.
When the frontend flag is off, the v2 endpoint is not called, the genetic-group
field and candidate cards are hidden, and the existing v1 PDF path is used.

When the candidate request is invalid, unavailable, aborted, stale, or fails
defensive response validation:

- the successful v1 milk result remains;
- the successful v1 ration remains;
- DMI is unavailable rather than zero;
- THI is shown only when supplied by a valid backend response; and
- stale candidate responses are ignored.

## Source attribution and limits

Detailed source attribution is restrained to the candidate-enabled PDF and
technical documentation:

`Source: Mendeley Data, DOI: 10.17632/954f6g36sb.2`

The DMI candidate requires wider multi-farm validation. AI estimates are
decision-support values, not guaranteed outcomes, and the recommendation does
not replace a veterinarian or qualified animal nutritionist.

## Responsive and accessibility design

The page uses a one-column base layout, a two-column primary-card grid from the
small breakpoint, and a two-column page layout only at the extra-large
breakpoint. Cards use `min-w-0`, values can wrap, and action buttons are
full-width on narrow screens. Native labels, keyboard-operable controls,
visible focus rings, `aria-invalid`, `aria-describedby`, status roles, and
alert roles remain in place.
