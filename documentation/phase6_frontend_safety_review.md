# Phase 6 frontend safety review

Date: 2026-07-26
Result: PASS WITH OPERATIONAL LIMITATIONS

## Safety controls

| Control | Result | Evidence |
|---|---|---|
| Candidate UI disabled by default | PASS | Strict public flag parser and focused tests 1-4, 38 |
| Backend dependency explicit | PASS | Frontend/root README and UI copy |
| Genetic group deliberate | PASS | Empty default, exact enum selector, tests 6-11 |
| Breed inference absent | PASS | Selector reset and request-builder tests |
| Candidate weather has no silent UI default | PASS | Conditional initial state and test 43 |
| THI backend-owned | PASS | No formula/category logic; tests 12, 15, 42 |
| Humidity 0-100 | PASS | Request builder and tests 13-14 |
| Stale response protection | PASS | Abort controller, sequence id, test 44 |
| Candidate failure isolated from v1 | PASS | Separate state and test 27 |
| Null not rendered as zero | PASS | Formatter and PDF tests 21, 47 |
| DMI material basis explicit | PASS | UI/PDF unit and catalogue warning |
| ML and rules separated | PASS | Separate components and source labels |
| Technical failures controlled | PASS | Defensive response validation and expandable status |
| Personal data logging avoided | PASS | Candidate client contains no payload logging |

## Failure behavior

- Missing or unknown group: no fabricated group; v2 is suppressed in normal
  UI use or the backend fallback is shown if such a response is received.
- Missing/invalid weather: v2 is suppressed; the v1 request remains
  independent.
- Dry/out-of-scope animal: candidate values stay null and scope is shown.
- Local: values remain candidate outputs with `LIMITED_SUPPORT` and the
  approved Local warning.
- Artifact unavailable/hash mismatch/model error: no unrelated model is
  substituted.
- Partial response: available and unavailable targets remain separate.
- Network/500/malformed response: a farmer-readable error preserves the
  controlled technical code without a stack trace.

## Protected-system verification

The following SHA-256 values match the Phase 5 evidence:

| Protected item | SHA-256 |
|---|---|
| Bangladesh DMI candidate | `312DDBAADA9A92A8B52E4ED95B254ACE0FD3EBEE1C6DD0B12BB003562EDD035B` |
| Bangladesh milk candidate | `AA650EA16D4E89BB6A660778854138BEECCCCBEA9B3C589E2E549EF823D5F56E` |
| DMI metadata | `86077E3529CEC215F2C6C827E81881FD73C4B1DE7551C451084369C1061041EE` |
| Milk metadata | `FCE8EA9956996A010D6AD1665E482786BDCBD497359FA018825106119FC0E46B` |
| Retained milk model | `B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA` |
| Phase 4 candidate | `5FDA66E3D9879FD6CF49D83B3235781545E5784781509BCC340FBFE03BBA286E` |
| Phase 4 metadata | `D1D90A9D2BD817B8F91F81665B92F371806F8F7DF1CC98ACE1C8B50768DD4069` |
| Feed planner | `27C17A8DBDF8111FC961DD4DF06CB51201C7C480600494AA52D871C777B72F2A` |
| Nutrition rules | `3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C` |

All raw and processed external dataset hashes also match their pre-Phase 6
snapshot. No training or promotion command was run.

## Quality results and limitations

- Focused frontend tests: 49/49 pass.
- Default and candidate-enabled TypeScript/Vite builds: pass.
- Phase 6-scoped ESLint: pass.
- Full frontend ESLint: seven existing repository errors remain in
  `ErrorBoundary`, `FeedRecommendation`, `HealthTracking`,
  `LivestockTable`, `Notifications`, and `Profile`. Phase 6 did not broaden
  scope to rewrite unrelated pages; no error originates in a new Phase 6
  module.
- Backend: 307/307 pass after historical frontend-freeze snapshots were
  advanced to the authorized Phase 6 source hashes.
- Local Vite served only on `127.0.0.1` and returned HTTP 200.
- Responsive behavior was checked from the compiled layout and source
  breakpoints. A final authenticated visual pass on physical/mobile browser
  sizes remains appropriate in Phase 7.

These operational limitations do not change the research-only, disabled
default or the ML/rule safety boundary.
