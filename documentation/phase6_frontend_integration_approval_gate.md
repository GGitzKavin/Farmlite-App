# Phase 6 frontend integration approval gate

Date: 2026-07-26

| Requirement | Status | Evidence | Remaining action |
|---|---|---|---|
| Frontend flag defaults disabled | PASS | Flag parser; tests 1-4, 38 | Keep disabled outside controlled review |
| Existing UI preserved when disabled | PASS | Existing v1 path retained; tests 5, 35 | Phase 7 regression check |
| Genetic group explicitly collected | PASS | Exact native selector with empty placeholder | None |
| Breed inference prohibited | PASS | Reset logic; tests 8-9 | Preserve boundary |
| API v2 called correctly | PASS | Typed client posts `/api/v2/predict` | None |
| THI remains backend-owned | PASS | No frontend formula/category logic; tests 15, 42 | None |
| DMI unit displayed correctly | PASS | `kg dry matter/cow/day`; tests 17, 32 | Preserve wording |
| Milk unit displayed correctly | PASS | `L/cow/day`; tests 18, 32 | Preserve wording |
| ML and rule outputs separated | PASS | Separate section/source labels; tests 20, 34, 48 | None |
| Fallback states handled | PASS | Controlled messages/details and scenario report | Authenticated visual review in Phase 7 |
| Candidate warnings displayed | PASS | Approved catalogue composition; tests 29-30, 40, 49 | None |
| PDF works without candidate result | PASS | Focused test 31 | Visual sample review in Phase 7 |
| PDF labels candidate result correctly | PASS | Tests 32-34, 41, 47-48 | Visual sample review in Phase 7 |
| Existing v1 flow preserved | PASS | Independent request and state; backend v1 tests | None |
| Frontend tests pass | PASS | 49/49 | Maintain in CI |
| Backend tests pass | PASS | 307/307; compileall PASS | Maintain snapshots |
| Production approval remains false | PASS | Both flags default off; model metadata/contracts unchanged | External/system validation still required |

## Additional quality note

Phase 6-scoped ESLint passes. The repository-wide lint command still reports
seven existing errors across six existing components/pages. The
authenticated mobile and visual-PDF pass is also deferred because this
environment has no authenticated browser session or PDF renderer. These are
system-validation limitations, not reasons to alter the controlled ML/rule
boundary.

## Recommendation

`READY_FOR_PHASE_7_WITH_LIMITATIONS`

This recommendation authorizes only a separately requested Phase 7 system
validation. It does not enable either flag, approve deployment, approve
production use, or approve veterinary use.
