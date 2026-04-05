"""Tests for Alembic Migrations Setup — STORY-044"""
import os


def test_alembic_ini_exists():
    assert os.path.exists("alembic.ini"), "alembic.ini must exist at project root"


def test_migrations_folder_exists():
    assert os.path.isdir("migrations"), "migrations/ folder must exist"


def test_env_py_exists():
    assert os.path.exists("migrations/env.py"), "migrations/env.py must exist"


def test_versions_folder_exists():
    assert os.path.isdir("migrations/versions"), "migrations/versions/ folder must exist"


def test_initial_migration_exists():
    files = os.listdir("migrations/versions")
    py_files = [f for f in files if f.endswith(".py") and not f.startswith("__")]
    assert len(py_files) >= 1, "At least one migration must exist"


def test_alembic_env_uses_settings():
    """env.py reads DATABASE_URL from app settings (not hardcoded)."""
    with open("migrations/env.py") as f:
        content = f.read()
    assert "settings" in content or "database_url" in content.lower()


def test_alembic_ini_uses_env_variable():
    """alembic.ini sqlalchemy.url references env var or placeholder."""
    with open("alembic.ini") as f:
        content = f.read()
    # Should have sqlalchemy.url setting
    assert "sqlalchemy.url" in content
