import json

from sscc.models.sscc_model import SSCCModel, SSCCResult


def test_generate_persists_sscc_record_before_invoking_pdf_lambda(app, monkeypatch):
    payload = {
        "po_number": "PO-2024-001",
        "customer_name": "Acme Retail",
        "supplier_name": "Beta Logistics",
        "store": "Store 42",
        "location": "Warehouse A",
        "check_digit": 0,
        "quantities": 100,
        "product": "Widget XL",
    }

    called = {}

    class FakeLambdaClient:
        def invoke(self, FunctionName, InvocationType, Payload):
            called["FunctionName"] = FunctionName
            called["InvocationType"] = InvocationType
            called["Payload"] = json.loads(Payload)
            return {"StatusCode": 202}

    monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

    with app.app_context():
        from sscc.extentions.db import db
        db.drop_all()
        db.create_all()

        client = app.test_client()
        response = client.post("/api/v1/sscc/generate", json=payload)

        assert response.status_code == 202
        assert SSCCModel.query.count() == 1
        assert SSCCModel.query.first().sscc_code.startswith("0")
        assert called["FunctionName"] == "sscc-label-generator"


def test_generate_invokes_pdf_lambda_instead_of_rendering_pdf(app, monkeypatch):
    payload = {
        "po_number": "PO-2024-001",
        "customer_name": "Acme Retail",
        "supplier_name": "Beta Logistics",
        "store": "Store 42",
        "location": "Warehouse A",
        "check_digit": 0,
        "quantities": 100,
        "product": "Widget XL",
    }

    result = SSCCResult(
        sscc_code="000000000000000001",
        carton_number="CN-001",
        po_number="PO-2024-001",
        customer_name="Acme Retail",
        supplier_name="Beta Logistics",
        store="Store 42",
        location="Warehouse A",
        quantities=100,
        product="Widget XL",
    )

    called = {}

    def fake_generate_sscc(_request):
        return result

    class FakeLambdaClient:
        def invoke(self, FunctionName, InvocationType, Payload):
            called["FunctionName"] = FunctionName
            called["InvocationType"] = InvocationType
            called["Payload"] = json.loads(Payload)
            return {"StatusCode": 202}

    monkeypatch.setattr("sscc.resources.sscc_resource.generate_sscc", fake_generate_sscc)
    monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

    client = app.test_client()
    response = client.post("/api/v1/sscc/generate", json=payload)

    assert response.status_code == 202
    assert response.get_json()["message"] == "PDF generation started"
    assert called["FunctionName"] == "sscc-label-generator"
    assert called["InvocationType"] == "Event"
    assert called["Payload"]["sscc_code"] == result.sscc_code


def test_persisted_sscc_record_matches_lambda_payload(app, monkeypatch):
    """Verify the DB-persisted SSCC record contains exact values sent to Lambda."""
    payload = {
        "po_number": "PO-2024-999",
        "customer_name": "Big Box Retail",
        "supplier_name": "Fast Supply",
        "store": "Store 88",
        "location": "Warehouse B",
        "check_digit": 5,
        "quantities": 250,
        "product": "Premium Widget",
    }

    called = {}

    class FakeLambdaClient:
        def invoke(self, FunctionName, InvocationType, Payload):
            called["Payload"] = json.loads(Payload)
            return {"StatusCode": 202}

    monkeypatch.setattr("sscc.resources.sscc_resource.boto3", type("Boto3Module", (), {"client": lambda *args, **kwargs: FakeLambdaClient()})())

    with app.app_context():
        from sscc.extentions.db import db
        db.drop_all()
        db.create_all()

        client = app.test_client()
        response = client.post("/api/v1/sscc/generate", json=payload)

        assert response.status_code == 202

        sscc_record = SSCCModel.query.first()
        assert sscc_record is not None
        assert sscc_record.po_number == called["Payload"]["po_number"]
        assert sscc_record.carton_number == called["Payload"]["carton_number"]
        assert sscc_record.sscc_code == called["Payload"]["sscc_code"]
        assert sscc_record.customer_name == called["Payload"]["customer_name"]
        assert sscc_record.supplier_name == called["Payload"]["supplier_name"]
        assert sscc_record.store == called["Payload"]["store"]
        assert sscc_record.location == called["Payload"]["location"]
        assert sscc_record.quantities == called["Payload"]["quantities"]
        assert sscc_record.product == called["Payload"]["product"]
