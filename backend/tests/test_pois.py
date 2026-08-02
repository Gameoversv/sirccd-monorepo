"""
Tests de `GET /api/v1/pois` (api/routes/pois.py).

Este endpoint no tenía ningún test: ni de RBAC ni funcional. Es el que
alimenta las capas de riesgo del mapa y el que estuvo detrás del incidente de
producción del 2026-07-19 (tabla `pois` vacía).

Se cubren la autenticación y el mapeo capa -> categorías de origen, que es
lógica pura. Las consultas contra la tabla `pois` no se cubren aquí porque usa
columnas PostGIS y no existe en el entorno SQLite de tests.
"""

import pytest
from fastapi.testclient import TestClient

from api.routes.pois import (
    LAYER_TO_SOURCE_CATEGORIES,
    RECOMMENDED_BUFFER_BY_LAYER,
    SOURCE_TO_LAYER_CATEGORY,
)
from models.poi import POICategory
from schemas.poi import POILayerCategoryEnum


ENDPOINT = "/api/v1/pois/"


# ==========================================
# Autenticación
# ==========================================

@pytest.mark.unit
class TestPoisAutenticacion:

    def test_sin_token_no_se_puede_listar(self, client: TestClient):
        response = client.get(ENDPOINT)

        assert response.status_code in (401, 403)

    def test_con_token_invalido_no_se_puede_listar(self, client: TestClient):
        response = client.get(ENDPOINT, headers={"Authorization": "Bearer no-es-un-jwt"})

        assert response.status_code == 401

    def test_rechaza_el_esquema_de_autorizacion_incorrecto(self, client: TestClient):
        response = client.get(ENDPOINT, headers={"Authorization": "Basic dXNlcjpwYXNz"})

        assert response.status_code in (401, 403)


# ==========================================
# Validación de parámetros
# ==========================================

@pytest.mark.unit
class TestPoisValidacionDeParametros:

    def test_rechaza_una_categoria_inexistente(self, client: TestClient, auth_headers_admin: dict):
        response = client.get(f"{ENDPOINT}?categories=aeropuerto", headers=auth_headers_admin)

        assert response.status_code == 422

    @pytest.mark.parametrize("limit", [0, -1, 5001])
    def test_rechaza_limites_fuera_de_rango(
        self, client: TestClient, auth_headers_admin: dict, limit: int
    ):
        response = client.get(f"{ENDPOINT}?limit={limit}", headers=auth_headers_admin)

        assert response.status_code == 422


# ==========================================
# Mapeo de capas (lógica pura)
# ==========================================

@pytest.mark.unit
class TestMapeoDeCapas:

    def test_toda_capa_declara_al_menos_una_categoria_de_origen(self):
        for layer, sources in LAYER_TO_SOURCE_CATEGORIES.items():
            assert sources, f"La capa {layer} no mapea ninguna categoría de origen"

    def test_estan_las_cuatro_capas_de_riesgo(self):
        assert set(LAYER_TO_SOURCE_CATEGORIES.keys()) == {
            POILayerCategoryEnum.SCHOOL,
            POILayerCategoryEnum.HOSPITAL,
            POILayerCategoryEnum.FIRE_STATION,
            POILayerCategoryEnum.COMMUNITY_CENTER,
        }

    def test_ninguna_categoria_de_origen_se_repite_entre_capas(self):
        """
        Si una categoría cayera en dos capas, el mismo POI aparecería duplicado
        en el mapa y contaría dos veces en el score de proximidad.
        """
        vistas: list[POICategory] = []
        for sources in LAYER_TO_SOURCE_CATEGORIES.values():
            vistas.extend(sources)

        assert len(vistas) == len(set(vistas))

    def test_el_indice_inverso_es_coherente_con_el_directo(self):
        for layer, sources in LAYER_TO_SOURCE_CATEGORIES.items():
            for source in sources:
                assert SOURCE_TO_LAYER_CATEGORY[source] == layer

    def test_escuelas_y_universidades_van_a_la_capa_escolar(self):
        assert SOURCE_TO_LAYER_CATEGORY[POICategory.SCHOOL] == POILayerCategoryEnum.SCHOOL
        assert SOURCE_TO_LAYER_CATEGORY[POICategory.UNIVERSITY] == POILayerCategoryEnum.SCHOOL

    def test_hospitales_y_clinicas_van_a_la_capa_sanitaria(self):
        assert SOURCE_TO_LAYER_CATEGORY[POICategory.HOSPITAL] == POILayerCategoryEnum.HOSPITAL
        assert SOURCE_TO_LAYER_CATEGORY[POICategory.CLINIC] == POILayerCategoryEnum.HOSPITAL


# ==========================================
# Buffers recomendados
# ==========================================

@pytest.mark.unit
class TestBuffersRecomendados:

    def test_toda_capa_tiene_buffer_definido(self):
        assert set(RECOMMENDED_BUFFER_BY_LAYER.keys()) == set(LAYER_TO_SOURCE_CATEGORIES.keys())

    def test_los_buffers_estan_en_el_rango_documentado(self):
        """La documentación del endpoint promete buffers de 50 a 200 metros."""
        for layer, buffer_m in RECOMMENDED_BUFFER_BY_LAYER.items():
            assert 50 <= buffer_m <= 200, f"{layer} tiene un buffer fuera de rango: {buffer_m}"

    def test_los_bomberos_tienen_el_buffer_mas_amplio(self):
        assert RECOMMENDED_BUFFER_BY_LAYER[POILayerCategoryEnum.FIRE_STATION] == max(
            RECOMMENDED_BUFFER_BY_LAYER.values()
        )
