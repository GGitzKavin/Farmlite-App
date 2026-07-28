# Phase 7 Release Approval Gate

Date: 2026-07-26

## Final decision

`SYSTEM_READY_WITH_DOCUMENTED_LIMITATIONS`

FarmLite is ready for final academic submission as an implemented,
integrated decision-support system. The automated repository gate passes.
Limitations that require an authorized external environment or post-submission
hardening are explicitly recorded and do not justify changing frozen
Firebase/model/rule behavior during Phase 7.

## Approval matrix

| Gate | Result | Evidence |
|---|---|---|
| Repository baseline inventoried | Pass | `phase7_system_inventory.json` |
| Phase 6–6.3 files present | Pass | Inventory and 105 frontend tests |
| Authentication flow present/protected | Pass with limitation | Source review; no live Firebase login |
| Dashboard acceptance | Pass | Phase 6.2 tests |
| Individual livestock acceptance | Pass | Phase 6.2/6.3 tests and source review |
| Batch acceptance | Pass | Phase 6.3 tests |
| Animal profile acceptance | Pass | Phase 6.2 tests |
| Health/vaccination/notifications | Pass with limitation | Source/tests; no live writes |
| Profile/Farm Type | Pass | Phase 6.2 tests |
| Supported recommendation | Pass | v1/v2 controlled execution |
| Unknown genetic group | Pass | Null DMI, preserved THI/v1 flow |
| Invalid weather | Pass | Controlled fallback; no frontend THI |
| Candidate unavailable | Pass | Artifact/fallback and orchestration tests |
| Flags disabled | Pass | Backend/frontend disabled-mode tests |
| Unsupported status | Pass | Fail-closed eligibility tests |
| Local genetic group | Pass with limitation | `LIMITED_SUPPORT` |
| Output ownership | Pass | UI/PDF/source tests |
| Farmer PDF | Pass with limitation | Content/page/buffer tests; no visual renderer |
| Responsive behavior | Pass with limitation | Source contracts; no browser viewport run |
| Accessibility | Pass with limitation | Focused contracts; no full axe/screen reader |
| Security/privacy | Pass with documented deployment findings | Final security review |
| Firebase freeze | Pass | No Firebase mutation/deployment |
| Performance/reliability | Pass with warning | Local metrics; large chunk warning |
| Model/artifact integrity | Pass | Frozen hashes and 308 backend tests |
| Nutrition-rule integrity | Pass | Frozen hash |
| API v1/v2 contracts | Pass | Backend tests |
| Frontend typecheck | Pass | `tsc -b` |
| Feature-enabled build | Pass | Vite build |
| Feature-disabled build | Pass | Vite build left in `dist` |
| Backend compileall | Pass | Python compileall |
| Repository ESLint | Documented limitation | Six inherited findings |
| Git diff syntax | Pass | `git diff --check` (line-ending notices only) |
| Staged files | Pass: zero | Git check |

## Integrity values

- retained milk model:
  `B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA`
- collected-data DMI artifact:
  `312DDBAADA9A92A8B52E4ED95B254ACE0FD3EBEE1C6DD0B12BB003562EDD035B`
- DMI metadata:
  `86077E3529CEC215F2C6C827E81881FD73C4B1DE7551C451084369C1061041EE`
- internal candidate milk artifact:
  `AA650EA16D4E89BB6A660778854138BEECCCCBEA9B3C589E2E549EF823D5F56E`
- internal candidate milk metadata:
  `FCE8EA9956996A010D6AD1665E482786BDCBD497359FA018825106119FC0E46B`
- nutrition rules:
  `3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C`

## Phase 7 corrective changes

- Prevented raw v1 exception text from reaching clients.
- Added regression coverage for the generic v1 500 response.
- Made Flask debug mode explicit opt-in.
- Removed Firebase user-object console logging.
- Advanced protected-source test snapshots to the reviewed Phase 7 state.

No model, coefficient, metadata, feature order, THI formula/boundary,
nutrition formula/rule, API success contract or Firebase configuration was
changed.

## Documented limitations

1. No source-controlled copy of the deployed temporary Firestore rules.
2. No live Firebase mutation/login test during the frozen review.
3. No browser viewport, axe or screen-reader automation.
4. No visual PDF renderer.
5. Six inherited repository ESLint findings.
6. Vite main-chunk warning.
7. Broad development CORS and no Flask Firebase-token enforcement.
8. External npm advisory lookup not authorized.
9. Models remain within limited declared validation scope.

## Exact supported release scope

FarmLite supports authenticated management of farmer-owned livestock, batch,
health, vaccination and feed-inventory records plus dashboard, notification,
profile and PDF workflows. Decision support covers supported lactating cows:
one FarmLite milk estimate, feature-gated collected-data DMI, backend THI and
an independently rule-generated advisory ration. Missing, invalid,
unsupported or unavailable candidate conditions fail safely. This scope does
not extend to unrestricted clinical, commercial, universal or multi-farm
claims.

## Next action

Perform the short witnessed manual check described in
`final_limitations_and_future_validation.md`, capture the exact deployed
Firestore rule version and visually inspect the PDF. If those checks show no
new blocker, submit the repository and Phase 7 evidence without staging or
committing through Codex.
