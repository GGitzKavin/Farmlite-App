# FarmLite Final Limitations and Future Validation

Date: 2026-07-26

## Declared release scope

The supported release scope is an authenticated, single-farmer-view livestock
management application with individual and batch records, health and
vaccination tracking, notifications, feed inventory and controlled
decision-support for supported lactating cows.

Within the recommendation flow:

- one expected milk-yield result is farmer-facing;
- DMI is available only when the collected-data path is enabled and eligible;
- THI is backend-calculated from valid weather inputs;
- ration composition is produced only by the FarmLite nutrition rule engine;
- unsupported or incomplete conditions fail safely.

The release is appropriate for academic submission and controlled evaluation.
It is not unrestricted veterinary, nutritional, commercial, regulatory,
universal or multi-farm validation.

## Model limitations

- The retained FarmLite milk model is associated with
  publisher-declared synthetic source data.
- Synthetic evaluation performance does not establish real-farm accuracy.
- The collected-data DMI model is candidate-only, feature-gated and trained
  within a limited source-study population.
- `Local` is limited support.
- Unknown genetic group cannot produce DMI.
- Breed is not a safe proxy for genetic group.
- The internal candidate milk result is not approved for farmer-facing use.
- Study-observed sanity bounds are integration guards, not universal
  biological limits.

## Recommendation limitations

- DMI is dry matter, not total or fresh feed.
- DMI is not converted into ration components.
- Ration values are advisory rules and do not account for every available
  feed analysis, animal disease, pregnancy, economics or veterinary finding.
- Weather is manually submitted; FarmLite does not verify sensor calibration.
- Invalid weather leaves THI unavailable.
- Results must be reviewed by qualified professionals for high-stakes use.

## Firebase and privacy limitations

- The exact deployed temporary Firestore rule text is absent from the
  repository and was not verified.
- Some legacy screens perform broad collection reads followed by client-side
  ownership filtering; server rules must enforce isolation.
- The Flask APIs do not validate Firebase ID tokens.
- Privacy retention, data export/deletion and incident-response procedures are
  deployment/organizational responsibilities.

## Validation limitations

- No live Firebase account or stored record was changed during Phase 7.
- Authentication/CRUD conclusions use source inspection and existing tests,
  not a destructive live end-to-end run.
- No browser automation was available for screenshot validation at 320, 375,
  768, 1024 and desktop widths.
- No visual PDF renderer was installed; PDF buffers, page counts and content
  contracts passed, while pixel-level review remains manual.
- No complete axe/screen-reader audit was available.
- The external npm advisory service was unavailable without authorization.
- Performance measurements use an in-process Flask client and local Vite
  preview, not production network traffic.

## Engineering limitations

- Repository-wide ESLint has six inherited errors.
- The minified main frontend chunk is approximately 1.57 MB and triggers
  Vite’s large-chunk warning.
- CORS is unrestricted in the Flask development configuration.
- The protected settings route is an existing placeholder and is not part of
  the supported feature scope.

## Required future validation

Before public deployment:

1. Export, source-control and independently review the exact Firestore rules
   without weakening them.
2. Execute authenticated cross-user authorization tests in a dedicated
   non-production Firebase project.
3. Add deployment-level Flask authentication, explicit CORS origins, rate
   limits and log-retention controls.
4. Run an authorized dependency advisory/SBOM scan.
5. Complete browser testing at the five required widths and across supported
   browsers.
6. Complete axe, keyboard-only, screen-reader and contrast testing; correct
   legacy label/status gaps.
7. Visually inspect the five PDF acceptance fixtures and printer output.
8. Resolve existing lint debt and plan route-level/code-split bundles without
   altering model behavior.

Before making stronger model claims:

1. Validate prospectively on independent farms and seasons.
2. Pre-register target definitions, eligibility and evaluation metrics.
3. Record calibrated sensor, milk and feed-intake measurement protocols.
4. Evaluate group-level error, drift, missingness and out-of-distribution
   behavior.
5. Obtain veterinary and animal-nutrition review.
6. Keep DMI and ration ownership separate.
7. Do not replace or average the farmer-facing milk result without a new,
   explicitly approved release process.

## Immediate next action

Run a short, witnessed submission smoke test in an authorized Firebase test
account: login, view existing records, create and remove one disposable test
record if permitted, execute the seven recommendation scenarios, inspect the
generated PDF visually, and record the deployed Firestore rule version. Do
not change rules or production data during that check.
