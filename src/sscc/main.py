"""SSCC Service application factory — factory pattern."""

import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS

from sscc.extensions import ma
from sscc.extentions.db import db
from sscc.resources import register_blueprints


def create_app(config_object: str = "sscc.config.Config") -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config_object: Path to configuration class (e.g., "sscc.config.Config")
    
    Returns:
        Flask application instance
    """
    sscc_service = Flask(__name__)
    
    # Load configuration from object
    sscc_service.config.from_object(config_object)
    
    # Database configuration
    sscc_service.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    sscc_service.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    
    # Flask-specific configuration
    sscc_service.config["PROPAGATE_EXCEPTIONS"] = True
    sscc_service.config["API_TITLE"] = "SSCC Service API"
    sscc_service.config["API_VERSION"] = "v1"
    
    # Initialize extensions
    db.init_app(sscc_service)
    ma.init_app(sscc_service)
    
    # Configure CORS for development and production
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    allowed_origins = [origin.strip() for origin in allowed_origins]
    
    CORS(
        sscc_service,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        intercept_exceptions=True,
    )
    
    # Create database tables on app context
    with sscc_service.app_context():
        db.create_all()
    
    # Register blueprints
    register_blueprints(sscc_service)
    
    # Health check endpoint
    @sscc_service.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200
    
    return sscc_service
