# FarmLite Phase 5 Integration Approval Gate

| Check | Status | Evidence | Required action |
|---|---|---|---|
| Feed classifier beats baseline | `FAILED` | DOES_NOT_BEAT_BASELINE | Review only if candidate artifact exists. |
| Feed classifier predicts all relevant classes | `PASSED` | 8 predicted classes | Replace/redesign data or classifier if collapsed. |
| Feed quantity beats baseline | `FAILED` | DOES_NOT_BEAT_BASELINE | Review only the locked eligible design. |
| Design A/B comparison completed | `PASSED` | Report created | None. |
| Milk yield beats baseline | `PASSED` | BEATS_BASELINE | Interpret only as synthetic prototype performance. |
| Milk-yield ablation completed | `PASSED` | Validation and test compared | Retain transparency warning. |
| Validation/test stability acceptable | `PASSED_WITH_LIMITATIONS` | DOES_NOT_BEAT_BASELINE; DOES_NOT_BEAT_BASELINE; BEATS_BASELINE | Do not tune against test. |
| Candidate artifacts reload successfully | `PASSED` | 1 eligible artifact(s) | Only integrate separately approved candidates. |
| Existing production model preserved | `PASSED` | SHA-256 unchanged: True | Stop immediately if false. |
| Synthetic limitation documented | `PASSED` | Reports, metadata, and model cards | Keep warning visible in any later integration. |
| Dairy-scope limitation documented | `PASSED_WITH_LIMITATIONS` | Dataset is not verified dairy-only | Acquire a scoped dataset before real-world claims. |
| Integration not yet performed | `PASSED` | Phase 4 only | Await explicit Phase 5 approval. |

## Final Recommendation: `READY_FOR_PARTIAL_INTEGRATION_REVIEW`

Phase 5 has not begun. No Flask or React integration was performed.
