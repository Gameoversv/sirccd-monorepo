# Guía de Pruebas para B-03: Autenticación JWT y RBAC

## 🧪 Cómo Probar el Sistema de Autenticación

### Prerrequisitos

1. **Base de datos iniciada**:
```bash
cd backend
docker-compose -f docker-compose.db.yml up -d
```

2. **Migraciones aplicadas**:
```bash
cd backend
alembic upgrade head
```

3. **Dependencias instaladas**:
```bash
cd backend
pip install -r requirements.txt
```

---

## ✅ Método 1: Swagger UI (Recomendado - Más Fácil)

### Paso 1: Iniciar el Servidor

```bash
cd backend
python start_server.py
```

O directamente con uvicorn:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 2: Abrir Swagger UI

Navegar a: **http://localhost:8000/docs**

### Paso 3: Probar Registro

1. Expandir `POST /api/v1/auth/register`
2. Click en **"Try it out"**
3. Modificar el JSON de ejemplo:
```json
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "SecurePass123!",
  "full_name": "Usuario de Prueba",
  "phone": "+18095551234"
}
```
4. Click en **"Execute"**
5. Ver respuesta (debe ser 201):
```json
{
  "message": "Usuario registrado exitosamente...",
  "user_id": 1,
  "username": "testuser",
  "email": "test@example.com"
}
```

### Paso 4: Probar Login

1. Expandir `POST /api/v1/auth/login`
2. Click en **"Try it out"**
3. Usar credenciales del paso anterior:
```json
{
  "username": "testuser",
  "password": "SecurePass123!"
}
```
4. Click en **"Execute"**
5. **COPIAR** el `access_token` de la respuesta

### Paso 5: Autenticarse en Swagger

1. Click en el botón **"Authorize"** (arriba a la derecha, ícono de candado)
2. Pegar el token copiado en el campo **"Value"**
3. Click en **"Authorize"**
4. Click en **"Close"**

### Paso 6: Probar Endpoint Protegido

1. Expandir `GET /api/v1/auth/me`
2. Click en **"Try it out"**
3. Click en **"Execute"**
4. Ver respuesta con tus datos:
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Usuario de Prueba",
  "role": "ciudadano",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-02T15:30:00"
}
```

---

## ✅ Método 2: cURL (Terminal)

### Registro:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "username": "curluser",
    "password": "CurlPass123!",
    "full_name": "Usuario cURL"
  }'
```

### Login y Guardar Token:
```bash
# PowerShell
$response = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login -Method POST -ContentType "application/json" -Body '{"username":"curluser","password":"CurlPass123!"}'
$token = $response.access_token
Write-Host "Token: $token"
```

```bash
# Bash/WSL
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"curluser","password":"CurlPass123!"}' \
  | grep -o '"access_token":"[^"]*"' \
  | cut -d'"' -f4)

echo "Token: $TOKEN"
```

### Usar Token en Peticiones:
```bash
# PowerShell
$headers = @{"Authorization" = "Bearer $token"}
Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/me -Headers $headers
```

