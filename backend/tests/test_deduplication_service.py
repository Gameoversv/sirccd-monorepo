"""
Tests del servicio de deduplicación (services/deduplication_service.py).

462 statements en 0%: el módulo más grande del backend y el núcleo del
producto — decide si dos fotos son el mismo bache. Un fallo aquí no da error:
fusiona reportes distintos o deja pasar duplicados, en silencio.

Igual que `test_queue_service.py`, el módulo se carga bajo otro nombre porque
`conftest.py` lo sustituye por un MagicMock en `sys.modules`.

Todo corre offline: se usa el backend de histograma (OpenCV + numpy), nunca
ResNet ni CLIP, así que ningún test descarga pesos ni necesita GPU.
"""

import importlib.util
import math
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image


def _load_real_dedup_service():
    ruta = Path(__file__).resolve().parent.parent / "services" / "deduplication_service.py"
    spec = importlib.util.spec_from_file_location("deduplication_service_real", ruta)
    modulo = importlib.util.module_from_spec(spec)
    # `@dataclass` resuelve las anotaciones buscando el módulo por su nombre en
    # sys.modules, así que hay que registrarlo antes de ejecutarlo. Se registra
    # bajo el alias, no bajo 'services.deduplication_service': esa entrada
    # sigue siendo el MagicMock que necesita el resto de la suite.
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


ds = _load_real_dedup_service()


@pytest.fixture
def service(tmp_path):
    """
    Servicio con backend de histograma y un índice en carpeta temporal.

    `histogram` no descarga nada; `index_path` en tmp evita tocar
    `storage/faiss_index.bin` del repositorio.
    """
    return ds.DeduplicationService(
        db=MagicMock(),
        visual_model="histogram",
        index_path=str(tmp_path / "index.bin"),
    )


def imagen(color=(255, 0, 0), size=(64, 64)) -> Image.Image:
    return Image.new("RGB", size, color)


# ==========================================
# Helpers numéricos
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestHelpersNumericos:

    def test_safe_div_evita_la_division_por_cero(self):
        assert ds._safe_div(10, 0) == 0.0
        assert ds._safe_div(10, 4) == 2.5

    def test_l2_normalize_deja_norma_unitaria(self):
        vec = ds._l2_normalize(np.array([3.0, 4.0]))

        assert float(np.linalg.norm(vec)) == pytest.approx(1.0)

    def test_l2_normalize_tolera_el_vector_cero(self):
        vec = ds._l2_normalize(np.zeros(4))

        assert not np.isnan(vec).any()
        assert float(np.linalg.norm(vec)) == 0.0

    def test_coseno_de_vectores_identicos_es_uno(self):
        v = np.array([1.0, 2.0, 3.0])

        assert ds._cosine_similarity(v, v) == pytest.approx(1.0)

    def test_coseno_de_vectores_ortogonales_es_cero(self):
        assert ds._cosine_similarity(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)

    def test_el_coseno_no_depende_de_la_escala(self):
        a = np.array([1.0, 2.0])
        b = np.array([10.0, 20.0])

        assert ds._cosine_similarity(a, b) == pytest.approx(1.0)


# ==========================================
# Similitud de texto
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestSimilitudDeTexto:

    def test_textos_identicos_dan_uno(self):
        assert ds._text_similarity("bache grande", "bache grande") == pytest.approx(1.0)

    def test_ignora_mayusculas_y_espacios_sobrantes(self):
        assert ds._text_similarity("  Bache Grande ", "bache grande") == pytest.approx(1.0)

    @pytest.mark.parametrize("a,b", [(None, "x"), ("x", None), ("", "x"), ("x", "")])
    def test_sin_texto_devuelve_cero(self, a, b):
        assert ds._text_similarity(a, b) == 0.0

    def test_textos_parecidos_puntuan_mas_que_distintos(self):
        parecidos = ds._text_similarity("bache en la calle", "bache en la avenida")
        distintos = ds._text_similarity("bache en la calle", "semáforo roto")

        assert parecidos > distintos


