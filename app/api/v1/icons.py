"""Icon Library API — STORY-035"""
from fastapi import APIRouter, Query

from app.services.icon_service import get_all_icons, search_icons

router = APIRouter(prefix="/icons", tags=["icons"])


@router.get("/")
def list_icons(q: str = Query("")):
    if q:
        return search_icons(q)
    return get_all_icons()
