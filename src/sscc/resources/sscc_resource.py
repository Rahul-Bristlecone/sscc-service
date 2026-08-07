"""SSCC blueprint — all /api/v1/sscc/* routes."""

from flask import Blueprint, request, jsonify, make_response, current_app
from marshmallow import ValidationError

from sscc.schemas.sscc_schema import SSCCRequestSchema, SSCCResultSchema, OrderFetchSchema
from sscc.models.sscc_model import SSCCRequest
from sscc.services.sscc_service import generate_sscc
from sscc.services.pdf_service import generate_label_pdf
from sscc.services.order_client import fetch_order, OrderServiceError

sscc_bp = Blueprint("sscc", __name__, url_prefix="/api/v1/sscc")

_request_schema = SSCCRequestSchema()
_result_schema = SSCCResultSchema()
_order_fetch_schema = OrderFetchSchema()


@sscc_bp.post("/generate")
def generate():
    """
    Generate an SSCC barcode and return a downloadable PDF shipping label.

    Accepts JSON with all order fields directly.
    Returns: application/pdf
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        sscc_request: SSCCRequest = _request_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed.", "details": exc.messages}), 422

    result = generate_sscc(sscc_request)
    pdf_bytes = generate_label_pdf(result)

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="label_{result.sscc_code}.pdf"'
    )
    response.headers["X-SSCC-Code"] = result.sscc_code
    response.headers["X-Carton-Number"] = result.carton_number
    return response


@sscc_bp.post("/generate/json")
def generate_json():
    """
    Same as /generate but returns SSCC metadata as JSON instead of a PDF.
    Useful for integrations that only need the SSCC code.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        sscc_request: SSCCRequest = _request_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed.", "details": exc.messages}), 422

    result = generate_sscc(sscc_request)
    return jsonify(_result_schema.dump(result)), 201


@sscc_bp.post("/generate-from-order")
def generate_from_order():
    """
    Fetch order details from the order service by PO number,
    then generate and return a PDF shipping label.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        params = _order_fetch_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed.", "details": exc.messages}), 422

    try:
        order = fetch_order(params["po_number"])
    except OrderServiceError as exc:
        return jsonify({"error": str(exc)}), 502

    # Merge order data with request params
    full_payload = {
        **order,
        "check_digit": params["check_digit"],
        "carton_number": params.get("carton_number"),
    }

    try:
        sscc_request: SSCCRequest = _request_schema.load(full_payload)
    except ValidationError as exc:
        return jsonify(
            {"error": "Order data from order service is incomplete.", "details": exc.messages}
        ), 502

    result = generate_sscc(sscc_request)
    pdf_bytes = generate_label_pdf(result)

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="label_{result.sscc_code}.pdf"'
    )
    response.headers["X-SSCC-Code"] = result.sscc_code
    response.headers["X-Carton-Number"] = result.carton_number
    return response
