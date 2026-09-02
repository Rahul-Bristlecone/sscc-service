"""SSCC domain models."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sscc.extentions.db import db


class SSCCModel(db.Model):
    __tablename__ = "sscc_labels"
    __table_args__ = (
        db.UniqueConstraint("sscc_code", name="uq_sscc_code"),
        db.UniqueConstraint("carton_number", name="uq_carton_number"),
    )

    sscc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_number = db.Column(db.String(128), nullable=False)
    customer_name = db.Column(db.String(128), nullable=False)
    supplier_name = db.Column(db.String(128), nullable=False)
    store = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False) # irrelevant
    check_digit = db.Column(db.Integer, nullable=False)
    # quantities to deliver, another->quantities to ship
    quantities = db.Column(db.Integer, nullable=False, default=1)
    # pack size from product table over ride by TUN in some scenarios, default 1
    pack_size = db.Column(db.Integer, nullable=False, default=1)
    # calculated & might be entered by user
    carton_count = db.Column(db.Integer, nullable=False, default=0)
    carton_printed = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, nullable=False, default=0)
    product = db.Column(db.String(256), nullable=True)
    carton_number = db.Column(db.String(32), nullable=False)
    sscc_code = db.Column(db.String(20), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


# this whole data will be received from order table
class SSCCOrderModel(db.Model):
    __tablename__ = "sscc_orders"
    __table_args__ = (db.UniqueConstraint("po_number", name="uq_order_po_number"),)

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_number = db.Column(db.String(128), nullable=False)
    customer_name = db.Column(db.String(128), nullable=False)
    supplier_name = db.Column(db.String(128), nullable=False)
    store = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False)
    quantities = db.Column(db.Integer, nullable=False)
    pack_size = db.Column(db.Integer, nullable=False, default=1)
    carton_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, nullable=False, default=0)


class CartonSequenceModel(db.Model):
    __tablename__ = "carton_sequence"

    sequence_id = db.Column(db.Integer, primary_key=True, default=1)
    next_number = db.Column(db.Integer, nullable=False, default=1)


@dataclass
class SSCCRequest:
    po_number: str
    customer_name: str
    supplier_name: str
    store: str
    location: str
    check_digit: int          # 0-9; used as GS1 extension digit
    quantities: int
    pack_size: int = 1
    carton_printed: Optional[int] = None
    product: Optional[str] = None
    carton_number: Optional[str] = None   # auto-generated if omitted


@dataclass
class SSCCResult:
    sscc_code: str            # 18-digit GS1 SSCC
    carton_number: str
    po_number: str
    customer_name: str
    supplier_name: str
    store: str
    location: str
    quantities: int
    pack_size: int = 1
    product: str = ""
