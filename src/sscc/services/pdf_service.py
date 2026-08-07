"""PDF shipping label generation using ReportLab."""

import io
import os
import tempfile

import barcode
from barcode.writer import ImageWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    HRFlowable,
)

from sscc.models.sscc_model import SSCCResult


_PAGE_SIZE = landscape(A5)
_MARGIN = 12 * mm


def _generate_barcode_image(sscc_code: str) -> str:
    """Write a GS1-128 barcode PNG to a temp file and return its path."""
    # AI (00) identifies the data as an SSCC in GS1-128 context
    barcode_data = f"00{sscc_code}"
    writer = ImageWriter()
    writer.set_options(
        {
            "module_height": 15,
            "module_width": 0.6,
            "quiet_zone": 2,
            "font_size": 8,
            "text_distance": 3,
            "write_text": True,
        }
    )
    code128 = barcode.get("code128", barcode_data, writer=writer)
    tmp_path = os.path.join(tempfile.gettempdir(), f"sscc_{sscc_code}")
    full_path = code128.save(tmp_path)   # saves as <tmp_path>.png
    return full_path


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Heading1"],
            fontSize=14,
            spaceAfter=4,
            textColor=colors.HexColor("#1a1a2e"),
            leading=18,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#555555"),
            spaceAfter=1,
        ),
        "value": ParagraphStyle(
            "Value",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=4,
            leading=14,
        ),
        "sscc": ParagraphStyle(
            "SSCC",
            parent=base["Normal"],
            fontSize=9,
            fontName="Courier",
            textColor=colors.HexColor("#222222"),
            spaceAfter=2,
            alignment=1,  # centre
        ),
    }


def generate_label_pdf(result: SSCCResult) -> bytes:
    """Generate a shipping label PDF for the given SSCCResult and return raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=_PAGE_SIZE,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN,
        title=f"Shipping Label – {result.sscc_code}",
    )

    st = _styles()
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Shipping Label", st["title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4 * mm))

    # ── Detail table ─────────────────────────────────────────────────────────
    detail_data = [
        [
            Paragraph("Customer", st["label"]),
            Paragraph("Store", st["label"]),
            Paragraph("Supplier", st["label"]),
            Paragraph("PO Number", st["label"]),
        ],
        [
            Paragraph(result.customer_name, st["value"]),
            Paragraph(result.store, st["value"]),
            Paragraph(result.supplier_name, st["value"]),
            Paragraph(result.po_number, st["value"]),
        ],
        [
            Paragraph("Product", st["label"]),
            Paragraph("Quantities Ordered", st["label"]),
            Paragraph("Location", st["label"]),
            Paragraph("Carton No.", st["label"]),
        ],
        [
            Paragraph(result.product or "—", st["value"]),
            Paragraph(str(result.quantities), st["value"]),
            Paragraph(result.location, st["value"]),
            Paragraph(result.carton_number, st["value"]),
        ],
    ]

    col_width = (_PAGE_SIZE[0] - 2 * _MARGIN) / 4
    detail_table = Table(detail_data, colWidths=[col_width] * 4)
    detail_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f4ff")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#f0f4ff")),
                ("ROWBACKGROUND", (0, 1), (-1, 1), colors.white),
                ("ROWBACKGROUND", (0, 3), (-1, 3), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(detail_table)
    story.append(Spacer(1, 6 * mm))

    # ── Barcode ───────────────────────────────────────────────────────────────
    barcode_path = _generate_barcode_image(result.sscc_code)
    try:
        barcode_img = RLImage(barcode_path, width=150 * mm, height=22 * mm)
        barcode_img.hAlign = "CENTER"
        story.append(barcode_img)
    finally:
        if os.path.exists(barcode_path):
            os.remove(barcode_path)

    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(f"(00)&nbsp;{result.sscc_code}", st["sscc"])
    )

    doc.build(story)
    return buffer.getvalue()
