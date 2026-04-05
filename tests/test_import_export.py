"""Tests for CSV Import + Export — STORY-032 / STORY-033"""
import io

# ── CSV Export ────────────────────────────────────────────────────────────────

def test_csv_export_returns_csv(auth_client, db, admin_user, tenant_a):
    from tests.conftest import make_subscription
    make_subscription(db, tenant_a.id, admin_user.id, name="Netflix", cost=9.99)
    r = auth_client.get("/api/v1/export/csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    text = r.text
    assert "Netflix" in text
    assert "name" in text.lower()  # header row


def test_csv_export_requires_auth(client):
    r = client.get("/api/v1/export/csv")
    assert r.status_code == 401


def test_csv_export_tenant_isolated(auth_client, auth_client_b, db, admin_user, tenant_a):
    from tests.conftest import make_subscription
    make_subscription(db, tenant_a.id, admin_user.id, name="TenantAOnly")
    r = auth_client_b.get("/api/v1/export/csv")
    assert r.status_code == 200
    assert "TenantAOnly" not in r.text


def test_json_export_returns_json(auth_client, db, admin_user, tenant_a):
    from tests.conftest import make_subscription
    make_subscription(db, tenant_a.id, admin_user.id, name="Adobe CC", cost=54.99)
    r = auth_client.get("/api/v1/export/json")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(s["name"] == "Adobe CC" for s in data)


def test_json_export_requires_auth(client):
    r = client.get("/api/v1/export/json")
    assert r.status_code == 401


# ── CSV Import ────────────────────────────────────────────────────────────────

def _csv_file(content: str) -> tuple:
    return ("file", ("subscriptions.csv", io.BytesIO(content.encode()), "text/csv"))


def test_csv_import_creates_subscriptions(auth_client, db, admin_user, tenant_a):
    csv_content = "name,provider,cost,currency,billing_cycle\nSlack,Salesforce,8.75,EUR,monthly\n"
    r = auth_client.post("/api/v1/import/csv",
                         files=[_csv_file(csv_content)])
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 1


def test_csv_import_requires_auth(client):
    csv_content = "name,cost\nTest,5\n"
    r = client.post("/api/v1/import/csv", files=[_csv_file(csv_content)])
    assert r.status_code == 401


def test_csv_import_skips_missing_name(auth_client):
    csv_content = "name,cost\n,9.99\nValid Name,5.00\n"
    r = auth_client.post("/api/v1/import/csv", files=[_csv_file(csv_content)])
    assert r.status_code == 200
    assert r.json()["imported"] == 1
    assert r.json()["skipped"] == 1


def test_csv_import_handles_extra_columns(auth_client):
    csv_content = "name,unknown_col,cost\nGithub,ignored_value,4.00\n"
    r = auth_client.post("/api/v1/import/csv", files=[_csv_file(csv_content)])
    assert r.status_code == 200
    assert r.json()["imported"] == 1


def test_csv_import_preview(auth_client):
    """Preview endpoint returns parsed rows without committing."""
    csv_content = "name,cost\nPreviewRow,3.50\n"
    r = auth_client.post("/api/v1/import/csv/preview",
                         files=[_csv_file(csv_content)])
    assert r.status_code == 200
    data = r.json()
    assert "rows" in data
    assert "columns" in data
    assert len(data["rows"]) == 1
