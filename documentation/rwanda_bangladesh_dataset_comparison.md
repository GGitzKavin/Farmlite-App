# Rwanda–Bangladesh Dataset Comparison

| Dimension | Bangladesh HF cross | Rwanda dairy |
|---|---|---|
| Dataset type | Repeated experimental/observational records across THI categories | Cross-sectional farm/cow source |
| Cow count | 50 identifiable cows | 96 source-reported cows; workbook cow IDs absent |
| Observation count | 750 rows in each workbook | 96 cow-workbook rows |
| Repeated measures | 15/cow | Not verifiable; methodology is cross-sectional |
| Cow identifiers | Present; physiology coverage mismatch | Absent in audited workbook |
| DMI | kg/cow/day target verified; exact protocol unclear | Blocked by unclear capacity/intake semantics and negative leftovers |
| Milk yield | measured L/cow/day | verified hand-milked L/day |
| Environment | Categorical THI; no numeric T/RH/THI | Current FarmLite temperature/humidity absent |
| Nutrient variables | Milk composition and blood outcomes; no ration nutrients | Calculated CP/ME candidates and fodder text |
| Feed labels | No expert/optimized recommendation labels | No expert recommendation labels |
| Data quality | Complete composite keys internally; 90% physiology cross-match; AST/ALT unit conflict | DMI semantic conflicts, age-column contamination, unit/formula issues |
| ML readiness | DMI/milk design with limitations and cow grouping | Milk/water with limitations; DMI blocked |
| Rule readiness | Supporting heat/composition research only | CP/ME rule support with limitations |
| External validation | Candidate only after feature/population harmonization | DMI not currently valid as Bangladesh external validation |

## Recommendation

Use Bangladesh for future DMI and milk model design only after a new approval and protocol clarification. Keep Rwanda as separate milk/water and rule-support evidence; do not use its unclear DMI as external validation. Do not concatenate the sources. Current harmonization is insufficient because identifiers, design, populations, feature availability, and DMI semantics differ.
