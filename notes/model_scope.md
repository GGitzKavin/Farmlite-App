# FarmLite AI Feed Recommendation Scope

Supported animal category:
Dairy cattle only.

Model inputs:
- Breed
- Age_Months
- Weight_Kg
- Health_Status
- Lactation_Stage
- Days_In_Milk
- Previous_Week_Avg_Yield_L
- Body_Condition_Score
- Ambient_Temperature_C
- Humidity_Percent

Candidate prediction targets:
- Milk_Yield_L
- Total_Feed_Kg
- Dry_Matter_Intake_Kg
- Concentrate_Kg
- Roughage_Kg
- Crude_Protein_Requirement
- Energy_Requirement

Validation and generated outputs:
- Mineral_Mix_Kg
- Feeding_Frequency
- Water_Advice
- Warnings
- Confidence_Level
- Explanation

The machine-learning model must predict genuine feed-related values.
Nutrition rules must validate or refine model predictions but must not be the only source of the total feed recommendation.
