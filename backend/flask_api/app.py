from flask import Flask, request, jsonify
from flask_cors import CORS
import os

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
        data = request.json
        # Expected inputs based on prompt:
        # breed, weight, health_status, age, milk_production_stage
        
        breed = data.get('breed', 'Unknown')
        weight = data.get('weight', 0)
        health_status = data.get('healthStatus', 'Healthy')
        age = data.get('age', 0)
        stage = data.get('milkProductionStage', 'Dry')

        # Placeholder AI Logic until Hugging Face model is integrated
        # The user requested to keep the HF model integration empty for now.
        
        recommended_feed = "Standard Dairy Mix"
        quantity = 0
        nutrition_score = 80
        summary = "Based on basic parameters, maintain regular feeding."

        if health_status.lower() == 'sick':
            recommended_feed = "High-Energy Recovery Feed"
            summary = "Animal is sick. High-energy, easily digestible feed is recommended."
        elif 'lactating' in stage.lower():
            recommended_feed = "Lactation Premium Ration"
            quantity = (float(weight) * 0.03) + 5 # Rough estimate
            summary = f"Currently in {stage} stage. Lactating cows require higher intake. Supplementing with calcium and phosphorus."
            nutrition_score = 95
        else:
            quantity = float(weight) * 0.025
            summary = "Standard maintenance ration suitable for current weight and stage."

        response = {
            "recommendedFeed": recommended_feed,
            "quantity": round(quantity, 2),
            "nutritionScore": nutrition_score,
            "summary": summary
        }
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
