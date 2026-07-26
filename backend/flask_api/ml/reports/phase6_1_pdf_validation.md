# Phase 6.1 PDF validation report

Date: 2026-07-26

## Result

PASS WITH VISUAL-RENDERER LIMITATION

The candidate-enabled generator creates exactly two pages under the controlled
acceptance fixture. The feature-disabled branch keeps the original v1 report.

## Required content

| Check | Result |
|---|---|
| Approved decision-support title | PASS |
| Selected-cow summary and four primary result cards | PASS |
| One expected milk value only | PASS |
| Candidate milk absent | PASS |
| DMI unit is `kg DM/cow/day` | PASS |
| THI sourced from backend response | PASS |
| Ration sourced from nutrition rule engine | PASS |
| DMI/ration clarification included | PASS |
| Cow/ration warnings and AI scope separated | PASS |
| Four exact value-source lines | PASS |
| Mendeley DOI note included | PASS |
| Disclaimer included | PASS |
| Page numbers and consistent footer | PASS |
| Exactly two pages with DMI | PASS |
| Exactly two usable pages without DMI | PASS |

## Programmatic PDF checks

- Controlled PDF with DMI: two pages and real jsPDF ArrayBuffer greater than
  3,000 bytes.
- Controlled PDF without DMI: two pages and real jsPDF ArrayBuffer greater
  than 2,500 bytes.
- Null data shape: no rendered `null`, `undefined`, or `NaN`.
- Result data shape: exactly one milk row and one DMI row.
- Source and narrative scan: no farmer-facing candidate milk or
  geography-based dataset/model heading.

The page-one layout uses fixed result-card geometry and compact summary grids;
page two uses wrapped text with controlled section order. No third page is
created by the acceptance fixtures.

A local visual PDF renderer was unavailable. Pixel-level typography,
printer-specific line wrapping, and logo rendering remain a Phase 7
system-validation task.
