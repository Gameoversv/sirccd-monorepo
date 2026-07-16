"""
Tests del proxy de imágenes: firma HMAC y lectura desde storage.

El bucket de MinIO es privado, así que las imágenes se sirven por
`/{scope}/{id}/image`. Estos tests cubren las dos piezas que no dependen de
PostGIS: la firma de las URLs y la lectura de bytes.
"""

import importlib.util
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from core.image_tokens import sign_image_url, verify_image_signature


def _load_real_storage_module():
    """
    Carga services/storage.py de verdad.

    conftest reemplaza `services.storage` por un MagicMock para el resto de la
    suite; aquí hace falta el código real, así que se carga bajo otro nombre
    para no alterar ese mock global.
    """
    path = Path(__file__).resolve().parents[1] / "services" / "storage.py"
    spec = importlib.util.spec_from_file_location("_real_services_storage", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


StorageService = _load_real_storage_module().StorageService


def _parse(url: str) -> tuple[int, str]:
    """Extrae (exp, sig) de una URL firmada."""
    query = parse_qs(urlparse(url).query)
    return int(query["exp"][0]), query["sig"][0]


@pytest.mark.unit
class TestImageSignature:
    def test_signed_url_points_to_the_proxy_endpoint(self):
        # Arrange / Act
        url = sign_image_url("reportes", 12, "original")

        # Assert
        assert urlparse(url).path == "/api/v1/reportes/12/image"

    def test_accepts_its_own_signature(self):
        # Arrange
        url = sign_image_url("reportes", 12, "original")
        exp, sig = _parse(url)

        # Act / Assert
        assert verify_image_signature("reportes", 12, "original", exp, sig) is True

    def test_rejects_signature_reused_for_another_report(self):
        # Arrange
        exp, sig = _parse(sign_image_url("reportes", 12, "original"))

        # Act / Assert
        assert verify_image_signature("reportes", 13, "original", exp, sig) is False

    def test_rejects_signature_reused_across_scopes(self):
        # Arrange
        exp, sig = _parse(sign_image_url("reportes", 12, "original"))

        # Act / Assert
        assert verify_image_signature("incidents", 12, "original", exp, sig) is False

    def test_rejects_signature_reused_for_another_variant(self):
        # Arrange
        exp, sig = _parse(sign_image_url("reportes", 12, "original"))

        # Act / Assert
        assert verify_image_signature("reportes", 12, "annotated", exp, sig) is False

    def test_rejects_expired_signature(self):
        # Arrange: firma ya vencida
        url = sign_image_url("reportes", 12, "original", ttl_seconds=-1)
        exp, sig = _parse(url)

        # Act / Assert
        assert verify_image_signature("reportes", 12, "original", exp, sig) is False

    def test_rejects_extended_expiry_without_resigning(self):
        # Arrange: mover exp no basta, va dentro del HMAC
        url = sign_image_url("reportes", 12, "original")
        exp, sig = _parse(url)

        # Act / Assert
        assert verify_image_signature("reportes", 12, "original", exp + 86400, sig) is False

    @pytest.mark.parametrize(
        "exp,sig",
        [(None, "abc"), (1_900_000_000, None), (1_900_000_000, "")],
        ids=["sin_exp", "sin_sig", "sig_vacia"],
    )
    def test_rejects_missing_credentials(self, exp, sig):
        assert verify_image_signature("reportes", 12, "original", exp, sig) is False


@pytest.mark.integration
class TestImageEndpointAuth:
    """
    Puerta de entrada del proxy.

    El rechazo ocurre antes de tocar la BD, así que se puede probar sin las
    tablas PostGIS (que no existen en el SQLite de tests).
    """

    def test_rejects_request_without_token_or_signature(self, client):
        response = client.get("/api/v1/reportes/1/image")
        assert response.status_code == 401

    def test_rejects_forged_signature(self, client):
        response = client.get(
            "/api/v1/reportes/1/image",
            params={"variant": "original", "exp": 1_900_000_000, "sig": "no-es-valida"},
        )
        assert response.status_code == 401

    def test_rejects_signature_minted_for_another_report(self, client):
        # Arrange
        exp, sig = _parse(sign_image_url("reportes", 999, "original"))

        # Act
        response = client.get(
            "/api/v1/reportes/1/image",
            params={"variant": "original", "exp": exp, "sig": sig},
        )

        # Assert
        assert response.status_code == 401

    def test_rejects_unknown_variant(self, client):
        response = client.get("/api/v1/reportes/1/image", params={"variant": "../../etc"})
        assert response.status_code == 422

    def test_incident_image_rejects_request_without_credentials(self, client):
        response = client.get("/api/v1/incidents/1/image")
        assert response.status_code == 401


@pytest.mark.unit
class TestLocalImageRead:
    """Lectura del fallback local (cuando MinIO no está disponible)."""

    @pytest.fixture
    def storage(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            StorageService, "_check_minio_available", lambda self: False
        )
        return StorageService()

    def test_reads_a_stored_image(self, storage, tmp_path):
        # Arrange
        image = tmp_path / "storage" / "images" / "reports" / "a.jpg"
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"jpeg-bytes")

        # Act
        content = storage.read_image_bytes("/storage/images/reports/a.jpg")

        # Assert
        assert content == b"jpeg-bytes"

    def test_returns_none_when_file_is_missing(self, storage):
        assert storage.read_image_bytes("/storage/images/reports/nope.jpg") is None

    def test_returns_none_for_empty_url(self, storage):
        assert storage.read_image_bytes("") is None

    def test_rejects_path_traversal_outside_the_image_directory(self, storage, tmp_path):
        # Arrange: secreto fuera de storage/images
        secret = tmp_path / "secret.env"
        secret.write_bytes(b"SECRET_KEY=hunter2")

        # Act
        content = storage.read_image_bytes("/storage/images/../../secret.env")

        # Assert
        assert content is None

    def test_guesses_content_type_from_the_extension(self):
        assert StorageService.guess_content_type("/storage/images/a/b.png") == "image/png"
        assert StorageService.guess_content_type("http://minio:9000/b/c.jpg") == "image/jpeg"

    def test_falls_back_to_binary_content_type_when_unknown(self):
        assert (
            StorageService.guess_content_type("/storage/images/a/b")
            == "application/octet-stream"
        )
