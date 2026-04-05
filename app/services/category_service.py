"""CategoryService — thin DB wrapper for category operations."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryService:

    @staticmethod
    def list(db: Session, tenant_id: str) -> list[Category]:
        return (
            db.query(Category)
            .filter(Category.tenant_id == tenant_id)
            .order_by(Category.name)
            .all()
        )

    @staticmethod
    def get(db: Session, cat_id: str, tenant_id: str) -> Category | None:
        return (
            db.query(Category)
            .filter(Category.id == cat_id, Category.tenant_id == tenant_id)
            .first()
        )

    @staticmethod
    def create(
        db: Session,
        tenant_id: str,
        name: str,
        color: str = "#F97316",
        icon: str | None = None,
    ) -> Category:
        cat = Category(tenant_id=tenant_id, name=name, color=color, icon=icon)
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    @staticmethod
    def update(db: Session, cat: Category, **kwargs) -> Category:
        for key, value in kwargs.items():
            setattr(cat, key, value)
        db.commit()
        db.refresh(cat)
        return cat

    @staticmethod
    def delete(db: Session, cat: Category) -> None:
        db.delete(cat)
        db.commit()
