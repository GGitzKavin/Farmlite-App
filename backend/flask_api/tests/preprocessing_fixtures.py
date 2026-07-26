"""Small deterministic fixtures for preprocessing tests."""

from __future__ import annotations

from itertools import cycle, islice

import pandas as pd


FEED_TYPES = [
    "Concentrates",
    "Crop_Residues",
    "Dry_Fodder",
    "Green_Fodder",
    "Hay",
    "Mixed_Feed",
    "Pasture_Grass",
    "Silage",
]
BREEDS = ["Holstein-Friesian", "Jersey", "Ayrshire", "Brown_Swiss"]
LACTATION_STAGES = ["Early", "Mid", "Late"]
BASE_FEATURES = [
    "breed",
    "age_months",
    "weight_kg",
    "lactation_stage",
    "days_in_milk",
    "previous_week_avg_yield_l",
    "body_condition_score",
    "ambient_temperature_c",
    "humidity_percent",
]


def make_fixture(rows: int = 80) -> pd.DataFrame:
    """Return a canonical fixture with every audited feed category."""

    feed_types = list(islice(cycle(FEED_TYPES), rows))
    breeds = list(islice(cycle(BREEDS), rows))
    lactation = list(islice(cycle(LACTATION_STAGES), rows))
    return pd.DataFrame(
        {
            "source_row_number": range(1, rows + 1),
            "cattle_id": [f"TEST_{index:04d}" for index in range(rows)],
            "observation_date": ["2024-01-01"] * rows,
            "breed": breeds,
            "age_months": [24 + index % 100 for index in range(rows)],
            "weight_kg": [300.0 + index for index in range(rows)],
            "lactation_stage": lactation,
            "days_in_milk": [1 + index % 364 for index in range(rows)],
            "previous_week_avg_yield_l": [
                float(index % 30) for index in range(rows)
            ],
            "body_condition_score": [
                2.0 + (index % 7) * 0.5 for index in range(rows)
            ],
            "ambient_temperature_c": [
                20.0 + index % 15 for index in range(rows)
            ],
            "humidity_percent": [40.0 + index % 50 for index in range(rows)],
            "feed_type": feed_types,
            "feed_quantity_kg": [
                5.0 + (index % 20) * 0.5 for index in range(rows)
            ],
            "milk_yield_l": [
                2.0 + (index % 30) * 0.75 for index in range(rows)
            ],
            "health_status": ["Healthy"] * rows,
            "unapproved_extra": ["preserve-but-exclude"] * rows,
        }
    )


__all__ = ["BASE_FEATURES", "BREEDS", "FEED_TYPES", "make_fixture"]
