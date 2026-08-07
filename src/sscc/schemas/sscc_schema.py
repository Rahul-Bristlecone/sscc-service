"""Marshmallow schemas for SSCC request and response validation."""

from marshmallow import Schema, fields, validate, post_load, validates, ValidationError

from sscc.models.sscc_model import SSCCRequest, SSCCResult


class SSCCRequestSchema(Schema):
    po_number = fields.Str(required=True, metadata={"description": "Purchase order number"})
    customer_name = fields.Str(required=True, metadata={"description": "Customer name"})
    supplier_name = fields.Str(required=True, metadata={"description": "Supplier name"})
    store = fields.Str(required=True, metadata={"description": "Destination store"})
    location = fields.Str(required=True, metadata={"description": "Delivery location"})
    check_digit = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=9),
        metadata={"description": "GS1 extension digit (0–9)"},
    )
    quantities = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "Number of units to deliver"},
    )
    product = fields.Str(load_default=None, metadata={"description": "Product description"})
    carton_number = fields.Str(
        load_default=None,
        metadata={"description": "Pre-formed carton number (auto-generated if omitted)"},
    )

    @validates("po_number")
    def validate_po_number(self, value: str) -> None:
        if not value.strip():
            raise ValidationError("po_number must not be blank.")

    @post_load
    def make_request(self, data: dict, **kwargs) -> SSCCRequest:
        return SSCCRequest(**data)


class SSCCResultSchema(Schema):
    sscc_code = fields.Str()
    carton_number = fields.Str()
    po_number = fields.Str()
    customer_name = fields.Str()
    supplier_name = fields.Str()
    store = fields.Str()
    location = fields.Str()
    quantities = fields.Int()
    product = fields.Str()


class OrderFetchSchema(Schema):
    """Schema for fetching SSCC from order service by PO number."""
    po_number = fields.Str(required=True)
    check_digit = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=9),
    )
    carton_number = fields.Str(load_default=None)
