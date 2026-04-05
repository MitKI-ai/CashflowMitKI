"""ReportService — PDF Finanzreport mit ReportLab (EPIC-208 / Sprint 20).

Generates a monthly or yearly Cashflow + Vermögens-Report as a PDF byte stream.
No binary OS dependencies — ReportLab is pure Python.
"""
from __future__ import annotations

import io
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand colours ──────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0A1A3A")
ORANGE = colors.HexColor("#F97316")
CREME = colors.HexColor("#F8E3C7")
LIGHT_GRAY = colors.HexColor("#F3F4F6")
MID_GRAY = colors.HexColor("#9CA3AF")
GREEN = colors.HexColor("#22C55E")
RED = colors.HexColor("#EF4444")
BLUE = colors.HexColor("#3B82F6")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Normal"],
            fontSize=22,
            textColor=NAVY,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=MID_GRAY,
            spaceAfter=16,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Normal"],
            fontSize=13,
            textColor=NAVY,
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base["Normal"],
            fontSize=9,
            textColor=MID_GRAY,
            alignment=TA_LEFT,
        ),
        "value": ParagraphStyle(
            "value",
            parent=base["Normal"],
            fontSize=14,
            fontName="Helvetica-Bold",
            alignment=TA_RIGHT,
        ),
        "cell": ParagraphStyle(
            "cell",
            parent=base["Normal"],
            fontSize=9,
            textColor=NAVY,
        ),
        "cell_right": ParagraphStyle(
            "cell_right",
            parent=base["Normal"],
            fontSize=9,
            textColor=NAVY,
            alignment=TA_RIGHT,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontSize=8,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
        ),
    }


def _money(value: float, positive_green: bool = False) -> tuple[str, colors.Color]:
    sign = "+" if value >= 0 else ""
    formatted = f"{sign}{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    if positive_green:
        color = GREEN if value >= 0 else RED
    else:
        color = NAVY
    return formatted, color


def _metric_row(label: str, value: float, s: dict, *, color: colors.Color | None = None) -> list:
    val_str, auto_color = _money(value)
    c = color or auto_color
    val_para = Paragraph(
        f'<font color="#{c.hexval()[2:] if hasattr(c,"hexval") else "0A1A3A"}">'
        f'<b>{val_str}</b></font>',
        s["cell_right"],
    )
    return [Paragraph(label, s["cell"]), val_para]


class ReportService:
    @staticmethod
    def generate_monthly_pdf(
        *,
        tenant_name: str,
        user_name: str,
        year: int,
        month: int,
        cashflow_summary: dict[str, Any],
        net_worth: float = 0.0,
        savings_goals: list[dict[str, Any]] | None = None,
        top_transactions: list[dict[str, Any]] | None = None,
    ) -> bytes:
        """Return PDF bytes for a monthly cashflow report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )
        s = _styles()
        month_label = f"{month:02d}/{year}"
        elements: list = []

        # ── Header ────────────────────────────────────────────────────────────
        elements.append(Paragraph("cashflow.mitKI.ai", s["title"]))
        elements.append(Paragraph(f"Monatsbericht {month_label} · {tenant_name}", s["subtitle"]))
        elements.append(HRFlowable(width="100%", thickness=2, color=ORANGE, spaceAfter=12))

        # ── Cashflow Übersicht ────────────────────────────────────────────────
        elements.append(Paragraph("Cashflow-Übersicht", s["section"]))

        income = cashflow_summary.get("monthly_income", 0.0)
        expenses = cashflow_summary.get("monthly_expenses", 0.0)
        direct_debits = cashflow_summary.get("monthly_direct_debits", 0.0)
        subscriptions = cashflow_summary.get("monthly_subscriptions", 0.0)
        savings = cashflow_summary.get("monthly_savings", 0.0)
        net = cashflow_summary.get("monthly_net", 0.0)

        cf_data = [
            ["Position", "Betrag"],
            ["Einnahmen", f"+{income:,.2f} €"],
            ["Feste Ausgaben", f"-{expenses:,.2f} €"],
            ["Lastschriften", f"-{direct_debits:,.2f} €"],
            ["Abonnements", f"-{subscriptions:,.2f} €"],
            ["Sparrate", f"-{savings:,.2f} €"],
            ["Netto-Cashflow", f"{net:+,.2f} €"],
        ]

        cf_table = Table(cf_data, colWidths=[120 * mm, 50 * mm])
        cf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [LIGHT_GRAY, colors.white]),
            ("BACKGROUND", (0, -1), (-1, -1), CREME),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TEXTCOLOR", (1, -1), (1, -1), GREEN if net >= 0 else RED),
            ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, MID_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(cf_table)
        elements.append(Spacer(1, 8 * mm))

        # ── Gesamtvermögen ────────────────────────────────────────────────────
        if net_worth:
            elements.append(Paragraph("Gesamtvermögen", s["section"]))
            nw_data = [["Gesamtvermögen", f"{net_worth:,.2f} €"]]
            nw_table = Table(nw_data, colWidths=[120 * mm, 50 * mm])
            nw_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CREME),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
                ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(nw_table)
            elements.append(Spacer(1, 8 * mm))

        # ── Sparziele ─────────────────────────────────────────────────────────
        if savings_goals:
            elements.append(Paragraph("Sparziele", s["section"]))
            sg_data = [["Ziel", "Aktuell", "Ziel", "Fortschritt"]]
            for g in savings_goals:
                pct = min(100.0, g["current"] / g["target"] * 100) if g.get("target") else 0
                sg_data.append([
                    g["name"],
                    f"{g['current']:,.2f} €",
                    f"{g['target']:,.2f} €",
                    f"{pct:.1f}%",
                ])
            sg_table = Table(sg_data, colWidths=[75 * mm, 35 * mm, 35 * mm, 25 * mm])
            sg_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, MID_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(sg_table)
            elements.append(Spacer(1, 8 * mm))

        # ── Top Transaktionen ─────────────────────────────────────────────────
        if top_transactions:
            elements.append(Paragraph("Letzte Transaktionen", s["section"]))
            tx_data = [["Datum", "Beschreibung", "Kategorie", "Betrag"]]
            for tx in top_transactions[:10]:
                sign = "+" if tx["type"] == "income" else "-"
                tx_data.append([
                    tx["date"],
                    tx["description"][:40],
                    tx.get("category", ""),
                    f"{sign}{tx['amount']:,.2f} €",
                ])
            tx_table = Table(tx_data, colWidths=[25 * mm, 75 * mm, 30 * mm, 30 * mm])
            tx_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("BOX", (0, 0), (-1, -1), 0.5, MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, MID_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(tx_table)
            elements.append(Spacer(1, 8 * mm))

        # ── Footer ────────────────────────────────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceBefore=8))
        elements.append(Paragraph(
            f"Erstellt am {date.today().strftime('%d.%m.%Y')} · cashflow.mitKI.ai · {user_name}",
            s["footer"],
        ))

        doc.build(elements)
        return buffer.getvalue()
