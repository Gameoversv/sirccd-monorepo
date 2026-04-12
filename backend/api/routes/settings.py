"""
Ajustes de administracion para parametros del score de prioridad.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import require_admin
from db.session import get_db
from models.priority_setting import PrioritySetting
from models.user import User
from schemas.priority_settings import PrioritySettingsResponse, PrioritySettingsUpdateRequest
from core.config import settings as app_settings


router = APIRouter(prefix="/admin/settings", tags=["Ajustes"])


def _ensure_priority_settings(db: Session) -> PrioritySetting:
    row = db.query(PrioritySetting).order_by(PrioritySetting.id.asc()).first()
    if row:
        return row

    row = PrioritySetting(
        weight_severity=0.35,
        weight_age=0.20,
        weight_damage_type=0.15,
        weight_location=0.20,
        weight_duplicates=0.10,
        poi_radius_meters=int(getattr(app_settings, "PRIORITY_POI_RADIUS_METERS", 500)),
        duplicate_radius_meters=int(getattr(app_settings, "PRIORITY_DUPLICATE_RADIUS_METERS", 100)),
        duplicate_time_window_days=int(getattr(app_settings, "PRIORITY_DUPLICATE_TIME_WINDOW_DAYS", 30)),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _to_response(row: PrioritySetting) -> PrioritySettingsResponse:
    total = float(
        row.weight_severity
        + row.weight_age
        + row.weight_damage_type
        + row.weight_location
        + row.weight_duplicates
    )
    return PrioritySettingsResponse(
        id=row.id,
        weight_severity=float(row.weight_severity),
        weight_age=float(row.weight_age),
        weight_damage_type=float(row.weight_damage_type),
        weight_location=float(row.weight_location),
        weight_duplicates=float(row.weight_duplicates),
        weights_total=round(total, 4),
        poi_radius_meters=int(row.poi_radius_meters),
        duplicate_radius_meters=int(row.duplicate_radius_meters),
        duplicate_time_window_days=int(row.duplicate_time_window_days),
        updated_by=row.updated_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/priority", response_model=PrioritySettingsResponse)
def get_priority_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    _ = current_user
    row = _ensure_priority_settings(db)
    return _to_response(row)


@router.put("/priority", response_model=PrioritySettingsResponse)
def update_priority_settings(
    payload: PrioritySettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    row = _ensure_priority_settings(db)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return _to_response(row)

    # Si se actualizan pesos, validamos que sumen 1.0 (100%).
    next_weights = {
        "weight_severity": float(row.weight_severity),
        "weight_age": float(row.weight_age),
        "weight_damage_type": float(row.weight_damage_type),
        "weight_location": float(row.weight_location),
        "weight_duplicates": float(row.weight_duplicates),
    }
    for key in list(next_weights.keys()):
        if key in data:
            next_weights[key] = float(data[key])

    weights_total = sum(next_weights.values())
    if abs(weights_total - 1.0) > 0.001:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los pesos deben sumar 1.0 (100%).",
        )

    for key, value in data.items():
        setattr(row, key, value)

    row.updated_by = current_user.id
    db.commit()
    db.refresh(row)
    return _to_response(row)

