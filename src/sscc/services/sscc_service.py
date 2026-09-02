"""Core SSCC generation logic."""

import threading
import re
from math import ceil

from flask import current_app

from sscc.extentions.db import db
from sscc.models.sscc_model import CartonSequenceModel, SSCCRequest, SSCCResult

# The lock protects concurrent requests within one application process. The
# database row makes the sequence durable across process restarts.
_counter_lock = threading.Lock()


def _next_carton_sequence() -> int:
    with _counter_lock:
        sequence = db.session.get(CartonSequenceModel, 1)
        if sequence is None:
            sequence = CartonSequenceModel(sequence_id=1, next_number=1)
            db.session.add(sequence)
            db.session.flush()
        seq = sequence.next_number
        if seq > 9_999_999:
            raise ValueError("The 7-digit carton-number sequence is exhausted.")
        sequence.next_number += 1
        db.session.flush()
    return seq


def _advance_carton_sequence(carton_number: str) -> None:
    with _counter_lock:
        sequence = db.session.get(CartonSequenceModel, 1)
        if sequence is None:
            sequence = CartonSequenceModel(sequence_id=1, next_number=1)
            db.session.add(sequence)
            db.session.flush()
        sequence.next_number = max(sequence.next_number, int(carton_number) + 1)
        db.session.flush()


def _get_initials(name: str, count: int = 2) -> str:
    """Return the first `count` uppercase initials of a multi-word name."""
    words = re.split(r"\s+", name.strip())
    initials = "".join(w[0].upper() for w in words if w)
    return (initials + "XX")[:count]   # pad with X if fewer words than count


def build_carton_number(supplier_name: str, customer_name: str, sequence: int) -> str:
    """
    Format: a company-assigned 7-digit numeric sequence.
    """
    if not 1 <= sequence <= 9_999_999:
        raise ValueError("Carton sequence must be between 1 and 9,999,999.")
    return f"{sequence:07d}"


def _calculate_sscc_check_digit(seventeen_digits: str) -> int:
    """
    GS1 Mod-10 check digit.
    Multiply digits from right: odd positions × 3, even × 1; sum; complement to 10.
    """
    if len(seventeen_digits) != 17 or not seventeen_digits.isdigit():
        raise ValueError(f"Expected 17 numeric digits, got: {seventeen_digits!r}")
    total = sum(
        int(d) * (3 if i % 2 == 0 else 1)
        for i, d in enumerate(reversed(seventeen_digits))
    )
    return (10 - (total % 10)) % 10


def generate_sscc(request: SSCCRequest) -> SSCCResult:
    """
    Build an 18-digit GS1 SSCC and return a populated SSCCResult.

        SSCC layout (20 digits total including AI 00):
            [2] application identifier — always 00
      [1] extension digit  — from request.check_digit
            [9] GS1 company prefix — from GS1_COMPANY_PREFIX config
            [7] serial reference  — the 7-digit carton number
      [1] check digit       — calculated via GS1 Mod-10
    """
    company_prefix: str = current_app.config["GS1_COMPANY_PREFIX"]
    if not company_prefix.isdigit() or len(company_prefix) != 9:
        raise ValueError("GS1_COMPANY_PREFIX must contain exactly 9 digits.")

    # Resolve or generate carton number
    if request.carton_number:
        carton_number = request.carton_number
        sequence_digits = carton_number
        _advance_carton_sequence(carton_number)
    else:
        seq = _next_carton_sequence()
        carton_number = build_carton_number("", "", seq)
        sequence_digits = f"{seq:07d}"

    # Build the 17-digit payload: extension(1) + prefix(9) + serial(7).
    seventeen = f"{request.check_digit}{company_prefix}{sequence_digits}"
    check = _calculate_sscc_check_digit(seventeen)
    sscc_code = f"00{seventeen}{check}"

    return SSCCResult(
        sscc_code=sscc_code,
        carton_number=carton_number,
        po_number=request.po_number,
        customer_name=request.customer_name,
        supplier_name=request.supplier_name,
        store=request.store,
        location=request.location,
        quantities=request.quantities,
        pack_size=request.pack_size,
        product=request.product or "",
    )
