"""SSCC domain models."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sscc.extentions.db import db


class SSCCModel(db.Model):
    __tablename__ = "sscc_labels"
    __table_args__ = (
        db.UniqueConstraint("sscc_code", name="uq_sscc_code"),
        db.UniqueConstraint("po_number", "carton_number", name="uq_sscc_business_key"),
    )

    sscc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    po_number = db.Column(db.String(128), nullable=False)
    customer_name = db.Column(db.String(128), nullable=False)
    supplier_name = db.Column(db.String(128), nullable=False)
    store = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(128), nullable=False)
    check_digit = db.Column(db.Integer, nullable=False)
    quantities = db.Column(db.Integer, nullable=False, default=1)
    product = db.Column(db.String(256), nullable=True)
    carton_number = db.Column(db.String(32), nullable=False)
    sscc_code = db.Column(db.String(18), nullable=False)

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


@dataclass
class SSCCRequest:
    po_number: str
    customer_name: str
    supplier_name: str
    store: str
    location: str
    check_digit: int          # 0-9; used as GS1 extension digit
    quantities: int
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
    product: str = ""
