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
    def test_triggers_pdf_lambda_and_returns_202(self, client, sscc_payload, monkeypatch):
        """Generate endpoint now triggers Lambda asynchronously and returns 202."""
        class FakeLambdaClient:
            def invoke(self, FunctionName, InvocationType, Payload):
                return {"StatusCode": 202}

        monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.status_code == 202
        data = resp.get_json()
        assert data["message"] == "PDF generation started"
        assert len(data["sscc_code"]) == 20

    def test_sscc_is_18_digits(self, client, sscc_payload, monkeypatch):
        class FakeLambdaClient:
            def invoke(self, FunctionName, InvocationType, Payload):
                return {"StatusCode": 202}

        monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        sscc = resp.get_json()["sscc_code"]
        assert sscc.isdigit()
        assert len(sscc) == 20

    def test_carton_number_in_response(self, client, sscc_payload, monkeypatch):
        class FakeLambdaClient:
            def invoke(self, FunctionName, InvocationType, Payload):
                return {"StatusCode": 202}

        monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        carton = resp.get_json()["carton_number"]
        assert carton == "0000001"

    def test_custom_carton_number_respected(self, client, sscc_payload, monkeypatch):
        class FakeLambdaClient:
            def invoke(self, FunctionName, InvocationType, Payload):
                return {"StatusCode": 202}

        monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

        sscc_payload["carton_number"] = "0000099"
        resp = client.post(
            "/api/v1/sscc/generate",
            data=json.dumps(sscc_payload),
            content_type="application/json",
        )
        assert resp.get_json()["carton_number"] == "0000099"

    def test_carton_printed_defaults_to_carton_count(self, client, sscc_payload, monkeypatch):
        class FakeLambdaClient:
            def invoke(self, FunctionName, InvocationType, Payload):
                return {"StatusCode": 202}

        monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

        response = client.post("/api/v1/sscc/generate", json=sscc_payload)

        assert response.status_code == 202
        data = response.get_json()
        assert data["carton_count"] == 100
        assert data["carton_printed"] == 100

    def test_carton_printed_can_be_overridden(self, client, sscc_payload, monkeypatch):
        class FakeLambdaClient:
            def invoke(self, FunctionName, InvocationType, Payload):
                return {"StatusCode": 202}

        monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())
        sscc_payload["carton_printed"] = 4

        response = client.post("/api/v1/sscc/generate", json=sscc_payload)

        assert response.status_code == 202
        assert response.get_json()["carton_printed"] == 4

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


