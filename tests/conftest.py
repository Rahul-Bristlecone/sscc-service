"""Pytest fixtures shared across test modules."""

import pytest

from sscc.main import create_app


@pytest.fixture()
def app():
    app = create_app("sscc.config.TestingConfig")
    app.config.update(
        {
            "TESTING": True,
            "GS1_COMPANY_PREFIX": "1234567",
            "SSCC_EXTENSION_DIGIT": 0,
        }
    )
    with app.app_context():
        from sscc.extentions.db import db
        db.create_all()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sscc_payload():
    return {
        "po_number": "PO-2024-001",
        "customer_name": "Acme Retail",
        "supplier_name": "Beta Logistics",
        "store": "Store 42",
        "location": "Warehouse A",
        "check_digit": 0,
        "quantities": 100,
        "product": "Widget XL",
    }
