"""FTS5 Full-Text Search Service — STORY-031

Uses SQLite FTS5 virtual table. Isolated here so PostgreSQL migration
only requires changes in this single file.
"""
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.subscription import Subscription

logger = logging.getLogger(__name__)

_DDL_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS subscriptions_fts
USING fts5(
    subscription_id UNINDEXED,
    tenant_id UNINDEXED,
    name,
    provider,
    notes,
    tokenize='unicode61'
);
"""

_TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS sub_fts_insert
AFTER INSERT ON subscriptions BEGIN
    INSERT INTO subscriptions_fts(subscription_id, tenant_id, name, provider, notes)
    VALUES (new.id, new.tenant_id,
            COALESCE(new.name,''), COALESCE(new.provider,''), COALESCE(new.notes,''));
END;
"""

_TRIGGER_UPDATE = """
CREATE TRIGGER IF NOT EXISTS sub_fts_update
AFTER UPDATE ON subscriptions BEGIN
    DELETE FROM subscriptions_fts WHERE subscription_id = old.id;
    INSERT INTO subscriptions_fts(subscription_id, tenant_id, name, provider, notes)
    VALUES (new.id, new.tenant_id,
            COALESCE(new.name,''), COALESCE(new.provider,''), COALESCE(new.notes,''));
END;
"""

_TRIGGER_DELETE = """
CREATE TRIGGER IF NOT EXISTS sub_fts_delete
AFTER DELETE ON subscriptions BEGIN
    DELETE FROM subscriptions_fts WHERE subscription_id = old.id;
END;
"""


def init_fts(db: Session) -> None:
    """Create FTS5 table + triggers. Called at app startup."""
    try:
        for stmt in [_DDL_FTS, _TRIGGER_INSERT, _TRIGGER_UPDATE, _TRIGGER_DELETE]:
            db.execute(text(stmt))
        db.commit()
    except Exception as exc:
        logger.error("FTS5 init failed: %s", exc)


def rebuild_fts(db: Session) -> None:
    """Rebuild FTS index from current subscriptions table."""
    db.execute(text("DELETE FROM subscriptions_fts"))
    db.execute(text("""
        INSERT INTO subscriptions_fts(subscription_id, tenant_id, name, provider, notes)
        SELECT id, tenant_id, COALESCE(name,''), COALESCE(provider,''), COALESCE(notes,'')
        FROM subscriptions
    """))
    db.commit()


def search(db: Session, tenant_id: str, query: str) -> list[Subscription]:
    """Full-text search within a tenant's subscriptions."""
    if not query or not query.strip():
        return (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.name)
            .all()
        )

    # Sanitise query: append * for prefix matching, escape special chars
    safe_q = _fts_escape(query.strip()) + "*"

    try:
        rows = db.execute(
            text("""
                SELECT subscription_id FROM subscriptions_fts
                WHERE subscriptions_fts MATCH :q
                  AND tenant_id = :tid
            """),
            {"q": safe_q, "tid": tenant_id},
        ).fetchall()
    except Exception as exc:
        logger.warning("FTS5 search failed, falling back to LIKE: %s", exc)
        return _fallback_search(db, tenant_id, query)

    ids = [r[0] for r in rows]
    if not ids:
        return []
    return (
        db.query(Subscription)
        .filter(Subscription.id.in_(ids), Subscription.tenant_id == tenant_id)
        .all()
    )


def _fallback_search(db: Session, tenant_id: str, query: str) -> list[Subscription]:
    like = f"%{query}%"
    return (
        db.query(Subscription)
        .filter(
            Subscription.tenant_id == tenant_id,
            (Subscription.name.ilike(like) |
             Subscription.provider.ilike(like) |
             Subscription.notes.ilike(like)),
        )
        .all()
    )


def _fts_escape(q: str) -> str:
    """Escape FTS5 special characters."""
    special = set('"*^()|')
    return "".join(f'"{c}"' if c in special else c for c in q)
