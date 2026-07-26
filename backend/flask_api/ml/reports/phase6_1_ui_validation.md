# Phase 6.1 UI validation report

Date: 2026-07-26

## Result

PASS WITH VISUAL-ENVIRONMENT LIMITATIONS

The farmer UI presents one expected milk value from the existing FarmLite
prediction, one collected-data DMI value when available, backend THI, and the
existing advisory ration in a unified result panel.

The collected-data milk candidate remains implemented for controlled technical evaluation. It uses genetic group and THI category and is not used as the farmer-facing milk prediction.

## Ownership checks

| Output | Runtime source | Farmer label | Result |
|---|---|---|---|
| Expected milk | Existing v1 recommendation response | FarmLite milk prediction model | PASS |
| DMI | API v2 `ml_predictions.dmi_kg_day` | Collected-data DMI model | PASS |
| THI/category | API v2 `environment` | Backend THI calculation | PASS |
| Ration and composition | Existing v1 recommendation response | FarmLite nutrition rule engine | PASS |

The v2 milk field remains in the typed response and defensive validator but is
not consumed by the farmer component or PDF.

## Controlled scenarios

- Known group at 28 C and 75% humidity: HTTP 200, `ELIGIBLE`, THI 79.045,
  category T1, DMI 11.390466994631726 kg DM/cow/day.
- Genetic group omitted for Unknown / Not sure: HTTP 200,
  `FALLBACK_REQUIRED`, THI 79.045, DMI unavailable, fallback
  `GENETIC_GROUP_MISSING`.
- Humidity 101%: HTTP 200, `FALLBACK_REQUIRED`, THI and DMI unavailable,
  fallback `ENVIRONMENT_INVALID`.
- Frontend candidate flag disabled: v2 request initiation and candidate
  rendering are both guarded; the legacy PDF branch remains.
- Candidate request failure: successful v1 recommendation state is not
  cleared; stale requests are aborted and ignored.

Raw codes above are recorded only as technical evidence and are not rendered
to farmers.

## Accessibility and responsive audit

The selected-animal form and candidate fields retain native controls,
associated identifiers, `aria-invalid`, `aria-describedby`, alert/status
roles, keyboard behavior, visible focus styles, wrapped values, `min-w-0`,
single-column base layout, and breakpoint-controlled grids.

An authenticated browser was unavailable. Mobile and desktop rendering were
therefore verified by compiled responsive structure and source inspection, not
pixel-level screenshot review.

## Automated evidence

- Phase 6 safety suite: 25/25 PASS.
- Phase 6.1 suite: 32/32 PASS.
- Phase 6.1-scoped ESLint: PASS.
- Feature-enabled build and Vite HTTP smoke check: PASS.
- Default-disabled build: PASS.
- Backend regression suite: 307/307 PASS.
