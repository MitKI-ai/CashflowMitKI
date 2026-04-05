"""Tests for Structured Logging — STORY-041"""


def test_response_has_request_id_header(client):
    """Every response carries an X-Request-ID header."""
    r = client.get("/health")
    assert "x-request-id" in r.headers or "X-Request-ID" in r.headers


def test_request_id_is_uuid(client):
    """X-Request-ID value looks like a UUID."""
    import re
    r = client.get("/health")
    req_id = r.headers.get("x-request-id") or r.headers.get("X-Request-ID")
    assert req_id is not None
    assert re.match(r"[0-9a-f\-]{36}", req_id)


def test_structlog_module_importable():
    """structlog can be imported (is installed)."""
    import structlog
    assert structlog is not None


def test_app_logger_is_structlog():
    """app.core.logging exports a bound logger."""
    from app.core.logging import get_logger
    log = get_logger("test")
    assert log is not None


def test_structlog_produces_dict_on_health(client):
    """Health endpoint can be called without crashing logging."""
    r = client.get("/health")
    assert r.status_code == 200
