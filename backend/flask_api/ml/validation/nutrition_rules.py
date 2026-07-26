"""Validation boundary for future ML-generated feed values.

The active FarmLite recommendation remains unchanged in
``ml.inference.feed_planner``. These checks establish where genuine feed-model
outputs will be validated before nutrition refinements are introduced.
"""

from collections.abc import Mapping
from typing import Any


REQUIRED_FEED_PREDICTION_FIELDS = (
    "total_feed_kg",
    "dry_matter_intake_kg",
    "concentrate_kg",
    "roughage_kg",
    "crude_protein_requirement",
    "energy_requirement",
)


def find_missing_prediction_fields(
    prediction: Mapping[str, Any],
) -> list[str]:
    """List required genuine feed-output fields absent from a prediction."""

    return [
        field
        for field in REQUIRED_FEED_PREDICTION_FIELDS
        if field not in prediction or prediction[field] is None
    ]


__all__ = [
    "REQUIRED_FEED_PREDICTION_FIELDS",
    "find_missing_prediction_fields",
]
