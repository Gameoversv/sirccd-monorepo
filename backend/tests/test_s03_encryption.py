"""
Tests S-03 — Cifrado en tránsito y en reposo.

Cubre:
- EncryptedString TypeDecorator: cifra en bind, descifra en result
- Graceful fallback cuando FIELD_ENCRYPTION_KEY no está configurada
- Cifrado de User.phone en DB
- MinIO SSE: put_object recibe sse=SseS3() cuando MINIO_SSE_ENABLED=True
- MinIO SSE: no se pasa sse cuando MINIO_SSE_ENABLED=False
- Bucket privado: minio-init ya no usa mc anonymous set public
"""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EncryptedString TypeDecorator
# ═══════════════════════════════════════════════════════════════════════════════

class TestEncryptedString:
    """Verifica el ciclo cifrado/descifrado del TypeDecorator."""

    def _make_fernet_key(self) -> str:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()

    def _reset_fernet(self):
        import core.field_encryption as fe
        fe._fernet_instance = None
        fe._encryption_warned = False

    def test_encrypt_decrypt_roundtrip(self):
        """Cifrar y descifrar produce el valor original."""
        import core.field_encryption as fe
        self._reset_fernet()

        key = self._make_fernet_key()
        # settings es atributo de módulo en field_encryption.py → parcheable
        with patch.object(fe.settings, 'FIELD_ENCRYPTION_KEY', key):
            original = "829-555-1234"
            encrypted = fe.encrypt_value(original)
            assert encrypted != original
            decrypted = fe.decrypt_value(encrypted)
            assert decrypted == original

        self._reset_fernet()

    def test_encrypt_produces_different_ciphertext_each_time(self):
        """Fernet usa IV aleatorio — mismo plaintext produce distinto ciphertext."""
        from cryptography.fernet import Fernet
        import core.field_encryption as fe
        self._reset_fernet()

        key = self._make_fernet_key()
        fernet = Fernet(key.encode())

        c1 = fernet.encrypt(b"829-555-0000").decode()
        c2 = fernet.encrypt(b"829-555-0000").decode()
        assert c1 != c2  # IV aleatorio garantiza esto

        self._reset_fernet()

    def test_no_key_returns_plaintext(self):
        """Sin clave, encrypt_value retorna el valor sin modificar."""
        import core.field_encryption as fe
        self._reset_fernet()

        with patch.object(fe.settings, 'FIELD_ENCRYPTION_KEY', None):
            value = "sin-cifrar"
            result = fe.encrypt_value(value)

        assert result == value
        self._reset_fernet()

    def test_decrypt_invalid_token_returns_value(self):
        """
        Descifrar un valor en texto plano (migración gradual) no lanza excepción.
        Retorna el valor tal cual.
        """
        import core.field_encryption as fe
        self._reset_fernet()

        key = self._make_fernet_key()
        with patch.object(fe.settings, 'FIELD_ENCRYPTION_KEY', key):
            plaintext_in_db = "829-555-legado"
            result = fe.decrypt_value(plaintext_in_db)

        assert result == plaintext_in_db
        self._reset_fernet()

    def test_encrypted_string_type_decorator_bind(self):
        """process_bind_param cifra el valor antes de insertar en BD."""
        import core.field_encryption as fe
        from core.field_encryption import EncryptedString
        self._reset_fernet()

        key = self._make_fernet_key()
        with patch.object(fe.settings, 'FIELD_ENCRYPTION_KEY', key):
            enc_type = EncryptedString(200)
            bound = enc_type.process_bind_param("829-000-1111", dialect=None)

        assert bound != "829-000-1111"
        assert bound is not None
        self._reset_fernet()

    def test_encrypted_string_type_decorator_result(self):
        """process_result_value descifra el valor al leer de BD."""
        import core.field_encryption as fe
        from core.field_encryption import EncryptedString
        from cryptography.fernet import Fernet
        self._reset_fernet()

        key = self._make_fernet_key()
        fernet = Fernet(key.encode())
        ciphertext = fernet.encrypt(b"829-111-2222").decode()

        with patch.object(fe.settings, 'FIELD_ENCRYPTION_KEY', key):
            enc_type = EncryptedString(200)
            result = enc_type.process_result_value(ciphertext, dialect=None)

        assert result == "829-111-2222"
        self._reset_fernet()

    def test_none_values_passthrough(self):
        """None en bind y result se propaga sin error (campo nullable)."""
        from core.field_encryption import EncryptedString

        enc_type = EncryptedString(200)
        assert enc_type.process_bind_param(None, dialect=None) is None
        assert enc_type.process_result_value(None, dialect=None) is None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. User.phone usa EncryptedString
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserPhoneEncrypted:
    """Verifica que User.phone es del tipo EncryptedString."""

    def test_user_phone_column_uses_encrypted_type(self):
        """La columna phone del modelo User es EncryptedString."""
        from models.user import User
        from core.field_encryption import EncryptedString

        phone_col = User.__table__.c.phone
        assert isinstance(phone_col.type, EncryptedString), (
            f"phone debería ser EncryptedString, es {type(phone_col.type)}"
        )

    def test_phone_column_underlying_impl_is_string(self):
        """EncryptedString implementa sobre String (compatible con todas las BDs)."""
        from models.user import User
        from sqlalchemy import String

        phone_col = User.__table__.c.phone
        assert isinstance(phone_col.type.impl, String)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MinIO SSE-S3 en upload