# ==========================================
# Alias de modelos
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestModelAlias:

    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("resnet", "resnet50"),
            ("RESNET50", "resnet50"),
            ("  mobilenet  ", "mobilenet_v2"),
            ("clip", "clip-vit-base-patch32"),
            ("hist", "histogram"),
        ],
    )
    def test_normaliza_los_nombres_conocidos(self, entrada, esperado):
        assert ds._model_alias(entrada) == esperado

    def test_un_modelo_desconocido_falla_explicitamente(self):
        with pytest.raises(ValueError, match="no soportado"):
            ds._model_alias("modelo-inventado")


# ==========================================
# Distancia geográfica
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestHaversine:

    def test_el_mismo_punto_da_cero(self):
        assert ds.haversine_distance(19.45, -70.69, 19.45, -70.69) == pytest.approx(0.0)

    def test_un_grado_de_latitud_son_unos_111_km(self):
        distancia = ds.haversine_distance(19.0, -70.69, 20.0, -70.69)

        assert distancia == pytest.approx(111_195, rel=0.01)

    def test_es_simetrica(self):
        ida = ds.haversine_distance(19.45, -70.69, 19.46, -70.70)
        vuelta = ds.haversine_distance(19.46, -70.70, 19.45, -70.69)

        assert ida == pytest.approx(vuelta)

    def test_distancia_corta_realista_en_metros(self):
        """~0.0001 grados son unos 11 m: la escala del umbral de duplicados."""
        distancia = ds.haversine_distance(19.4500, -70.6900, 19.4501, -70.6900)

        assert 10 < distancia < 12


# ==========================================
# FAISSIndex
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestFaissIndex:

    def test_buscar_en_un_indice_vacio_no_falla(self):
        index = ds.FAISSIndex(embedding_dim=4)

        distancias, ids = index.search(np.zeros(4, dtype="float32"))

        assert len(distancias) == 0
        assert ids == []

    def test_encuentra_el_vecino_mas_cercano(self):
        index = ds.FAISSIndex(embedding_dim=2)
        index.add(np.array([[0.0, 0.0], [10.0, 10.0]], dtype="float32"), [101, 202])

        _, ids = index.search(np.array([0.1, 0.1], dtype="float32"), k=1)

        assert ids == [101]

    def test_devuelve_los_ids_ordenados_por_cercania(self):
        index = ds.FAISSIndex(embedding_dim=2)
        index.add(
            np.array([[0.0, 0.0], [1.0, 1.0], [9.0, 9.0]], dtype="float32"), [1, 2, 3]
        )

        _, ids = index.search(np.array([0.0, 0.0], dtype="float32"), k=3)

        assert ids == [1, 2, 3]

    def test_k_se_recorta_al_tamano_del_indice(self):
        index = ds.FAISSIndex(embedding_dim=2)
        index.add(np.array([[0.0, 0.0]], dtype="float32"), [7])

        _, ids = index.search(np.array([0.0, 0.0], dtype="float32"), k=50)

        assert ids == [7]

    def test_rechaza_ids_y_embeddings_descuadrados(self):
        index = ds.FAISSIndex(embedding_dim=2)

        with pytest.raises(ValueError, match="no coincide"):
            index.add(np.array([[0.0, 0.0], [1.0, 1.0]], dtype="float32"), [1])

    def test_clear_vacia_el_indice_y_el_mapa_de_ids(self):
        index = ds.FAISSIndex(embedding_dim=2)
        index.add(np.array([[0.0, 0.0]], dtype="float32"), [1])

        index.clear()

        assert index.index.ntotal == 0
        assert index.id_map == []

    def test_un_tipo_de_indice_desconocido_falla(self):
        with pytest.raises(ValueError, match="no soportado"):
            ds.FAISSIndex(embedding_dim=2, index_type="COSENO")

    def test_guardar_y_recargar_conserva_los_ids(self, tmp_path):
        ruta = str(tmp_path / "idx.bin")
        original = ds.FAISSIndex(embedding_dim=2)
        original.add(np.array([[1.0, 1.0], [5.0, 5.0]], dtype="float32"), [11, 22])
        original.save(ruta)

        recargado = ds.FAISSIndex(embedding_dim=2)
        recargado.load(ruta)

        assert recargado.id_map == [11, 22]
        _, ids = recargado.search(np.array([1.0, 1.0], dtype="float32"), k=1)
        assert ids == [11]


