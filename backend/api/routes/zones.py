"""
Zonas administrativas (P-03)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
from api.deps import get_current_active_user
from models.user import User
from models.zone import Zone

router = APIRouter()


@router.get("/", response_model=List[dict])
def list_zones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista zonas administrativas disponibles para filtrado."""
    zones = db.query(Zone.id, Zone.name, Zone.code).order_by(Zone.name).all()
    return [{"id": z.id, "name": z.name, "code": z.code} for z in zones]
