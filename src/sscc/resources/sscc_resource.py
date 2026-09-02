"""SSCC blueprint — all /api/v1/sscc/* routes."""

import json
from math import ceil

import boto3
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from sscc.schemas.sscc_schema import SSCCRequestSchema
from sscc.models.sscc_model import SSCCOrderModel, SSCCRequest, SSCCModel
from sscc.extentions.db import db
from sscc.services.sscc_service import generate_sscc

sscc_bp = Blueprint("sscc", __name__, url_prefix="/api/v1/sscc")

_request_schema = SSCCRequestSchema()


def _persist_generation(request: SSCCRequest, result):
    order = SSCCOrderModel.query.filter_by(po_number=result.po_number).one_or_none()
    if order is None:
        order = SSCCOrderModel(
            po_number=result.po_number,
            customer_name=result.customer_name,
            supplier_name=result.supplier_name,
            store=result.store,
            location=result.location,
            quantities=result.quantities,
            pack_size=request.pack_size,
        )
        db.session.add(order)
        db.session.flush()

    expected_cartons = ceil(order.quantities / order.pack_size)
    generated_cartons = SSCCModel.query.filter_by(po_number=result.po_number).count() + 1
    carton_printed = (
        request.carton_printed
        if request.carton_printed is not None
        else expected_cartons
    )
    order.carton_count = expected_cartons
    order.status = 1 if generated_cartons >= expected_cartons else 2

    sscc_record = SSCCModel(
        po_number=result.po_number,
        customer_name=result.customer_name,
        supplier_name=result.supplier_name,
        store=result.store,
        location=result.location,
        check_digit=int(request.check_digit),
        quantities=result.quantities,
        pack_size=request.pack_size,
        carton_count=expected_cartons,
        carton_printed=carton_printed,
        status=order.status,
        product=result.product,
        carton_number=result.carton_number,
        sscc_code=result.sscc_code,
    )
    db.session.add(sscc_record)
    db.session.commit()

    return order, sscc_record


# this is very important API endpoint, this will be called once the user presses
# the print button on UI, this will save the data at that moment in the database
# and invoke the lambda function for generating the barcode. (if pdf option is selected)
# else will invoke the actual physical printer to print the labels.
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

    try:
        result = generate_sscc(sscc_request)
    except ValueError as exc:
        return jsonify({"error": "SSCC configuration is invalid.", "details": str(exc)}), 500

    order, sscc_record = _persist_generation(sscc_request, result)

    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName="sscc-label-generator",
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
            "pack_size": result.pack_size,
            "carton_count": order.carton_count,
            "carton_printed": sscc_record.carton_printed,
            "status": order.status,
            "product": result.product,
        }),
    )

    return jsonify({
        "message": "PDF generation started",
        "sscc_code": result.sscc_code,
        "carton_number": result.carton_number,
        "carton_count": order.carton_count,
        "carton_printed": sscc_record.carton_printed,
        "status": order.status,
    }), 202


