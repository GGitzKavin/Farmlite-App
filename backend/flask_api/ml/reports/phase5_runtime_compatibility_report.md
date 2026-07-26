# Phase 5 runtime compatibility review

Result: PASS for the controlled repository environment; production remains
unapproved.

| Component | Runtime | Phase 4.5D serialization/review evidence |
|---|---:|---:|
| Python | 3.12.10 | 3.12.10 |
| NumPy | 2.4.4 | 2.4.4 |
| pandas | 3.0.2 | 3.0.2 |
| scikit-learn | 1.8.0 | 1.8.0 |
| joblib | 1.5.3 | 1.5.3 |

The candidate inventory records the serialization-review environment. The
current venv matches it. Both hash-verified pipelines deserialized, passed
pipeline/category checks, accepted an exact two-column pandas DataFrame, and
produced finite controlled predictions.

`requirements.txt` already contains pandas, scikit-learn, and joblib; NumPy
is a scikit-learn/pandas runtime dependency. No package install, upgrade, or
version change was necessary or performed.

The requirements file does not pin these packages. That is acceptable for
this existing controlled venv but is a reproducibility risk for a future
deployment. Pinning and a clean-environment compatibility check remain
required before any production proposal. Candidate status and all production,
commercial, and veterinary approval flags remain false.
