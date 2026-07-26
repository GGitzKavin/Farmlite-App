# Bangladesh Option B Support Report

## Final Decision: `DMI_AND_MILK_SUPPORT`

### 1. Is DMI clearly defined?

Yes: dry matter intake per cow in kg/day.

### 2. Is DMI measured per cow per day?

Yes; exact offered/refusal protocol remains `UNCLEAR`.

### 3. Is milk yield clearly defined?

Yes: daily milk yield per cow in litres.

### 4. Are cow identifiers present?

Yes, `Animal ID` in all workbooks.

### 5. Are repeated observations linkable?

Yes within each workbook; cross-workbook physiology coverage is only 90%.

### 6. Can grouped validation be performed?

Yes. Group only by cow; never split repeated rows randomly.

### 7. Are temperature and humidity available?

No numeric temperature or humidity fields are supplied.

### 8. Is THI measured or calculated?

Workbooks store assigned THI categories. The article documents calculation from T and RH, but numeric inputs/THI are absent.

### 9. Can a heat-stress-aware DMI model be designed?

`READY_WITH_LIMITATIONS` using categorical THI only.

### 10. Can a heat-stress-aware milk model be designed?

`READY_WITH_LIMITATIONS` using categorical THI only.

### 11. Can the physiological workbook be joined safely?

`POSSIBLE_WITH_LIMITATIONS`: 675/750 keys and 45/50 cow IDs match.

### 12. Can the blood workbook be joined safely?

`SAFE_ONE_TO_ONE` with DMI/milk: 750/750 keys.

### 13. Are blood variables appropriate for FarmLite?

No as ordinary inference inputs; they are research/laboratory outcomes.

### 14. Does any workbook contain expert feed recommendations?

No.

### 15. Can roughage and concentrate quantities be predicted?

No targets or component quantities are present.

### 16. Which FarmLite inputs are missing?

Age, weight, lactation stage, DIM, previous-week yield, BCS, ambient temperature, and humidity.

### 17. Which new frontend inputs may be useful?

Genetic group plus measured temperature/humidity or numeric THI, after future design review.

### 18. Can Bangladesh and Rwanda be combined?

No. Keep them separate; target semantics, population, design, and feature coverage differ.

### 19. Can Bangladesh be used for training and Rwanda for validation?

Not for DMI now; Rwanda DMI is semantically blocked. Milk requires a separate harmonization/feature review first.

### 20. Does this source restore the feed-quantity part of Option B?

It restores a verified DMI target for research model design, not a complete ration/quantity recommender.

## Boundary

This decision authorizes no training or integration. It does not treat genetic group or THI group as a recommendation label and does not change the frontend or Option B runtime.