# ==========================================
# VisualEmbedder (backend histograma, sin descargas)
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestVisualEmbedderHistograma:

    def test_el_embedding_tiene_la_dimension_declarada(self):
        embedder = ds.VisualEmbedder(model_name="histogram")

        vector = embedder.embed(imagen())

        assert vector.shape == (embedder.embedding_dim,)

    def test_es_determinista(self):
        embedder = ds.VisualEmbedder(model_name="histogram")

        primero = embedder.embed(imagen((0, 128, 255)))
        segundo = embedder.embed(imagen((0, 128, 255)))

        assert np.allclose(primero, segundo)

    def test_la_misma_imagen_puntua_por_encima_de_una_distinta(self):
        """
        Se comparan la imagen consigo misma y contra otra: con colores planos,
        el histograma cuantiza en bins, así que dos rojos casi iguales pueden
        caer en bins distintos y dar similitud 0. Eso es propio del fallback de
        histograma, no del pipeline real (ResNet/CLIP).
        """
        embedder = ds.VisualEmbedder(model_name="histogram")

        rojo = embedder.embed(imagen((255, 0, 0)))
        mismo_rojo = embedder.embed(imagen((255, 0, 0)))
        azul = embedder.embed(imagen((0, 0, 255)))

        assert ds._cosine_similarity(rojo, mismo_rojo) == pytest.approx(1.0)
        assert ds._cosine_similarity(rojo, mismo_rojo) > ds._cosine_similarity(rojo, azul)

    def test_embed_batch_devuelve_una_fila_por_imagen(self):
        embedder = ds.VisualEmbedder(model_name="histogram")

        matriz = embedder.embed_batch([imagen((255, 0, 0)), imagen((0, 255, 0))])

        assert matriz.shape == (2, embedder.embedding_dim)


# ==========================================
# Conversión distancia -> similitud
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestSimilitudes:

    def test_distancia_cero_es_similitud_maxima(self, service):
        assert service._distance_to_similarity(0.0) == pytest.approx(1.0)

    def test_la_similitud_nunca_es_negativa(self, service):
        assert service._distance_to_similarity(99.0) == 0.0

    def test_la_similitud_decrece_con_la_distancia(self, service):
        cerca = service._distance_to_similarity(0.2)
        lejos = service._distance_to_similarity(1.5)

        assert cerca > lejos

    def test_geo_similitud_en_el_mismo_punto_es_uno(self, service):
        assert service._geo_similarity(0.0, 50.0) == pytest.approx(1.0)

    def test_geo_similitud_decae_exponencialmente(self, service):
        assert service._geo_similarity(50.0, 50.0) == pytest.approx(math.exp(-1), rel=1e-6)

    def test_geo_similitud_tolera_umbral_cero(self, service):
        """El umbral se acota a 1 m para no dividir por cero."""
        assert service._geo_similarity(1.0, 0.0) == pytest.approx(math.exp(-1), rel=1e-6)


