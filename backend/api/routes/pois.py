"""
API de POIs para visualización de capas (P-02)

Endpoints para:
- Obtener POIs de capas críticas (escuelas, hospitales, bomberos, centros comunitarios)
- Soportar visualización de buffers de riesgo peatonal en frontend
"""

from typing import List, Optional, Set
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, cast
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_X, ST_Y

from db.session import get_db
from api.deps import get_current_active_user
from models.user import User
from models.poi import POI, POICategory
from schemas.poi import (
    POILayerCategoryEnum,
    POILayerItemResponse,
    POILayerListResponse,
)


router = APIRouter()


LAYER_TO_SOURCE_CATEGORIES = {
    POILayerCategoryEnum.SCHOOL: {POICategory.SCHOOL, POICategory.UNIVERSITY},
    POILayerCategoryEnum.HOSPITAL: {POICategory.HOSPITAL, POICategory.CLINIC},
    POILayerCategoryEnum.FIRE_STATION: {POICategory.FIRE_STATION},
    POILayerCategoryEnum.COMMUNITY_CENTER: {
        POICategory.COMMERCIAL,
        POICategory.BUS_STATION,
        POICategory.OTHER,
    },
}

SOURCE_TO_LAYER_CATEGORY = {
    source_category: layer_category
    for layer_category, source_categories in LAYER_TO_SOURCE_CATEGORIES.items()
    for source_category in source_categories
}

RECOMMENDED_BUFFER_BY_LAYER = {
    POILayerCategoryEnum.SCHOOL: 150,
    POILayerCategoryEnum.HOSPITAL: 120,
    POILayerCategoryEnum.FIRE_STATION: 200,
    POILayerCategoryEnum.COMMUNITY_CENTER: 100,
}


@router.get("/", response_model=POILayerListResponse)
def list_poi_layers(
    categories: Optional[List[POILayerCategoryEnum]] = Query(
        None,
        description="Categorías de capas: school, hospital, fire_station, community_center",
    ),
    limit: int = Query(1000, ge=1, le=5000, description="Cantidad máxima de POIs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lista POIs en categorías aptas para capas de riesgo peatonal.

    La visualización de buffers (50-200 m) se realiza en frontend usando estos puntos.
    """
    del current_user  # Garantiza autenticación sin exponer usuarios inactivos

    selected_layers = categories or list(LAYER_TO_SOURCE_CATEGORIES.keys())

    source_categories: Set[POICategory] = set()
    for layer in selected_layers:
        source_categories.update(LAYER_TO_SOURCE_CATEGORIES[layer])

    point_geom = cast(POI.location, Geometry(geometry_type="POINT", srid=4326))
    latitude_col = ST_Y(point_geom).label("latitude")
    longitude_col = ST_X(point_geom).label("longitude")

    rows = (
        db.query(POI, latitude_col, longitude_col)
        .filter(POI.category.in_(source_categories))
        .order_by(asc(POI.category), asc(POI.name))
        .limit(limit)
        .all()
    )

    pois: List[POILayerItemResponse] = []

    for poi, latitude, longitude in rows:
        if latitude is None or longitude is None:
            continue

        layer_category = SOURCE_TO_LAYER_CATEGORY.get(poi.category)
        if layer_category is None:
            continue

        pois.append(
            POILayerItemResponse(
                id=poi.id,
                name=poi.name,
                category=layer_category,
                source_category=poi.category.value,
                latitude=round(float(latitude), 6),
                longitude=round(float(longitude), 6),
                address=poi.address,
                city=poi.city,
                priority_weight=int(poi.priority_weight or 1),
                recommended_buffer_m=RECOMMENDED_BUFFER_BY_LAYER[layer_category],
            )
        )

    return POILayerListResponse(
        total=len(pois),
        pois=pois,
        categories=selected_layers,
        min_buffer_m=50,
        default_buffer_m=120,
        max_buffer_m=200,
    )
