"""Integration tests for SSCC API endpoints."""

import json
from unittest.mock import patch

import pytest


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


class TestGenerateEndpoint:
    def test_returns_pdf(self, client, sscc_payload):
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        assert resp.headers["X-SSCC-Code"]
        assert len(resp.headers["X-SSCC-Code"]) == 18

    def test_sscc_is_18_digits(self, client, sscc_payload):
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        sscc = resp.headers["X-SSCC-Code"]
        assert sscc.isdigit()
        assert len(sscc) == 18

    def test_carton_number_header_present(self, client, sscc_payload):
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        carton = resp.headers["X-Carton-Number"]
        # Should start with supplier initials (BE) + customer initials (AR)
        assert carton.startswith("BEAR")

    def test_custom_carton_number_respected(self, client, sscc_payload):
        sscc_payload["carton_number"] = "ABCD0000099"
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.headers["X-Carton-Number"] == "ABCD0000099"

    def test_missing_required_field_returns_422(self, client, sscc_payload):
        del sscc_payload["po_number"]
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_invalid_check_digit_returns_422(self, client, sscc_payload):
        sscc_payload["check_digit"] = 10  # out of range
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_no_body_returns_400(self, client):
        resp = client.post("/api/v1/sscc/generate", content_type="application/json")
        assert resp.status_code == 400


class TestGenerateJsonEndpoint:
    def test_returns_sscc_json(self, client, sscc_payload):
        resp = client.post(
            "/api/v1/sscc/generate/json",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "sscc_code" in data
        assert len(data["sscc_code"]) == 18
        assert data["po_number"] == sscc_payload["po_number"]
        assert data["quantities"] == sscc_payload["quantities"]


class TestGenerateFromOrderEndpoint:
    def test_fetches_order_and_returns_pdf(self, client):
        mock_order = {
            "po_number": "PO-999",
            "customer_name": "Retail Co",
            "supplier_name": "Supply Inc",
            "store": "Store 1",
            "location": "DC North",
            "quantities": 25,
            "product": "Test Product",
        }
        with patch("sscc.resources.sscc_resource.fetch_order", return_value=mock_order):
            resp = client.post(
                "/api/v1/sscc/generate-from-order",
                data=json.dumps({"po_number": "PO-999", "check_digit": 1}),
                content_type="application/json",
            )
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

    def test_order_not_found_returns_502(self, client):
        from sscc.services.order_client import OrderServiceError

        with patch(
            "sscc.resources.sscc_resource.fetch_order",
            side_effect=OrderServiceError("Order not found"),
        ):
            resp = client.post(
                "/api/v1/sscc/generate-from-order",
                data=json.dumps({"po_number": "MISSING", "check_digit": 0}),
                content_type="application/json",
            )
        assert resp.status_code == 502
