"""Basic API contract checks that do not change application data."""

import unittest
from unittest.mock import patch

from app import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "healthy", "service": "FarmLite AI API"},
        )

    def test_feed_endpoint_rejects_non_json_body(self) -> None:
        response = self.client.post(
            "/api/ai/feed-recommendation",
            data="not json",
            content_type="text/plain",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "success": False,
                "error": "Request body must be valid JSON.",
            },
        )

    def test_feed_endpoint_preserves_response_contract(self) -> None:
        response = self.client.post(
            "/api/ai/feed-recommendation",
            json={
                "animalId": "TEST-001",
                "animalName": "Luna",
                "breed": "Holstein-Friesian",
                "ageMonths": 48,
                "weightKg": 420,
                "healthStatus": "Healthy",
                "lactationStage": "Mid",
                "daysInMilk": 120,
                "previousWeekAvgYield": 14,
                "bodyConditionScore": 3.0,
                "ambientTemperatureC": 28,
                "humidityPercent": 75,
                "productionStage": "Mid Lactation",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(
            set(body),
            {
                "success",
                "animalId",
                "animalName",
                "prediction",
                "recommendation",
                "limitations",
            },
        )
        self.assertEqual(
            set(body["prediction"]),
            {
                "predictedMilkYieldL",
                "modelUsed",
                "target",
                "featuresUsed",
                "modelLimitation",
            },
        )
        self.assertEqual(
            set(body["recommendation"]),
            {
                "totalFeedKg",
                "roughageKg",
                "concentrateKg",
                "mineralMixKg",
                "waterAdvice",
                "feedingFrequency",
                "confidenceLevel",
                "explanation",
                "warnings",
                "disclaimer",
            },
        )

    @patch(
        "api.routes.predict_milk_yield",
        side_effect=RuntimeError("private implementation detail"),
    )
    def test_feed_endpoint_does_not_expose_unexpected_exception(
        self,
        _mock_prediction,
    ) -> None:
        response = self.client.post(
            "/api/ai/feed-recommendation",
            json={
                "animalId": "TEST-001",
                "animalName": "Luna",
                "breed": "Holstein-Friesian",
                "ageMonths": 48,
                "weightKg": 420,
                "healthStatus": "Healthy",
                "lactationStage": "Mid",
                "daysInMilk": 120,
                "previousWeekAvgYield": 14,
                "bodyConditionScore": 3.0,
                "ambientTemperatureC": 28,
                "humidityPercent": 75,
                "productionStage": "Mid Lactation",
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json(),
            {
                "success": False,
                "error": "An unexpected recommendation service error occurred.",
            },
        )
        self.assertNotIn("private implementation detail", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
