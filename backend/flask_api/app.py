import os

from flask import Flask
from flask_cors import CORS

from api.routes import api_blueprint
from api.v2_routes import api_v2_blueprint


def create_app() -> Flask:
    """Create the FarmLite Flask application."""

    flask_app = Flask(__name__)
    CORS(flask_app)
    flask_app.register_blueprint(api_blueprint)
    flask_app.register_blueprint(api_v2_blueprint)
    return flask_app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_enabled = os.environ.get('FLASK_DEBUG', '').strip().casefold() in {
        '1',
        'true',
        'yes',
        'on',
    }
    app.run(host='0.0.0.0', port=port, debug=debug_enabled)