# ==========================================
# Score fusionado
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestFusionScore:

    def test_con_un_solo_modelo_el_score_maximo_es_075(self, service):
        """
        Comportamiento a vigilar: el peso del modelo secundario (0.25) sigue
        contando en el denominador aunque no haya modelo secundario, así que
        una coincidencia perfecta llega como mucho a 0.75.

        En producción no muerde porque se configuran dos modelos (resnet50 +
        clip). Pero si `DEDUPLICATION_SECONDARY_MODEL` se deja vacío, el techo
        queda en 0.75 frente a un umbral de 0.72: sobreviven solo 3 centésimas
        de margen para declarar un duplicado.
        """
        score = service._fusion_score(
            model_similarities={service.primary_model: 1.0},
            geo_similarity=1.0,
            text_similarity=1.0,
        )

        assert score == pytest.approx(0.75)
        assert score > service.FUSION_SCORE_THRESHOLD

    def test_con_dos_modelos_una_coincidencia_perfecta_da_uno(self, service):
        # Se declara el modelo secundario sin instanciarlo: construir uno real
        # (resnet50/clip) descargaría pesos, y `_fusion_score` solo lee el
        # nombre y los pesos.
        service.secondary_model = "modelo_secundario"

        score = service._fusion_score(
            model_similarities={service.primary_model: 1.0, "modelo_secundario": 1.0},
            geo_similarity=1.0,
            text_similarity=1.0,
        )

        assert score == pytest.approx(1.0)

    def test_todo_nulo_da_cero(self, service):
        score = service._fusion_score(
            model_similarities={service.primary_model: 0.0},
            geo_similarity=0.0,
            text_similarity=0.0,
        )

        assert score == 0.0

    def test_el_score_siempre_queda_en_0_1(self, service):
        score = service._fusion_score(
            model_similarities={service.primary_model: 99.0},
            geo_similarity=99.0,
            text_similarity=99.0,
        )

        assert 0.0 <= score <= 1.0

    def test_un_modelo_ausente_cuenta_como_cero_y_no_revienta(self, service):
        score = service._fusion_score(
            model_similarities={},
            geo_similarity=1.0,
            text_similarity=1.0,
        )

        assert 0.0 <= score < 1.0

    def test_mas_similitud_visual_nunca_baja_el_score(self, service):
        bajo = service._fusion_score({service.primary_model: 0.1}, 0.5, 0.5)
        alto = service._fusion_score({service.primary_model: 0.9}, 0.5, 0.5)

        assert alto > bajo

    def test_la_cercania_geografica_sube_el_score(self, service):
        lejos = service._fusion_score({service.primary_model: 0.5}, 0.0, 0.5)
        cerca = service._fusion_score({service.primary_model: 0.5}, 1.0, 0.5)

        assert cerca > lejos

    def test_lo_visual_pesa_mas_que_el_texto(self, service):
        """
        Dos fotos iguales con descripciones distintas deben puntuar más que dos
        fotos distintas con la misma descripción.
        """
        visual = service._fusion_score({service.primary_model: 1.0}, 0.5, 0.0)
        textual = service._fusion_score({service.primary_model: 0.0}, 0.5, 1.0)

        assert visual > textual


# ==========================================
# Configuración del servicio
# ==========================================

@pytest.mark.unit
@pytest.mark.ml
class TestConfiguracionDelServicio:

    def test_registra_un_embedder_y_un_indice_por_modelo(self, tmp_path):
        service = ds.DeduplicationService(
            db=MagicMock(),
            visual_model="histogram",
            index_path=str(tmp_path / "i.bin"),
        )

        assert set(service.embedders.keys()) == {"histogram"}
        assert set(service.indexes.keys()) == {"histogram"}

    def test_el_modelo_secundario_repetido_no_se_duplica(self, tmp_path):
        service = ds.DeduplicationService(
            db=MagicMock(),
            visual_model="histogram",
            secondary_visual_model="hist",
            index_path=str(tmp_path / "i.bin"),
        )

        assert service.models == ["histogram"]

    def test_el_modelo_invalido_falla_al_construir(self, tmp_path):
        with pytest.raises(ValueError):
            ds.DeduplicationService(
                db=MagicMock(),
                visual_model="no-existe",
                index_path=str(tmp_path / "i.bin"),
            )

    def test_la_ruta_del_indice_se_sanea_por_modelo(self, service):
        ruta = service._model_index_path("clip-vit-base-patch32")

        assert "clip_vit_base_patch32" in ruta
        assert " " not in ruta

    def test_los_umbrales_son_valores_utilizables(self, service):
        assert 0.0 < service.FUSION_SCORE_THRESHOLD <= 1.0
        assert service.GEO_DISTANCE_THRESHOLD > 0
        assert service.TIME_WINDOW_DAYS > 0
