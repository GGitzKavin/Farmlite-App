# Phase 5 backend security and failure review

## Result

The backend prototype is suitable for controlled review behind its
disabled-by-default flag. It is not approved for public production.

| Area | Control | Result / residual risk |
|---|---|---|
| Path traversal | Resolve paths and require containment in the repository candidate root | PASS; outside-root simulation is rejected |
| Artifact configuration | Runtime paths come only from reviewed repository inventory | PASS; metadata locator text is ignored |
| joblib/pickle | Verify file and metadata hashes before deserialization | Controlled risk; joblib can execute code, so only reviewed repository artifacts may ever be allowed |
| Integrity order | Existence, artifact hash, metadata hash/contract, then `joblib.load` | PASS; mismatch test proves no deserialize call |
| Metadata | Candidate status, false approval flags, target, feature order, dataset identity, repeated measures, reload evidence | PASS; unit is bound by reviewed inventory/model contract because immutable metadata has no separate unit field |
| Unexpected errors | Route returns a generic controlled 500 | PASS; exception detail and payload are not returned |
| Request size | 16 KiB body cap and 256-character text cap | PASS |
| JSON types | Object-only JSON, allow-list fields, finite numerics, range checks | PASS |
| Weather | No silent defaults; humidity 0-100 inclusive; no invented temperature study range | PASS with documented study-range uncertainty |
| Concurrency | Reentrant lock protects verify/load/cache; only successes cached | PASS for in-process Flask runtime |
| Partial availability | Tasks load and validate independently | PASS; a valid peer output survives |
| Logging | State/category/reason/task only; no full payload, training rows, binary, or identifiers | PASS |
| Nutrition isolation | No nutrition import or invocation in v2 | PASS |

## Residual limitations

- Hashes are rooted in repository-controlled JSON, not an external signature
  service. Repository change control remains part of the trust boundary.
- A hash-verified joblib remains executable serialization. Never accept an
  uploaded artifact or caller-supplied path/hash.
- The registered endpoint has no Phase 5-specific authentication, rate
  limit, or production CORS policy. The feature flag must remain false
  outside explicitly controlled review until those deployment controls are
  decided.
- In-memory cache state is process-local. Multi-worker deployment would
  verify once per worker.
- Package requirements are unpinned even though the current venv exactly
  matches the recorded review environment.
- Study-observed output ranges are integration safety guards, not universal
  biological bounds. Values outside are rejected, never clipped.
- The source workbooks lack numeric weather values, and the models lack
  independent external-farm validation.

No finding permits production, commercial, or veterinary readiness claims.