# ═══════════════════════════════════════════════════════════════════════════════

class TestMinioSSE:
    """Verifica que SSE-S3 se pasa a put_object cuando MINIO_SSE_ENABLED=True."""

    def _load_real_storage(self):
        """
        Carga el módulo real services.storage ignorando el mock del conftest.
        El conftest reemplaza sys.modules['services.storage'] con MagicMock;
        aquí lo cargamos directamente para probar el código real.
        """
        import sys
        import importlib.util
        from pathlib import Path

        spec_path = Path(__file__).parent.parent / "services" / "storage.py"
        spec = importlib.util.spec_from_file_location("services.storage_real", spec_path)
        module = importlib.util.module_from_spec(spec)
        # Inyectar dependencias mockeadas para que el módulo cargue sin error
        sys.modules.setdefault('services.anonymizer', MagicMock())
        sys.modules.setdefault('services.exif_service', MagicMock())
        spec.loader.exec_module(module)
        return module

    @pytest.mark.asyncio
    async def test_sse_passed_when_enabled(self):
        """Con MINIO_SSE_ENABLED=True, put_object recibe un argumento sse no-None."""
        storage_module = self._load_real_storage()
        StorageService = storage_module.StorageService

        mock_client = MagicMock()

        with patch.object(storage_module.settings, 'MINIO_BUCKET_IMAGES', "sirccd-images"), \
             patch.object(storage_module.settings, 'MINIO_SECURE', False), \
             patch.object(storage_module.settings, 'MINIO_SSE_ENABLED', True):

            svc = StorageService.__new__(StorageService)
            svc.use_minio = True
            svc.client = mock_client

            await svc._upload_to_minio("reports/test.jpg", b"bytes", "image/jpeg")

        call_kwargs = mock_client.put_object.call_args
        sse_arg = call_kwargs.kwargs.get("sse")
        # Con SSE habilitado, sse debe ser una instancia de SseS3 (no None)
        assert sse_arg is not None, "put_object debe recibir sse != None cuando SSE está habilitado"
        assert "SseS3" in type(sse_arg).__name__, (
            f"Se esperaba SseS3, se recibió {type(sse_arg).__name__}"
        )

    @pytest.mark.asyncio
    async def test_no_sse_when_disabled(self):
        """Con MINIO_SSE_ENABLED=False, put_object recibe sse=None."""
        storage_module = self._load_real_storage()
        StorageService = storage_module.StorageService

        mock_client = MagicMock()

        with patch.object(storage_module.settings, 'MINIO_BUCKET_IMAGES', "sirccd-images"), \
             patch.object(storage_module.settings, 'MINIO_SECURE', False), \
             patch.object(storage_module.settings, 'MINIO_SSE_ENABLED', False):

            svc = StorageService.__new__(StorageService)
            svc.use_minio = True
            svc.client = mock_client

            await svc._upload_to_minio("reports/test.jpg", b"bytes", "image/jpeg")

        call_kwargs = mock_client.put_object.call_args
        sse_arg = call_kwargs.kwargs.get("sse")
        assert sse_arg is None, f"Sin SSE se esperaba sse=None, se recibió {sse_arg}"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Config — nuevas variables S-03 presentes
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfigS03:
    """Verifica que las variables S-03 existen en Settings con defaults seguros."""

    def test_minio_sse_enabled_default_false(self):
        """MINIO_SSE_ENABLED por defecto es False (evitar romper dev sin config)."""
        from core.config import Settings
        s = Settings()
        assert s.MINIO_SSE_ENABLED is False

    def test_field_encryption_key_default_none(self):
        """FIELD_ENCRYPTION_KEY por defecto es None (dev sin cifrado)."""
        from core.config import Settings
        s = Settings()
        assert s.FIELD_ENCRYPTION_KEY is None

    def test_redis_password_default_none(self):
        """REDIS_PASSWORD por defecto es None (dev sin auth)."""
        from core.config import Settings
        s = Settings()
        assert s.REDIS_PASSWORD is None

    def test_minio_sse_enabled_via_env(self):
        """MINIO_SSE_ENABLED se puede activar via variable de entorno."""
        with patch.dict(os.environ, {"MINIO_SSE_ENABLED": "True"}):
            from core.config import Settings
            s = Settings()
            assert s.MINIO_SSE_ENABLED is True

    def test_field_encryption_key_via_env(self):
        """FIELD_ENCRYPTION_KEY se puede inyectar via variable de entorno."""
        fake_key = "test-fernet-key-value"
        with patch.dict(os.environ, {"FIELD_ENCRYPTION_KEY": fake_key}):
            from core.config import Settings
            s = Settings()
            assert s.FIELD_ENCRYPTION_KEY == fake_key


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Bucket privado — docker-compose.yml no usa mc anonymous set public
# ═══════════════════════════════════════════════════════════════════════════════

