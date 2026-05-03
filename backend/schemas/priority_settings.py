"""
Schemas de ajustes de prioridad (admin).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class PrioritySettingsUpdateRequest(BaseModel):
    weight_severity: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_age: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_damage_type: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_location: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_duplicates: Optional[float] = Field(None, ge=0.0, le=1.0)

    poi_radius_meters: Optional[int] = Field(None, ge=1, le=5000)
    duplicate_radius_meters: Optional[int] = Field(None, ge=1, le=5000)
    duplicate_time_window_days: Optional[int] = Field(None, ge=1, le=365)

    # M-13: DBSCAN clustering params
    clustering_eps_meters: Optional[int] = Field(None, ge=5, le=2000)
    clustering_min_samples: Optional[int] = Field(None, ge=2, le=20)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "weight_severity": 0.35,
                "weight_age": 0.20,
                "weight_damage_type": 0.15,
                "weight_location": 0.20,
                "weight_duplicates": 0.10,
                "poi_radius_meters": 500,
                "duplicate_radius_meters": 100,
                "duplicate_time_window_days": 30,
                "clustering_eps_meters": 50,
                "clustering_min_samples": 2,
            }
        }
    )


class PrioritySettingsResponse(BaseModel):
    id: int
    weight_severity: float
    weight_age: float
    weight_damage_type: float
    weight_location: float
    weight_duplicates: float
    weights_total: float
    poi_radius_meters: int
    duplicate_radius_meters: int
    duplicate_time_window_days: int
    clustering_eps_meters: int
    clustering_min_samples: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

