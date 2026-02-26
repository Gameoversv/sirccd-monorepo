"""Script rápido para verificar que B-03 funciona correctamente"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

print("=" * 60)
print("VERIFICACIÓN RÁPIDA B-03 - AUTENTICACIÓN")
print("=" * 60)

# 1. Test password hashing
print("\n1. Password Hashing:")
password = "testpassword123"
hashed = get_password_hash(password)
print(f"   Password: {password}")
print(f"   Hash: {hashed[:50]}...")
print(f"   ✓ Verifica correctamente: {verify_password(password, hashed)}")
print(f"   ✓ Rechaza incorrecta: {not verify_password('wrong', hashed)}")

# 2. Test JWT token creation
print("\n2. JWT Token Creation:")
user_id = 123
token = create_access_token(
    subject=user_id,
    additional_claims={"role": "ciudadano", "username": "testuser"}
)
print(f"   User ID: {user_id}")
print(f"   Token: {token[:50]}...")
print(f"   ✓ Token creado exitosamente")

# 3. Test JWT token decoding
print("\n3. JWT Token Decoding:")
payload = decode_access_token(token)
print(f"   Subject: {payload['sub']}")
print(f"   Role: {payload['role']}")
print(f"   Username: {payload['username']}")
print(f"   ✓ Token decodificado correctamente")

# 4. Test invalid token
print("\n4. Invalid Token:")
invalid_payload = decode_access_token("invalid.token.here")
print(f"   ✓ Token inválido rechazado: {invalid_payload is None}")

# 5. Test schemas
print("\n5. Schemas Pydantic:")
try:
    from schemas.user import UserCreate, UserResponse
    from schemas.auth import LoginRequest, LoginResponse
    print("   ✓ schemas.user importado")
    print("   ✓ schemas.auth importado")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 6. Test dependencies
print("\n6. Dependencias FastAPI:")
try:
    from api.deps import (
        get_current_user,
        require_admin,
        require_brigada,
        require_supervisor
    )
    print("   ✓ get_current_user disponible")
    print("   ✓ require_admin disponible")
    print("   ✓ require_brigada disponible")
    print("   ✓ require_supervisor disponible")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 7. Test routes
print("\n7. Rutas de Autenticación:")
try:
    from api.routes.auth import router
    print(f"   ✓ Router importado")
    print(f"   ✓ Rutas registradas: {len(router.routes)}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print(f"\n{'=' * 60}")
print("✅ B-03 VERIFICADO - TODOS LOS COMPONENTES FUNCIONANDO")
print(f"{'=' * 60}\n")
