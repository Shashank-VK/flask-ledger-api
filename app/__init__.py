from typing import Any
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.extensions import db
from app.routes import auth_bp, expenses_bp, summary_bp, health_bp

def create_app(config_object: Any = None) -> Flask:
    app = Flask(__name__)

    if config_object is None:
        app.config.from_object(Config)
    elif isinstance(config_object, dict):
        app.config.from_mapping(config_object)
    else:
        app.config.from_object(config_object)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(health_bp)

    # Ensure all errors are returned as JSON, never HTML
    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        response = jsonify({"error": e.description})
        response.status_code = e.code if e.code is not None else 500
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(e: Exception):
        if isinstance(e, HTTPException):
            response = jsonify({"error": e.description})
            response.status_code = e.code if e.code is not None else 500
            return response
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()

    return app
