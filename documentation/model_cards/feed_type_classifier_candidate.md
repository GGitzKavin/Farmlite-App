# FarmLite Synthetic Feed-Type Classifier Candidate

## Model Purpose

Predict one publisher-declared synthetic feed category from nine approved cattle and environment features.

## Intended Use

Undergraduate demonstration of a reproducible synthetic tabular ML workflow.

## Out-of-Scope Use

Veterinary, nutritional, commercial, farm-control, safety-critical, or real-world feeding decisions.

## Synthetic-Data Warning

FarmLite is an undergraduate prototype using publisher-declared synthetic cattle data. Predictions demonstrate an ML pipeline and are not veterinary, nutritional, commercial, or real-world feeding guidance.

## Inputs and Target

- Features: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`
- Target: `feed_type`

## Algorithm and Training

- Configuration: `feed_type_random_forest`
- Algorithm: RandomForestClassifier
- Hyperparameters: `{"max_depth": 18, "min_samples_leaf": 5, "n_estimators": 60, "n_jobs": 2, "random_state": 42}`
- Fit partition: locked 175,000-row training split only.
- Selection partition: locked 37,500-row validation split.
- Final evaluation: one-time locked 37,500-row test split.
- Random seed: 42 where supported.

## Results and Baseline Comparison

- Validation metrics: `{"accuracy": 0.12696, "balanced_accuracy": 0.12693082757259153, "confusion_matrix": [[623, 584, 700, 568, 537, 603, 558, 520], [551, 595, 684, 590, 532, 591, 580, 568], [579, 600, 669, 558, 562, 603, 625, 540], [540, 609, 682, 586, 539, 607, 563, 557], [579, 622, 705, 577, 546, 576, 568, 497], [593, 580, 677, 578, 509, 586, 604, 545], [598, 616, 682, 570, 502, 607, 594, 524], [559, 589, 697, 593, 500, 585, 577, 562]], "labels": ["Concentrates", "Crop_Residues", "Dry_Fodder", "Green_Fodder", "Hay", "Mixed_Feed", "Pasture_Grass", "Silage"], "macro_f1": 0.12688909988368033, "macro_precision": 0.12716236188078034, "macro_recall": 0.12693082757259153, "per_class": {"Concentrates": {"f1": 0.13376274825550188, "precision": 0.13479013414106447, "predicted_count": 4622, "recall": 0.1327509056040912, "support": 4693}, "Crop_Residues": {"f1": 0.12544802867383512, "precision": 0.12408759124087591, "predicted_count": 4795, "recall": 0.1268386271583884, "support": 4691}, "Dry_Fodder": {"f1": 0.13076622361219703, "precision": 0.12172489082969433, "predicted_count": 5496, "recall": 0.14125844594594594, "support": 4736}, "Green_Fodder": {"f1": 0.12598086638718692, "precision": 0.12683982683982684, "predicted_count": 4620, "recall": 0.12513346145633142, "support": 4683}, "Hay": {"f1": 0.12273800157356413, "precision": 0.12916962384669978, "predicted_count": 4227, "recall": 0.11691648822269807, "support": 4670}, "Mixed_Feed": {"f1": 0.12428419936373276, "precision": 0.12316099201345103, "predicted_count": 4758, "recall": 0.1254280821917808, "support": 4672}, "Pasture_Grass": {"f1": 0.12689596240119633, "precision": 0.12722210323409724, "predicted_count": 4669, "recall": 0.12657148945237587, "support": 4693}, "Silage": {"f1": 0.12523676880222842, "precision": 0.13030373290053326, "predicted_count": 4313, "recall": 0.12054912054912055, "support": 4662}}, "predicted_class_count": 8, "predicted_class_distribution": {"Concentrates": 4622, "Crop_Residues": 4795, "Dry_Fodder": 5496, "Green_Fodder": 4620, "Hay": 4227, "Mixed_Feed": 4758, "Pasture_Grass": 4669, "Silage": 4313}, "weighted_f1": 0.12689923538323464}`
- Final test metrics: `{"accuracy": 0.12290666666666666, "balanced_accuracy": 0.1228683796924512, "confusion_matrix": [[557, 637, 665, 585, 529, 587, 619, 513], [592, 592, 655, 600, 544, 584, 617, 507], [594, 655, 686, 557, 512, 583, 598, 550], [565, 642, 714, 566, 540, 571, 571, 514], [588, 547, 707, 562, 529, 604, 590, 543], [580, 589, 715, 635, 518, 569, 557, 510], [587, 601, 721, 565, 513, 606, 575, 526], [599, 604, 675, 590, 522, 568, 569, 535]], "labels": ["Concentrates", "Crop_Residues", "Dry_Fodder", "Green_Fodder", "Hay", "Mixed_Feed", "Pasture_Grass", "Silage"], "macro_f1": 0.12273523688125287, "macro_precision": 0.12298265635796264, "macro_recall": 0.1228683796924512, "per_class": {"Concentrates": {"f1": 0.11909343596322429, "precision": 0.11947661947661947, "predicted_count": 4662, "recall": 0.11871270247229326, "support": 4692}, "Crop_Residues": {"f1": 0.12387528771709563, "precision": 0.12163550441750565, "predicted_count": 4867, "recall": 0.12619910466851417, "support": 4691}, "Dry_Fodder": {"f1": 0.13355397644310327, "precision": 0.12387143373058866, "predicted_count": 5538, "recall": 0.14487856388595566, "support": 4735}, "Green_Fodder": {"f1": 0.12116022690784545, "precision": 0.12145922746781115, "predicted_count": 4660, "recall": 0.12086269485372625, "support": 4683}, "Hay": {"f1": 0.11918440914723442, "precision": 0.12574280960304254, "predicted_count": 4207, "recall": 0.11327623126338329, "support": 4670}, "Mixed_Feed": {"f1": 0.12177635098983414, "precision": 0.12178938356164383, "predicted_count": 4672, "recall": 0.12176332120693345, "support": 4673}, "Pasture_Grass": {"f1": 0.12247071352502663, "precision": 0.12244463373083475, "predicted_count": 4696, "recall": 0.12249680443118875, "support": 4694}, "Silage": {"f1": 0.12076749435665914, "precision": 0.12744163887565507, "predicted_count": 4198, "recall": 0.11475761475761476, "support": 4662}}, "predicted_class_count": 8, "predicted_class_distribution": {"Concentrates": 4662, "Crop_Residues": 4867, "Dry_Fodder": 5538, "Green_Fodder": 4660, "Hay": 4207, "Mixed_Feed": 4672, "Pasture_Grass": 4696, "Silage": 4198}, "weighted_f1": 0.12275211904421808}`
- Final baseline metrics: `{"accuracy": 0.12616, "balanced_accuracy": 0.12616008167769696, "confusion_matrix": [[598, 547, 600, 567, 567, 640, 591, 582], [598, 558, 575, 580, 586, 585, 604, 605], [586, 599, 614, 583, 598, 592, 567, 596], [527, 590, 620, 579, 611, 591, 591, 574], [587, 598, 589, 614, 557, 597, 590, 538], [570, 599, 598, 608, 550, 630, 555, 563], [566, 581, 617, 662, 535, 572, 581, 580], [650, 588, 537, 569, 570, 547, 587, 614]], "labels": ["Concentrates", "Crop_Residues", "Dry_Fodder", "Green_Fodder", "Hay", "Mixed_Feed", "Pasture_Grass", "Silage"], "macro_f1": 0.12614545950185524, "macro_precision": 0.12613945949430483, "macro_recall": 0.12616008167769696, "per_class": {"Concentrates": {"f1": 0.12758694260721143, "precision": 0.1277231952157198, "predicted_count": 4682, "recall": 0.12745098039215685, "support": 4692}, "Crop_Residues": {"f1": 0.11934552454282965, "precision": 0.11974248927038626, "predicted_count": 4660, "recall": 0.11895118311660627, "support": 4691}, "Dry_Fodder": {"f1": 0.12946758039008963, "precision": 0.12926315789473683, "predicted_count": 4750, "recall": 0.12967265047518478, "support": 4735}, "Green_Fodder": {"f1": 0.12260455267337216, "precision": 0.12158756824863502, "predicted_count": 4762, "recall": 0.1236386931454196, "support": 4683}, "Hay": {"f1": 0.12051060147122458, "precision": 0.12177525142107565, "predicted_count": 4574, "recall": 0.11927194860813704, "support": 4670}, "Mixed_Feed": {"f1": 0.13365864007637637, "precision": 0.13251998317206562, "predicted_count": 4754, "recall": 0.13481703402525144, "support": 4673}, "Pasture_Grass": {"f1": 0.12414529914529915, "precision": 0.12451778825546507, "predicted_count": 4666, "recall": 0.1237750319556881, "support": 4694}, "Silage": {"f1": 0.1318445351084389, "precision": 0.13198624247635427, "predicted_count": 4652, "recall": 0.1317031317031317, "support": 4662}}, "predicted_class_count": 8, "predicted_class_distribution": {"Concentrates": 4682, "Crop_Residues": 4660, "Dry_Fodder": 4750, "Green_Fodder": 4762, "Hay": 4574, "Mixed_Feed": 4754, "Pasture_Grass": 4666, "Silage": 4652}, "weighted_f1": 0.12614513318589407}`
- Status: `DOES_NOT_BEAT_BASELINE`

## Known and Ethical Limitations

- Synthetic generation formulas and dependency structure are undocumented.
- Feed and yield labels are not expert-validated recommendations or measurements.
- Feature importance is association, not causation or biological evidence.
- Dataset licensing remains unresolved.

## Dairy-Scope Limitation

The interface is scoped to dairy cattle, while the synthetic dataset contains cattle whose production purpose is not fully documented.

## Deployment Status

NO ELIGIBLE CANDIDATE - research-only result.

## Recommended Next Action

Use another expert-labelled dataset or redesign the target if no candidate clears the baseline; otherwise request a separate Phase 5 integration review.
