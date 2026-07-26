"""Typed API payload documentation.

The runtime request and response shapes remain defined by the existing API
contract. This module is the home for formal validation schemas when FarmLite
adopts a schema library in a later change.
"""

from typing import Any, TypedDict


class FeedRecommendationRequest(TypedDict, total=False):
    animalId: str
    animalName: str
    breed: str
    ageMonths: float
    weightKg: float
    healthStatus: str
    lactationStage: str
    daysInMilk: float
    previousWeekAvgYield: float
    bodyConditionScore: float
    ambientTemperatureC: float
    humidityPercent: float
    productionStage: str


JsonObject = dict[str, Any]

__all__ = ["FeedRecommendationRequest", "JsonObject"]
