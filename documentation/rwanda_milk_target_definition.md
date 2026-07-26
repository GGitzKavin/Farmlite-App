# Rwanda Milk Target Definition

## A. Direct Hand-Milked Yield

| Attribute | Evidence |
|---|---|
| Source field | `hand-milked yield` |
| Definition | Milk measured with graduated 1, 2 and 5 L plastic jugs after each milking session. |
| Unit/period | L/cow/day, supported by repository reporting. |
| Directly measured | `YES` |
| Includes calf estimate | `NO` |
| Includes all daily milkings | `UNCLEAR`; "after each milking session" is documented, but completeness needs confirmation. |
| Usable/missing | 96 / 0 |
| Range | 1-17 L/cow/day |
| Target status | `VERIFIED_MEASURED_MILK_L_COW_DAY` |
| Design status | `READY_WITH_LIMITATIONS` |

## B. Total Milk Performance

| Attribute | Evidence |
|---|---|
| Source field | `Total milk performance` |
| Definition | `hand-milked yield + Ass.calfmilk` |
| Unit/period | L/cow/day |
| Directly measured | `NO` |
| Includes calf estimate | `YES`; age-band allocation of 6/4/2/1/0 L. |
| Usable/missing | 96 / 0 |
| Range | 1-21 L/cow/day |
| Target status | `CALCULATED_TOTAL_MILK_L_COW_DAY` |
| Design status | `BLOCKED` unless the research objective explicitly requires estimated calf milk. |

The two fields remain separate. The preferred future target is directly
measured hand-milked yield, subject to confirmation that it covers all daily
milkings and that the 96 rows are independent.
