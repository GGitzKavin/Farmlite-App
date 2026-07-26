"""Checks for the retained milk-yield inference model."""

import unittest

from config.settings import MILK_YIELD_MODEL_PATH
from ml.inference.model_service import predict_milk_yield


SAMPLE_INPUT = {
    "breed": "Holstein-Friesian",
    "ageMonths": 48,
    "weightKg": 420,
    "lactationStage": "Mid",
    "daysInMilk": 120,
    "ambientTemperatureC": 28,
    "humidityPercent": 75,
    "previousWeekAvgYield": 14,
    "bodyConditionScore": 3.0,
}


class ModelServiceTests(unittest.TestCase):
    def test_retained_model_exists(self) -> None:
        self.assertTrue(MILK_YIELD_MODEL_PATH.is_file())

    def test_model_produces_existing_prediction_contract(self) -> None:
        result = predict_milk_yield(SAMPLE_INPUT)

        self.assertEqual(result["target"], "Milk_Yield_L")
        self.assertEqual(result["modelUsed"], "HistGradientBoostingRegressor")
        self.assertGreaterEqual(result["predictedMilkYieldL"], 0)


if __name__ == "__main__":
    unittest.main()
