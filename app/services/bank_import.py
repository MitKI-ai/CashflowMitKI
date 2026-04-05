"""Bank Statement Import Service — CSV + PDF parsing with entity matching."""
import csv
import io
import logging
import re

from sqlalchemy.orm import Session

from app.models.direct_debit import DirectDebit
from app.models.standing_order import StandingOrder
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _parse_german_number(s: str) -> float:
    """Parse German number format: 1.234,56 → 1234.56"""
    s = s.strip()
    if not s:
        return 0.0
    # Remove thousands separator (.)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _detect_delimiter(content: str) -> str:
    first_line = content.split("\n")[0]
    if ";" in first_line:
        return ";"
    if "\t" in first_line:
        return "\t"
    return ","


def _parse_date(s: str) -> str:
    """Parse DD.MM.YYYY → YYYY-MM-DD"""
    s = s.strip()
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return s  # already ISO


class BankImportService:
    @staticmethod
    def parse_csv(content: str) -> list[dict]:
        delimiter = _detect_delimiter(content)
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        entries = []
        for row in reader:
            # Find date, description, amount columns
            date_val = None
            desc_val = None
            amount_val = None
            for key, val in row.items():
                if not key:
                    continue
                kl = key.lower().strip()
                if kl in ("buchungstag", "datum", "date", "valuta"):
                    date_val = _parse_date(val)
                elif kl in ("verwendungszweck", "beschreibung", "description", "text", "buchungstext"):
                    desc_val = val.strip()
                elif kl in ("betrag", "amount", "umsatz", "betrag (eur)"):
                    amount_val = _parse_german_number(val)
            if desc_val and amount_val is not None:
                entries.append({
                    "date": date_val or "",
                    "description": desc_val,
                    "amount": amount_val,
                })
        return entries

    @staticmethod
    def parse_pdf(content: bytes) -> list[dict]:
        try:
            import pdfplumber
            entries = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    for line in text.split("\n"):
                        # Try to extract date + description + amount pattern
                        m = re.match(
                            r"(\d{2}\.\d{2}\.\d{4})\s+(.+?)\s+(-?[\d.,]+)\s*$",
                            line.strip(),
                        )
                        if m:
                            entries.append({
                                "date": _parse_date(m.group(1)),
                                "description": m.group(2).strip(),
                                "amount": _parse_german_number(m.group(3)),
                            })
            return entries
        except Exception as e:
            logger.warning("PDF parsing failed: %s", e)
            return []

    @staticmethod
    def match_entries(
        entries: list[dict], *, db: Session, tenant_id: str,
    ) -> list[dict]:
        """Match parsed entries against known StandingOrders, DirectDebits, Subscriptions."""
        standing_orders = db.query(StandingOrder).filter(
            StandingOrder.tenant_id == tenant_id, StandingOrder.is_active == True
        ).all()
        direct_debits = db.query(DirectDebit).filter(
            DirectDebit.tenant_id == tenant_id, DirectDebit.is_active == True
        ).all()
        subscriptions = db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id, Subscription.status == "active"
        ).all()

        known_income = {so.name.lower(): so for so in standing_orders if so.type == "income"}
        known_expense_so = {so.name.lower(): so for so in standing_orders if so.type != "income"}
        known_expense_dd = {dd.name.lower(): dd for dd in direct_debits}
        known_subs = {sub.name.lower(): sub for sub in subscriptions}

        def _fuzzy_match(entity_name: str, description: str) -> bool:
            """Check if entity name matches description via substring or keyword overlap."""
            if entity_name in description or description in entity_name:
                return True
            # Keyword overlap: split entity name into words, check if significant words appear
            words = [w for w in entity_name.split() if len(w) >= 3]
            if words and sum(1 for w in words if w in description) >= max(1, len(words) // 2):
                return True
            return False

        for entry in entries:
            desc_lower = entry["description"].lower()
            matched = False

            # Check income standing orders
            for name in known_income:
                if _fuzzy_match(name, desc_lower):
                    entry["match_status"] = "known_income"
                    entry["matched_entity"] = f"StandingOrder: {known_income[name].name}"
                    matched = True
                    break

            if not matched:
                # Check expense standing orders
                for name in known_expense_so:
                    if _fuzzy_match(name, desc_lower):
                        entry["match_status"] = "known_expense"
                        entry["matched_entity"] = f"StandingOrder: {known_expense_so[name].name}"
                        matched = True
                        break

            if not matched:
                # Check direct debits
                for name in known_expense_dd:
                    if _fuzzy_match(name, desc_lower):
                        entry["match_status"] = "known_expense"
                        entry["matched_entity"] = f"DirectDebit: {known_expense_dd[name].name}"
                        matched = True
                        break

            if not matched:
                # Check subscriptions
                for name in known_subs:
                    if _fuzzy_match(name, desc_lower):
                        entry["match_status"] = "known_expense"
                        entry["matched_entity"] = f"Subscription: {known_subs[name].name}"
                        matched = True
                        break

            if not matched:
                entry["match_status"] = "unknown"
                entry["matched_entity"] = None

        return entries
