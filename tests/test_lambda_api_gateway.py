import importlib
import json

lambda_module = importlib.import_module("pdf.handlers.lambda_handler")


def test_lambda_handler_supports_api_gateway_route(monkeypatch):
    payload = {
        "sscc_code": "000000000000000001",
        "carton_number": "CN-001",
        "po_number": "PO-1001",
        "customer_name": "Acme Retail",
        "supplier_name": "Beta Logistics",
        "store": "Store 5",
        "location": "WH-1",
        "quantities": 12,
        "product": "Widgets",
    }

    captured = {}

    def fake_generate_label_pdf(result):
        captured["sscc_code"] = result.sscc_code
        return b"%PDF-1.4 test"

    def fake_upload_to_s3(pdf_bytes, file_name, bucket_name):
        captured["file_name"] = file_name
        captured["bucket_name"] = bucket_name
        return "s3://bucket/labels/test.pdf"

    monkeypatch.setattr(lambda_module, "generate_label_pdf", fake_generate_label_pdf)
    monkeypatch.setattr(lambda_module, "upload_to_s3", fake_upload_to_s3)

    event = {
        "httpMethod": "POST",
        "path": "/generate",
        "body": json.dumps(payload),
    }

    result = lambda_module.lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "application/json"
    assert result["body"]
    assert captured["sscc_code"] == payload["sscc_code"]
    assert captured["file_name"] == "label_000000000000000001.pdf"
