"""Register all blueprints with the Flask app."""

from flask import Flask

from sscc.resources.sscc_resource import sscc_bp
from sscc.resources.health_resource import health_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(sscc_bp)
