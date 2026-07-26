# Rwanda Dairy Dataset Clarification Request

## Dataset identity

1. Does each row in the cow workbook represent one unique cow?
2. Does each row represent one unique farm?
3. Can cow and farm identifiers be provided?
4. Is `LabN°` a cow ID, farm ID, composite-feed sample ID, or another ID?
5. Why do six `LabN°` duplicate occurrences appear across three numbers?
6. What do the seven fodder-only sample keys represent?

## Age

7. Why do 30 entries in the age column contain breed names?
8. Is there a corrected age column or corrected workbook?
9. Can the numeric ages for these records be recovered?

## Feed and DMI

10. What does `DM served` represent exactly?
11. What does `leftover` represent exactly?
12. Why are 28 leftover values negative?
13. Does a negative leftover mean shortage, extra feed supplied, or an error?
14. What is the exact DMI calculation formula?
15. What does `DMIcapacity` represent?
16. Is `DMIcapacity` measured intake, predicted intake capacity, or requirement?
17. What are the units and period for every DMI field?
18. Which DMI field should be used as actual consumed dry-matter intake?

## Water

19. Does `waterday` mean water offered, provided, available, reported, or consumed?
20. Was remaining or refused water measured?
21. Is `waterday` per cow per day?
22. How was water requirement calculated, including equation version?
23. How was water gap calculated, and can inconsistent rows be corrected?

## Milk

24. Does `hand-milked yield` include all daily milkings?
25. Is its unit litres per cow per day?
26. How was calf milk consumption estimated?
27. Should `Total milk performance` be treated as observed or calculated?

## Protein

28. What are the units of CP intake and requirement fields?
29. What is the exact CP-gap formula?
30. Why does the metadata definition conflict with stored values?
31. Which CP equation or guideline and version was used?

## Energy

32. What are the units of ME composition, intake and requirements?
33. What is the exact `MEfeeds` equation and CP basis?
34. Which gas-volume or laboratory input was used?
35. Can the missing G24 gas-volume data be supplied?
36. Which energy-requirement guideline and version was used?

## NDF

37. What is the exact NDF unit?
38. Is it percentage of dry matter, g/kg DM, or another basis?

## Feeding plan

39. Does the bucket plan describe farmer practice or a researcher recommendation?
40. Was the ration nutritionally optimized?
41. Were ingredient quantities or inclusion percentages recorded?
42. Is there an additional workbook containing ration quantities?

## Corrected data

43. Is a corrected or newer dataset version available?
44. Can a data dictionary with formulas, units, row identifiers and collection periods be provided?
