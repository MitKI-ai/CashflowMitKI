from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_tenant_id, require_role
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    return CategoryService.list(db, tenant_id=tenant_id)


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    return CategoryService.create(db, tenant_id=tenant_id, **data.model_dump())


@router.put("/{cat_id}", response_model=CategoryResponse)
def update_category(
    cat_id: str,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    cat = CategoryService.get(db, cat_id=cat_id, tenant_id=tenant_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryService.update(db, cat=cat, **data.model_dump(exclude_unset=True))


@router.delete("/{cat_id}", status_code=204)
def delete_category(
    cat_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    _admin=Depends(require_role(["admin"])),
):
    cat = CategoryService.get(db, cat_id=cat_id, tenant_id=tenant_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    CategoryService.delete(db, cat=cat)