```bash
# Bash/WSL
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Método 3: Python Script (Automatizado)

Crear archivo `test_auth_manual.py`:

```python
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_auth_flow():
    """Prueba completa del flujo de autenticación"""
    
    print("=" * 60)
    print("🧪 PROBANDO FLUJO DE AUTENTICACIÓN")
    print("=" * 60)
    
    # 1. Registro
    print("\n1️⃣  Registrando usuario...")
    register_data = {
        "email": "pythontest@example.com",
        "username": "pythonuser",
        "password": "PythonPass123!",
        "full_name": "Usuario Python"
    }
    
    response = httpx.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        user_data = response.json()
        print(f"   ✅ Usuario creado: {user_data['username']} (ID: {user_data['user_id']})")
    elif response.status_code == 400:
        print(f"   ⚠️  Usuario ya existe")
    else:
        print(f"   ❌ Error: {response.text}")
        return
    
    # 2. Login
    print("\n2️⃣  Iniciando sesión...")
    login_data = {
        "username": "pythonuser",
        "password": "PythonPass123!"
    }
    
    response = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Error en login: {response.text}")
        return
    
    login_response = response.json()
    token = login_response["access_token"]
    print(f"   ✅ Login exitoso")
    print(f"   Token: {token[:30]}...")
    print(f"   Rol: {login_response['role']}")
    print(f"   Expira en: {login_response['expires_in']} segundos")
    
    # 3. Obtener info del usuario
    print("\n3️⃣  Obteniendo información del usuario...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"   ✅ Usuario autenticado:")
        print(f"      ID: {user_info['id']}")
        print(f"      Username: {user_info['username']}")
        print(f"      Email: {user_info['email']}")
        print(f"      Rol: {user_info['role']}")
        print(f"      Activo: {user_info['is_active']}")
    else:
        print(f"   ❌ Error: {response.text}")
        return
    
    # 4. Verificar token
    print("\n4️⃣  Verificando validez del token...")
    response = httpx.post(f"{BASE_URL}/auth/verify-token", params={"token": token})
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        verification = response.json()
        if verification["valid"]:
            print(f"   ✅ Token válido")
            print(f"      User ID: {verification['user_id']}")
            print(f"      Rol: {verification['role']}")
        else:
            print(f"   ❌ Token inválido")
    
    # 5. Probar token inválido
    print("\n5️⃣  Probando con token inválido...")
    bad_headers = {"Authorization": "Bearer token_invalido"}
    response = httpx.get(f"{BASE_URL}/auth/me", headers=bad_headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"   ✅ Token inválido rechazado correctamente")
    else:
        print(f"   ❌ Debería haber rechazado el token")
    
    # 6. Logout
    print("\n6️⃣  Cerrando sesión...")
    response = httpx.post(f"{BASE_URL}/auth/logout", headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        logout_response = response.json()
        print(f"   ✅ {logout_response['message']}")
    
    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("=" * 60)

if __name__ == "__main__":
    test_auth_flow()
```

**Ejecutar**:
```bash
cd backend
python test_auth_manual.py
```

---

## ✅ Método 4: pytest (Tests Automatizados)

Crear archivo `tests/test_auth_integration.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    """Probar registro de usuario"""
    response = client.post("/api/v1/auth/register", json={
        "email": "pytest@example.com",
        "username": "pytestuser",
        "password": "PytestPass123!",
        "full_name": "Usuario Pytest"
    })
    
    assert response.status_code in [201, 400]  # 400 si ya existe
    if response.status_code == 201:
        data = response.json()
        assert "user_id" in data
        assert data["username"] == "pytestuser"

def test_login_success():
    """Probar login exitoso"""
    # Primero asegurar que el usuario existe
    client.post("/api/v1/auth/register", json={
        "email": "pytest@example.com",
        "username": "pytestuser",
        "password": "PytestPass123!"
    })
    
    # Login
    response = client.post("/api/v1/auth/login", json={
        "username": "pytestuser",
        "password": "PytestPass123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert data["role"] == "ciudadano"

def test_login_wrong_password():
    """Probar login con contraseña incorrecta"""
    response = client.post("/api/v1/auth/login", json={
        "username": "pytestuser",
        "password": "WrongPassword123!"
    })
    
    assert response.status_code == 401
    assert "incorrectas" in response.json()["detail"].lower()

def test_get_current_user():
    """Probar obtener usuario actual con token válido"""
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "username": "pytestuser",
        "password": "PytestPass123!"
    })
    token = login_response.json()["access_token"]
    
    # Obtener usuario
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "pytestuser"
    assert data["role"] == "ciudadano"

def test_protected_endpoint_without_token():
    """Probar endpoint protegido sin token"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401

def test_protected_endpoint_invalid_token():
    """Probar endpoint protegido con token inválido"""
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer token_invalido"
    })
    
    assert response.status_code == 401
```

**Ejecutar tests**:
```bash
cd backend
pytest tests/test_auth_integration.py -v
```

---

## ✅ Método 5: Verificar en Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it sirccd-postgres psql -U sirccd_user -d sirccd_db
```

```sql
-- Ver usuarios registrados
SELECT id, username, email, role, is_active, is_verified, created_at 
FROM users;

-- Ver último login
SELECT username, last_login 
FROM users 
ORDER BY last_login DESC;

-- Contar usuarios por rol
SELECT role, COUNT(*) 
FROM users 
GROUP BY role;
```

---

## 📋 Checklist de Pruebas

### Funcionalidad Básica:
- [ ] ✅ Registrar usuario nuevo
- [ ] ✅ Login con credenciales correctas
- [ ] ✅ Rechazar login con contraseña incorrecta
- [ ] ✅ Rechazar login con usuario inexistente
- [ ] ✅ Obtener info de usuario autenticado
- [ ] ✅ Rechazar acceso sin token
- [ ] ✅ Rechazar token inválido
- [ ] ✅ Rechazar token expirado (esperar 30+ min)

### RBAC (Control de Roles):
- [ ] ✅ Usuario CIUDADANO puede acceder a endpoints públicos
- [ ] ⚠️ Usuario CIUDADANO NO puede acceder a endpoints de admin
- [ ] ✅ Usuario ADMIN puede acceder a todos los endpoints
- [ ] ✅ Usuario BRIGADA puede actualizar incidentes
- [ ] ✅ Usuario SUPERVISOR puede ver reportes pendientes

### Edge Cases:
- [ ] ✅ Email duplicado rechazado en registro
- [ ] ✅ Username duplicado rechazado en registro
- [ ] ✅ Contraseña muy corta rechazada (<8 caracteres)
- [ ] ✅ Email inválido rechazado
- [ ] ✅ Usuario inactivo no puede hacer login

---

## 🎯 Prueba Rápida Todo-en-Uno

```bash
# 1. Iniciar servidor
cd backend
python start_server.py
```

En otra terminal:
```bash
# 2. Ejecutar script de prueba
cd backend
python test_auth_manual.py
```

**Salida esperada:**
```
============================================================
🧪 PROBANDO FLUJO DE AUTENTICACIÓN
============================================================

1️⃣  Registrando usuario...
   Status: 201
   ✅ Usuario creado: pythonuser (ID: 1)

2️⃣  Iniciando sesión...
   Status: 200
   ✅ Login exitoso
   Token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
   Rol: ciudadano
   Expira en: 1800 segundos

3️⃣  Obteniendo información del usuario...
   Status: 200
   ✅ Usuario autenticado:
      ID: 1
      Username: pythonuser
      Email: pythontest@example.com
      Rol: ciudadano
      Activo: True

4️⃣  Verificando validez del token...
   Status: 200
   ✅ Token válido
      User ID: 1
      Rol: ciudadano

5️⃣  Probando con token inválido...
   Status: 401
   ✅ Token inválido rechazado correctamente

6️⃣  Cerrando sesión...
   Status: 200
   ✅ Sesión cerrada exitosamente

============================================================
✅ TODAS LAS PRUEBAS COMPLETADAS
============================================================
```

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
cd backend
pip install -r requirements.txt
```

### Error: "Connection refused" (Base de datos)
```bash
docker-compose -f docker-compose.db.yml up -d
sleep 5  # Esperar que PostgreSQL inicie
alembic upgrade head
```

### Error: "Table 'users' doesn't exist"
```bash
cd backend
alembic upgrade head
```

### Token expira muy rápido (testing)
Modificar en `.env`:
```env
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 horas para testing
```

---

## 📚 Recursos Adicionales

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Documentación completa**: `backend/docs/B-03_AUTHENTICATION.md`
- **Ejemplos de código**: `backend/docs/examples_b03_usage.py`
