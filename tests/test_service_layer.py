"""Tests for STORY-018: Service Layer — SubscriptionService + CategoryService"""
from datetime import date

import pytest

from app.services.subscription_service import SubscriptionService
from app.services.category_service import CategoryService
from tests.conftest import make_subscription, make_category


# ── SubscriptionService ───────────────────────────────────────────────────────

def test_service_list_subscriptions(db, tenant_a, admin_user):
    make_subscription(db, tenant_a.id, admin_user.id, name="GitHub")
    make_subscription(db, tenant_a.id, admin_user.id, name="AWS")
    results = SubscriptionService.list(db, tenant_id=tenant_a.id)
    names = [s.name for s in results]
    assert "GitHub" in names
    assert "AWS" in names


def test_service_list_filter_by_status(db, tenant_a, admin_user):
    make_subscription(db, tenant_a.id, admin_user.id, name="Active", status="active")
    make_subscription(db, tenant_a.id, admin_user.id, name="Paused", status="paused")
    results = SubscriptionService.list(db, tenant_id=tenant_a.id, status="active")
    assert all(s.status == "active" for s in results)
    assert any(s.name == "Active" for s in results)


def test_service_get_subscription(db, tenant_a, admin_user):
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Notion")
    found = SubscriptionService.get(db, sub_id=sub.id, tenant_id=tenant_a.id)
    assert found is not None
    assert found.name == "Notion"


def test_service_get_wrong_tenant_returns_none(db, tenant_a, tenant_b, admin_user):
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Secret")
    found = SubscriptionService.get(db, sub_id=sub.id, tenant_id=tenant_b.id)
    assert found is None


def test_service_create_subscription(db, tenant_a, admin_user):
    sub = SubscriptionService.create(
        db,
        tenant_id=tenant_a.id,
        user_id=admin_user.id,
        name="Figma",
        provider="Figma Inc",
        cost=15.0,
        currency="USD",
        billing_cycle="monthly",
        status="active",
        start_date=date.today(),
    )
    assert sub.id is not None
    assert sub.name == "Figma"
    assert sub.tenant_id == tenant_a.id


def test_service_update_subscription(db, tenant_a, admin_user):
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="Old Name")
    updated = SubscriptionService.update(db, sub=sub, name="New Name", cost=20.0)
    assert updated.name == "New Name"
    assert updated.cost == 20.0


def test_service_delete_subscription(db, tenant_a, admin_user):
    sub = make_subscription(db, tenant_a.id, admin_user.id, name="ToDelete")
    sub_id = sub.id
    SubscriptionService.delete(db, sub=sub)
    assert SubscriptionService.get(db, sub_id=sub_id, tenant_id=tenant_a.id) is None


# ── CategoryService ───────────────────────────────────────────────────────────

def test_service_list_categories(db, tenant_a):
    make_category(db, tenant_a.id, name="SaaS")
    make_category(db, tenant_a.id, name="Cloud")
    results = CategoryService.list(db, tenant_id=tenant_a.id)
    names = [c.name for c in results]
    assert "SaaS" in names
    assert "Cloud" in names


def test_service_list_categories_tenant_isolated(db, tenant_a, tenant_b):
    make_category(db, tenant_a.id, name="A Only")
    results = CategoryService.list(db, tenant_id=tenant_b.id)
    assert len(results) == 0


def test_service_create_category(db, tenant_a):
    cat = CategoryService.create(db, tenant_id=tenant_a.id, name="DevOps", color="#0000FF")
    assert cat.id is not None
    assert cat.name == "DevOps"
    assert cat.tenant_id == tenant_a.id


def test_service_delete_category(db, tenant_a):
    cat = make_category(db, tenant_a.id, name="Remove Me")
    CategoryService.delete(db, cat=cat)
    assert CategoryService.get(db, cat_id=cat.id, tenant_id=tenant_a.id) is None
