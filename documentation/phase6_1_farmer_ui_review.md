# Phase 6.1 farmer UI review

Date: 2026-07-26

## Review outcome

The implementation now reads as one FarmLite recommendation instead of an
existing recommendation beside a research panel. One milk value is visible,
the DMI and ration values have separate ownership, and internal candidate
codes are not rendered.

## Approved farmer wording

| Area | Approved wording |
|---|---|
| Page title | `FarmLite Feed Recommendation` |
| Result title | `FarmLite Recommendation for {animalName}` |
| Milk heading | `Expected Milk Yield` |
| Milk support | `Estimated using the selected cow’s production and management inputs.` |
| Milk source | `Source: FarmLite milk prediction model` |
| DMI heading | `Predicted Dry-Matter Intake` |
| DMI support | `Estimated amount of feed dry matter consumed after excluding moisture.` |
| DMI source | `Source: Collected-data DMI model` |
| THI heading | `Heat Stress Index` |
| THI support | `Calculated from the submitted temperature and humidity.` |
| THI source | `Source: Backend THI calculation` |
| Ration heading | `Advisory Daily Ration` |
| Ration source | `Source: FarmLite nutrition rule engine` |
| No-warning state | `No cow or ration warnings were identified for the supplied inputs.` |
| Candidate failure | `Dry-matter intake estimate is currently unavailable.` |
| Unknown group | `A verified genetic group is required to generate the dry-matter intake estimate.` |
| Disclaimer | `This recommendation is advisory and should not replace guidance from a veterinarian or qualified animal nutritionist.` |

The ration explanation dynamically states:

`The FarmLite nutrition rule engine calculated an advisory ration quantity of {totalFeedKg} kg/day.`

The former model-supplied-feed sentence is filtered out of the rendered
explanation without changing the backend nutrition response.

## Removed farmer-facing concepts

The rendered UI no longer contains:

- a second or comparison milk result;
- a separate Research AI Predictions panel;
- Optional research prediction input;
- Individual Cow Milk Estimate;
- raw eligibility, scope, mapping, target, or estimator codes;
- geography-based dataset or model labels; or
- language implying that AI generated the ration composition.

The candidate response still retains its milk field internally for contract
compatibility; no farmer-facing component reads it.

## Warnings and model scope

Cow and ration warnings are de-duplicated before display. When none remain,
the exact no-warning message is shown. Candidate scope is summarized once:

> AI estimates are decision-support values and are not guaranteed outcomes. The DMI model was developed using a collected research dataset and requires wider multi-farm validation.

Friendly scope text replaces raw candidate status codes.

## Validation summary

- Phase 6 frontend safety tests: 25/25 pass.
- Phase 6.1 frontend tests: 32/32 pass.
- TypeScript checks: pass through both production builds.
- Phase 6.1-scoped ESLint: pass.
- Feature-enabled local Vite response: HTTP 200 with the controlled flag true.
- Default and feature-enabled builds: pass.
- Responsive and accessibility source audit: pass.

An authenticated browser session was not available, so final visual inspection
at real mobile and desktop viewport sizes remains a Phase 7 system-validation
item. The responsive classes and accessibility contracts are covered by
source-level tests in this phase.
