from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from ml.feed_planner import generate_feed_plan
from ml.model_service import ModelServiceError, predict_milk_yield

app = Flask(__name__)
CORS(app) # Enable CORS for frontend requests

# Load environment variables if needed
# from dotenv import load_dotenv
# load_dotenv()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "FarmLite AI API"}), 200

@app.route('/api/ai/feed-recommendation', methods=['POST'])
def recommend_feed():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

        prediction = predict_milk_yield(data)
        weight_kg = float(data["weightKg"])
        predicted_milk_yield_l = prediction["predictedMilkYieldL"]

        base_feed_kg = weight_kg * 0.025
        milk_support_feed_kg = predicted_milk_yield_l * 0.30
        estimated_total_feed_kg = base_feed_kg + milk_support_feed_kg

        feed_plan = generate_feed_plan(
            predicted_feed_kg=estimated_total_feed_kg,
            weight_kg=weight_kg,
            milk_yield_l=predicted_milk_yield_l,
            health_status=data.get("healthStatus", "Healthy"),
            production_stage=data.get("productionStage"),
        )

        response = {
            "success": True,
            "animalId": data.get("animalId"),
            "animalName": data.get("animalName"),
            "prediction": {
                "predictedMilkYieldL": predicted_milk_yield_l,
                "modelUsed": prediction["modelUsed"],
                "target": prediction["target"],
                "featuresUsed": prediction["featuresUsed"],
                "modelLimitation": prediction["modelLimitation"],
            },
            "recommendation": {
                "totalFeedKg": feed_plan["total_feed_kg"],
                "roughageKg": feed_plan["roughage_kg"],
                "concentrateKg": feed_plan["concentrate_kg"],
                "mineralMixKg": feed_plan["mineral_mix_kg"],
                "waterAdvice": feed_plan["water_advice"],
                "feedingFrequency": feed_plan["feeding_frequency"],
                "confidenceLevel": feed_plan["confidence_level"],
                "explanation": feed_plan["explanation"],
                "warnings": feed_plan["warnings"],
                "disclaimer": feed_plan["disclaimer"],
            },
            "limitations": [
                "The ML model predicts milk yield only.",
                "The feed plan is generated using rule-based advisory logic.",
                "This recommendation is not veterinary or nutritionist advice.",
            ],
        }

        return jsonify(response), 200

    except ModelServiceError as error:
        return jsonify({"success": False, "error": error.message}), error.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Manual endpoint test from Windows PowerShell:
# curl -X POST http://127.0.0.1:5000/api/ai/feed-recommendation ^
#   -H "Content-Type: application/json" ^
#   -d "{\"animalName\":\"Luna\",\"breed\":\"Friesian\",\"ageMonths\":48,\"weightKg\":420,\"lactationStage\":\"Mid Lactation\",\"daysInMilk\":120,\"ambientTemperatureC\":28,\"humidityPercent\":75,\"previousWeekAvgYield\":14,\"bodyConditionScore\":3.0,\"healthStatus\":\"Healthy\",\"productionStage\":\"Mid Lactation\"}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
