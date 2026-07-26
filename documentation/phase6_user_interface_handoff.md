# Phase 6 user-interface handoff

Date: 2026-07-26
Audience: controlled local reviewers

## Enable for local review

Keep both flags off for normal behavior. For a controlled local session,
start the backend and frontend in separate terminals:

```powershell
# Backend terminal
$env:BANGLADESH_CANDIDATE_MODELS_ENABLED = "true"

# Frontend terminal, set before npm run dev
$env:VITE_BANGLADESH_CANDIDATE_UI_ENABLED = "true"
```

The accepted enabled values are `1`, `true`, `yes`, and `on`. Any other value
is false. Do not add either enabled value to a committed environment file.

## Reviewer workflow

1. Open the existing AI Feed Recommendation page.
2. Select a dairy cow as before.
3. Select a Holstein Friesian genetic group only when it is known:
   `Local`, `HF50`, `HF62.5`, `HF75`, or `HF87.5`.
4. Enter measured ambient temperature in Celsius and humidity from 0 to 100.
5. Generate the recommendation.
6. Review the unified FarmLite recommendation, including the one operational
   milk estimate, DMI when available, backend THI, and advisory ration.
7. Download the PDF and confirm the optional research section.

An unselected genetic group or missing candidate weather does not block the
existing recommendation. It suppresses the research request and displays a
reason.

## Interpretation

- DMI is dry-matter intake in `kg dry matter/cow/day`.
- DMI is not total feed, fresh-feed/as-fed weight, roughage, or concentrate.
- The expected milk yield is the single farmer-facing milk estimate from the
  FarmLite milk prediction model.
- THI and category come from the backend.
- Feed composition, ration quantities, minerals, water, and frequency remain
  existing rule-engine outputs.
- `Local` has limited validation support.
- The DMI model uses a collected research dataset, requires wider multi-farm
  validation, and is AI-assisted decision support only.
- Results are not veterinary or qualified animal-nutrition advice.

## Failure handling

Candidate disabled, missing/unknown input, invalid weather, out-of-scope
animal, artifact failure, model failure, partial result, malformed response,
and backend unavailability all preserve the v1 flow. Expand technical details
only when a reviewer needs the controlled code/status.

## Disable

Stop the frontend, remove
`VITE_BANGLADESH_CANDIDATE_UI_ENABLED` from the local process environment,
and rebuild/restart Vite. The candidate selector, candidate section, and v2
request path disappear. The backend flag is independent and should also
remain off outside controlled review.

## Known validation limitation

The compiled responsive layout and local loopback server were checked, but
this environment did not provide an authenticated browser session for a
final visual pass. Perform that check at common phone and desktop widths in
Phase 7 if Phase 6 is approved.

Do not start Phase 7 from this handoff automatically.
