"""SSCC Service application factory."""

from flask import Flask

from sscc.extensions import ma
from sscc.resources import register_blueprints


def create_app(config_object: str = "sscc.config.Config") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    ma.init_app(app)
    register_blueprints(app)

    return app
