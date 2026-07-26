# Phase 6.1 approval gate

Date: 2026-07-26

| Requirement | Status | Evidence | Remaining action |
|---|---|---|---|
| One farmer-facing milk prediction | PASS | UI/PDF ownership tests 1-4 and 19 | Preserve in Phase 7 |
| Candidate milk remains internal | PASS | No farmer component/PDF binding; backend response unchanged | Controlled evaluation only |
| Unified recommendation panel | PASS | Separate research panel removed; four-card grid implemented | Authenticated visual review |
| DMI and ration stay separate | PASS | Shared exact explanation; no conversion logic | Preserve boundary |
| Genetic group belongs to Feeding Inputs | PASS | Selector placement and mapping tests 10-13 | Preserve explicit selection |
| Unknown group preserves v1 output and THI | PASS | Request omits group; backend returns THI and group fallback | None |
| THI remains backend-owned | PASS | Backend response binding; no frontend formula | Preserve contract |
| Farmer wording is source-neutral | PASS | UI/PDF banned-label tests 20-21 | Preserve user-facing boundary |
| Warnings are concise and separated | PASS | De-duplication plus Cow and Ration Warnings / AI Model Scope | None |
| Candidate-enabled PDF is two pages | PASS | Real jsPDF tests 26-28 | Visual renderer review |
| Feature-disabled flow remains v1 | PASS | No v2 call; legacy PDF branch; default build | None |
| Failure preserves milk and ration | PASS | Independent v1 state; abort/stale guards; test 16 | None |
| Frontend tests | PASS | Phase 6: 25/25; Phase 6.1: 32/32 | Maintain in CI |
| Backend tests | PASS | 307/307; compileall PASS | Maintain in CI |
| Builds and typecheck | PASS | Enabled and default-disabled production builds | Large-chunk warning is non-blocking |
| Phase 6.1-scoped ESLint | PASS | Focused command completed with zero findings | None |
| Full repository ESLint | LIMITATION | Seven inherited findings across six files | Resolve as separate repository debt |
| Model and rule integrity | PASS | Nine protected hashes match the approved baselines | Do not retrain or modify |
| Git hygiene | PASS | `git diff --check` has no whitespace errors; staged-file count is 0; no prohibited git mutation command used | None |

## Decision

`READY_FOR_PHASE_7_WITH_LIMITATIONS`

The limitations are the unavailable authenticated mobile/desktop visual pass,
the unavailable visual PDF renderer, and seven inherited repository-wide
ESLint findings. These do not alter the one-milk product decision, model/rule
ownership, feature-flag safety, or passing automated regression evidence.

This gate does not start Phase 7, enable either feature flag, approve
deployment, or approve production, commercial, or veterinary use.
