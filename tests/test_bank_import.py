"""Tests for Bank Statement Import (CSV + PDF) — STORY-095, 096, 097."""
import io

# ── STORY-095: CSV Parser ────────────────────────────────────────────

def test_parse_csv_bank_statement(auth_client):
    csv_content = """Buchungstag;Verwendungszweck;Betrag
01.03.2026;Gehalt Arbeitgeber AG;4500.00
03.03.2026;REWE SAGT DANKE;-67.50
05.03.2026;EnBW Strom Abschlag;-85.00
10.03.2026;NETFLIX.COM;-17.99
27.03.2026;Miete Wohnung;-1200.00"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("kontoauszug.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert len(data["entries"]) == 5
    assert data["entries"][0]["description"] == "Gehalt Arbeitgeber AG"
    assert data["entries"][0]["amount"] == 4500.0
    assert data["entries"][1]["amount"] == -67.50


def test_csv_auto_detect_delimiter(auth_client):
    csv_content = """Datum,Beschreibung,Betrag
01.03.2026,Gehalt,4500.00
03.03.2026,Einkauf,-50.00"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("auszug.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert r.status_code == 200
    assert len(r.json()["entries"]) == 2


def test_csv_handles_german_numbers(auth_client):
    """German format: comma as decimal separator, semicolon as delimiter."""
    csv_content = """Buchungstag;Verwendungszweck;Betrag
01.03.2026;Gehalt;4.500,00
03.03.2026;Einkauf;-67,50"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("auszug.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert r.status_code == 200
    entries = r.json()["entries"]
    assert entries[0]["amount"] == 4500.0
    assert entries[1]["amount"] == -67.50


# ── STORY-096: PDF Parser ────────────────────────────────────────────

def test_parse_pdf_not_supported_yet_graceful(auth_client):
    """PDF with invalid content returns graceful error."""
    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("auszug.pdf", io.BytesIO(b"not a real pdf"), "application/pdf")},
    )
    # Should not crash — graceful error
    assert r.status_code in (200, 400)


def test_upload_size_limit(auth_client):
    """Files over 10MB are rejected."""
    big_content = b"x" * (11 * 1024 * 1024)  # 11MB
    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("huge.csv", io.BytesIO(big_content), "text/csv")},
    )
    assert r.status_code == 400


# ── STORY-097: Preview + Matching ────────────────────────────────────

def test_preview_with_matching(auth_client):
    """Parsed entries get matched against existing entities."""
    # Create known entities
    acc = auth_client.post("/api/v1/accounts/", json={"name": "Girokonto", "type": "checking", "bank_name": "Test"}).json()
    auth_client.post("/api/v1/standing-orders/", json={
        "name": "Gehalt", "type": "income", "amount": 4500,
        "frequency": "monthly", "execution_day": 27, "account_id": acc["id"],
    })
    auth_client.post("/api/v1/direct-debits/", json={
        "name": "EnBW Strom", "amount": 85, "frequency": "monthly",
        "expected_day": 5, "account_id": acc["id"],
    })

    csv_content = """Buchungstag;Verwendungszweck;Betrag
01.03.2026;Gehalt Arbeitgeber AG;4500.00
05.03.2026;EnBW Strom Abschlag;-85.00
15.03.2026;LIDL FILIALE;-32.10"""

    r = auth_client.post(
        "/api/v1/import/bank-statement/parse",
        files={"file": ("auszug.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    entries = r.json()["entries"]
    # Gehalt should match (green)
    gehalt = [e for e in entries if "Gehalt" in e["description"]][0]
    assert gehalt["match_status"] == "known_income"

    # EnBW should match (red)
    strom = [e for e in entries if "EnBW" in e["description"]][0]
    assert strom["match_status"] == "known_expense"

    # LIDL should be unknown (yellow)
    lidl = [e for e in entries if "LIDL" in e["description"]][0]
    assert lidl["match_status"] == "unknown"


def test_confirm_import_creates_transactions(auth_client):
    """Confirming import creates Transaction entities."""
    r = auth_client.post("/api/v1/import/bank-statement/confirm", json={
        "entries": [
            {"description": "LIDL Einkauf", "amount": -32.10, "date": "2026-03-15",
             "action": "transaction", "category": "food"},
            {"description": "Zahnarzt", "amount": -120.00, "date": "2026-03-20",
             "action": "transaction", "category": "health"},
            {"description": "Ignoriert", "amount": -5.00, "date": "2026-03-01",
             "action": "ignore"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["created_transactions"] == 2
    assert data["ignored"] == 1
