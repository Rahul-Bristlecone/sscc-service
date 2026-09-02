"""SSCC blueprint — all /api/v1/sscc/* routes."""

import json

import boto3
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from sscc.schemas.sscc_schema import SSCCRequestSchema, SSCCResultSchema, OrderFetchSchema
from sscc.models.sscc_model import SSCCRequest, SSCCModel
from sscc.extentions.db import db
from sscc.services.sscc_service import generate_sscc
from sscc.services.order_client import fetch_order, OrderServiceError

sscc_bp = Blueprint("sscc", __name__, url_prefix="/api/v1/sscc")

_request_schema = SSCCRequestSchema()
_result_schema = SSCCResultSchema()
_order_fetch_schema = OrderFetchSchema()


@sscc_bp.post("/generate")
def generate():
    """Generate SSCC data and trigger the separate PDF Lambda microservice."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        sscc_request: SSCCRequest = _request_schema.load(json_data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed.", "details": exc.messages}), 422

    result = generate_sscc(sscc_request)

    sscc_record = SSCCModel(
        po_number=result.po_number,
        customer_name=result.customer_name,
        supplier_name=result.supplier_name,
        store=result.store,
        location=result.location,
        check_digit=int(sscc_request.check_digit),
        quantities=result.quantities,
        product=result.product,
        carton_number=result.carton_number,
        sscc_code=result.sscc_code,
    )
    db.session.add(sscc_record)
    db.session.commit()

    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName="sscc-pdf-generator",
        InvocationType="Event",
        Payload=json.dumps({
            "sscc_code": result.sscc_code,
            "carton_number": result.carton_number,
            "po_number": result.po_number,
            "customer_name": result.customer_name,
            "supplier_name": result.supplier_name,
            "store": result.store,
            "location": result.location,
            "quantities": result.quantities,
            "product": result.product,
        }),
    )

    return jsonify({
        "message": "PDF generation started",
        "sscc_code": result.sscc_code,
        "carton_number": result.carton_number,
    }), 202


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
    """Fetch order details, generate SSCC data, and trigger the PDF Lambda."""
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

    sscc_record = SSCCModel(
        po_number=result.po_number,
        customer_name=result.customer_name,
        supplier_name=result.supplier_name,
        store=result.store,
        location=result.location,
        check_digit=int(sscc_request.check_digit),
        quantities=result.quantities,
        product=result.product,
        carton_number=result.carton_number,
        sscc_code=result.sscc_code,
    )
    db.session.add(sscc_record)
    db.session.commit()

    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName="sscc-pdf-generator",
        InvocationType="Event",
        Payload=json.dumps({
            "sscc_code": result.sscc_code,
            "carton_number": result.carton_number,
            "po_number": result.po_number,
            "customer_name": result.customer_name,
            "supplier_name": result.supplier_name,
            "store": result.store,
            "location": result.location,
            "quantities": result.quantities,
            "product": result.product,
        }),
    )

    return jsonify({
        "message": "PDF generation started",
        "sscc_code": result.sscc_code,
        "carton_number": result.carton_number,
    }), 202
