"""Core SSCC generation logic."""

import threading
import re

from flask import current_app

from sscc.models.sscc_model import SSCCRequest, SSCCResult

# Thread-safe sequential carton counter (per-process; reset on restart)
_counter_lock = threading.Lock()
_carton_counter: int = 1


def _next_carton_sequence() -> int:
    global _carton_counter
    with _counter_lock:
        seq = _carton_counter
        _carton_counter += 1
    return seq


def _get_initials(name: str, count: int = 2) -> str:
    """Return the first `count` uppercase initials of a multi-word name."""
    words = re.split(r"\s+", name.strip())
    initials = "".join(w[0].upper() for w in words if w)
    return (initials + "XX")[:count]   # pad with X if fewer words than count


def build_carton_number(supplier_name: str, customer_name: str, sequence: int) -> str:
    """
    Format: <2 supplier initials><2 customer initials><7-digit zero-padded sequence>
    e.g. ABXY0000001
    """
    sup = _get_initials(supplier_name, 2)
    cus = _get_initials(customer_name, 2)
    return f"{sup}{cus}{sequence:07d}"


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

    SSCC layout (18 digits total):
      [1] extension digit  — from request.check_digit
      [7] GS1 company prefix — from GS1_COMPANY_PREFIX config
      [9] serial reference  — 7-digit carton sequence left-padded to 9 digits
      [1] check digit       — calculated via GS1 Mod-10
    """
    company_prefix: str = current_app.config["GS1_COMPANY_PREFIX"]

    # Resolve or generate carton number
    if request.carton_number:
        carton_number = request.carton_number
        # Extract the trailing 7-digit numeric sequence for the serial reference
        match = re.search(r"(\d{7})$", carton_number)
        sequence_digits = match.group(1) if match else f"{_next_carton_sequence():07d}"
    else:
        seq = _next_carton_sequence()
        carton_number = build_carton_number(request.supplier_name, request.customer_name, seq)
        sequence_digits = f"{seq:07d}"

    # Build the 17-digit payload: extension(1) + prefix(7) + serial(9)
    serial_reference = sequence_digits.zfill(9)
    seventeen = f"{request.check_digit}{company_prefix}{serial_reference}"
    check = _calculate_sscc_check_digit(seventeen)
    sscc_code = f"{seventeen}{check}"

    return SSCCResult(
        sscc_code=sscc_code,
        carton_number=carton_number,
        po_number=request.po_number,
        customer_name=request.customer_name,
        supplier_name=request.supplier_name,
        store=request.store,
        location=request.location,
        quantities=request.quantities,
        product=request.product or "",
    )
