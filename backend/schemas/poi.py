"""
Schemas Pydantic para capas de POIs (P-02)
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class POILayerCategoryEnum(str, Enum):
    """Categorías simplificadas para visualización en mapa."""

    SCHOOL = "school"
    HOSPITAL = "hospital"
    FIRE_STATION = "fire_station"
    COMMUNITY_CENTER = "community_center"


class POILayerItemResponse(BaseModel):
    """POI listo para dibujarse como capa de mapa."""

    id: int
    name: str
    category: POILayerCategoryEnum
    source_category: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    priority_weight: int = Field(1, ge=1, le=10)
    recommended_buffer_m: int = Field(..., ge=50, le=200)

    model_config = ConfigDict(from_attributes=True)


class POILayerListResponse(BaseModel):
    """Response para obtener la capa de POIs."""

    total: int
    pois: List[POILayerItemResponse]
    categories: List[POILayerCategoryEnum]
    min_buffer_m: int = Field(50, ge=50, le=200)
    default_buffer_m: int = Field(120, ge=50, le=200)
    max_buffer_m: int = Field(200, ge=50, le=200)