class TestBucketNotPublic:
    """Verifica que el compose de dev no configura bucket público."""

    def test_minio_init_no_public_access_in_dev_compose(self):
        """docker-compose.yml no debe contener 'mc anonymous set public'."""
        import re
        compose_path = (
            __file__
            .replace("backend/tests/test_s03_encryption.py", "docker-compose.yml")
            .replace("backend\\tests\\test_s03_encryption.py", "docker-compose.yml")
        )
        with open(compose_path, "r") as f:
            content = f.read()

        assert "mc anonymous set public" not in content, (
            "docker-compose.yml no debe configurar acceso anónimo público al bucket"
        )

    def test_prod_compose_no_public_access(self):
        """docker-compose.prod.yml tampoco debe tener bucket público."""
        compose_path = (
            __file__
            .replace("backend/tests/test_s03_encryption.py", "docker-compose.prod.yml")
            .replace("backend\\tests\\test_s03_encryption.py", "docker-compose.prod.yml")
        )
        with open(compose_path, "r") as f:
            content = f.read()

        assert "mc anonymous set public" not in content

    def test_prod_compose_enables_sse(self):
        """docker-compose.prod.yml habilita MINIO_SSE_ENABLED=True."""
        compose_path = (
            __file__
            .replace("backend/tests/test_s03_encryption.py", "docker-compose.prod.yml")
            .replace("backend\\tests\\test_s03_encryption.py", "docker-compose.prod.yml")
        )
        with open(compose_path, "r") as f:
            content = f.read()

        assert "MINIO_SSE_ENABLED" in content
        assert 'MINIO_SSE_ENABLED: "True"' in content

    def test_prod_compose_uses_field_encryption_key(self):
        """docker-compose.prod.yml inyecta FIELD_ENCRYPTION_KEY."""
        compose_path = (
            __file__
            .replace("backend/tests/test_s03_encryption.py", "docker-compose.prod.yml")
            .replace("backend\\tests\\test_s03_encryption.py", "docker-compose.prod.yml")
        )
        with open(compose_path, "r") as f:
            content = f.read()

        assert "FIELD_ENCRYPTION_KEY" in content

    def test_prod_compose_redis_has_password(self):
        """docker-compose.prod.yml configura Redis con --requirepass."""
        compose_path = (
            __file__
            .replace("backend/tests/test_s03_encryption.py", "docker-compose.prod.yml")
            .replace("backend\\tests\\test_s03_encryption.py", "docker-compose.prod.yml")
        )
        with open(compose_path, "r") as f:
            content = f.read()

        assert "--requirepass" in content

    def test_nginx_conf_uses_tls12_plus(self):
        """nginx.conf solo permite TLS 1.2 y 1.3."""
        nginx_path = (
            __file__
            .replace("backend/tests/test_s03_encryption.py", "infra/nginx/nginx.conf")
            .replace("backend\\tests\\test_s03_encryption.py", "infra\\nginx\\nginx.conf")
        )
        with open(nginx_path, "r") as f:
            content = f.read()

        assert "TLSv1.2" in content
        assert "TLSv1.3" in content
        assert "TLSv1.0" not in content
        assert "TLSv1.1" not in content
        assert "ssl_certificate" in content
        assert "Strict-Transport-Security" in content
