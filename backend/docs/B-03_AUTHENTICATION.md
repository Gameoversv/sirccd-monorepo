# B-03: Autenticación JWT y RBAC

## Descripción General

Implementación completa de autenticación basada en JWT (JSON Web Tokens) y control de acceso basado en roles (RBAC - Role-Based Access Control) para el sistema SIRCCD.

## Arquitectura de Autenticación

### Flujo de Autenticación

```
1. Registro
   Usuario → POST /auth/register → Sistema hashea password → BD → Usuario creado

2. Login
   Usuario → POST /auth/login → Verifica credenciales → Genera JWT → Retorna token

3. Acceso a recursos protegidos
   Usuario → Request con JWT → Middleware valida token → Extrae roles → Permite/Deniega acceso
```

### Componentes Implementados

#### 1. `core/security.py` - Utilidades de Seguridad

**Funciones de Password Hashing (bcrypt):**
- `get_password_hash(password: str) -> str`: Genera hash bcrypt
- `verify_password(plain: str, hashed: str) -> bool`: Verifica contraseña

**Funciones de JWT:**
- `create_access_token(subject, expires_delta, additional_claims) -> str`: Crea token de acceso
- `create_refresh_token(subject, expires_delta) -> str`: Crea refresh token
- `decode_access_token(token: str) -> dict`: Decodifica y valida token
- `validate_token_type(token: str, expected_type: str) -> bool`: Valida tipo de token

**Configuración:**
- Algoritmo: HS256
- Expiración access token: 30 minutos (configurable)
- Expiración refresh token: 7 días
- Secret key: Desde `settings.SECRET_KEY`

#### 2. `schemas/user.py` - Schemas de Usuario

**Schemas Pydantic:**
- `UserBase`: Campos comunes (email, username, full_name, phone, role)
- `UserCreate`: Para crear usuarios (incluye password)
- `UserUpdate`: Para actualizaciones (campos opcionales)
- `UserResponse`: Para respuestas API (sin password)
- `UserListItem`: Schema simplificado para listados
- `PasswordChange`: Para cambio de contraseña

**Validaciones:**
- Email válido (EmailStr)
- Username: 3-100 caracteres
- Password: mínimo 8 caracteres
- Todos los campos validados por Pydantic

#### 3. `schemas/auth.py` - Schemas de Autenticación

**Schemas principales:**
- `LoginRequest`: Credenciales de login (username/email + password)
- `LoginResponse`: Respuesta con token + datos usuario
- `RegisterRequest`: Datos para registro de usuario
- `RegisterResponse`: Confirmación de registro
- `Token`: Token JWT + metadata
- `TokenPayload`: Payload decodificado del token
- `TokenVerification`: Resultado de verificación de token
- `RefreshTokenRequest`: Solicitud de refresh token

#### 4. `api/deps.py` - Dependencias de FastAPI

**Dependencias de Autenticación:**

```python
# Básica
CurrentUser = Annotated[User, Depends(get_current_user)]
# → Extrae y valida token, retorna usuario

ActiveUser = Annotated[User, Depends(get_current_active_user)]
# → Usuario debe estar activo

VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
# → Usuario debe estar verificado (email confirmado)
```

**Dependencias de Autorización (RBAC):**

```python
AdminUser = Annotated[User, Depends(require_admin)]
# → Solo usuarios con rol ADMIN

SupervisorUser = Annotated[User, Depends(require_supervisor)]
# → SUPERVISOR o ADMIN

BrigadaUser = Annotated[User, Depends(require_brigada)]
# → BRIGADA, SUPERVISOR o ADMIN
```

**Factory para roles personalizados:**
```python
require_role(*allowed_roles: UserRole)
# → Crea dependencia para roles específicos

# Ejemplo de uso:
@router.get("/endpoint", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SUPERVISOR))])
async def protected_endpoint():
    return {"message": "Solo admins y supervisores"}
```

#### 5. `api/routes/auth.py` - Endpoints de Autenticación

**Endpoints implementados:**

##### POST `/api/v1/auth/register`
Registrar nuevo usuario (ciudadano por defecto)

**Request:**
```json
{
  "email": "usuario@example.com",
  "username": "usuario123",
  "password": "securepass123",
  "full_name": "Usuario Ejemplo",
  "phone": "+1809-555-0123"
}
```

**Response (201):**
```json
{
  "message": "Usuario registrado exitosamente. Por favor verifica tu email.",
  "user_id": 1,
  "username": "usuario123",
  "email": "usuario@example.com"
}
```

**Validaciones:**
- Email único
- Username único
- Password mínimo 8 caracteres
- Usuario creado como CIUDADANO y no verificado

##### POST `/api/v1/auth/login`
Iniciar sesión

**Request:**
```json
{
  "username": "usuario123",  // o email
  "password": "securepass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": 1,
  "username": "usuario123",
  "email": "usuario@example.com",
  "role": "ciudadano",
  "full_name": "Usuario Ejemplo"
}
```

**Funcionalidades:**
- Acepta username o email en campo username
- Actualiza last_login del usuario
- Retorna token JWT + información del usuario

##### POST `/api/v1/auth/login/oauth2`
Login compatible con OAuth2 (para Swagger UI y herramientas)

**Request (form data):**
```
username=usuario123
password=securepass123
```

**Response (200):**
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

##### GET `/api/v1/auth/me`
Obtener información del usuario actual

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": 1,
  "username": "usuario123",
  "email": "usuario@example.com",
  "full_name": "Usuario Ejemplo",
  "phone": "+1809-555-0123",
  "role": "ciudadano",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-02-26T10:00:00",
  "updated_at": "2026-02-26T12:30:00",
  "last_login": "2026-02-26T12:30:00"
}
```

##### POST `/api/v1/auth/verify-token`
Verificar validez de un token

**Request:**
```
?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "valid": true,
  "user_id": 1,
  "role": "ciudadano",
  "expires_at": 1709048400
}
```

##### POST `/api/v1/auth/refresh`
Obtener nuevo access token con refresh token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

##### POST `/api/v1/auth/logout`
Cerrar sesión

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "message": "Sesión cerrada exitosamente",
  "username": "usuario123"
}
```

**Nota:** Con JWT stateless, el logout se maneja principalmente en el cliente. Este endpoint puede extenderse para implementar blacklist de tokens en Redis.

## Sistema de Roles (RBAC)

### Roles Disponibles

```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"          # Administrador del sistema
    SUPERVISOR = "supervisor"  # Supervisor de brigadas
    BRIGADA = "brigada"       # Miembro de brigada
    CIUDADANO = "ciudadano"   # Ciudadano reportante
```

### Jerarquía de Permisos

```
CIUDADANO (nivel más bajo)
    ↓
BRIGADA
    ↓
SUPERVISOR
    ↓
ADMIN (nivel más alto)
```

### Uso en Endpoints

**Ejemplo 1: Solo admins**
```python
from api.deps import AdminUser

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: AdminUser):
    # Solo admins pueden ejecutar esto
    pass
```

**Ejemplo 2: Brigada o superior**
```python
from api.deps import BrigadaUser

@router.get("/incidents/assigned")
async def get_assigned_incidents(current_user: BrigadaUser):
    # BRIGADA, SUPERVISOR o ADMIN pueden acceder
    pass
```

**Ejemplo 3: Múltiples roles específicos**
```python
from api.deps import require_role
from models.user import UserRole

@router.post(
    "/reports/approve",
    dependencies=[Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN))]
)
async def approve_report():
    # Solo SUPERVISOR o ADMIN
    pass
```

**Ejemplo 4: Usuario autenticado (cualquier rol)**
```python
from api.deps import CurrentUser

@router.get("/profile")
async def get_profile(current_user: CurrentUser):
    # Cualquier usuario autenticado
    return {"user": current_user.username}
```

## Seguridad Implementada

### 1. Password Hashing
- **Algoritmo:** bcrypt (vía Passlib)
- **Ventajas:**
  - Resistente a ataques de fuerza bruta
  - Salt automático único por password
  - Computacionalmente costoso para atacantes
  - Estándar de la industria

### 2. JWT (JSON Web Tokens)
- **Algoritmo de firma:** HS256 (HMAC con SHA-256)
- **Claims estándar:**
  - `sub`: User ID
  - `exp`: Timestamp de expiración
  - `iat`: Timestamp de emisión
- **Claims personalizados:**
  - `role`: Rol del usuario
  - `username`: Nombre de usuario
  - `type`: Tipo de token (access/refresh)

### 3. Validaciones
- Email único y válido
- Username único (3-100 caracteres)
- Password mínimo 8 caracteres
- Verificación de usuario activo en cada request
- Verificación de expiración de token

### 4. Protección contra Ataques

**SQL Injection:**
- SQLAlchemy ORM previene inyección automáticamente
- Queries parametrizadas

**Password Timing Attacks:**
- `verify_password` usa comparación de tiempo constante

**Token Hijacking:**
- Tokens firmados criptográficamente
- Validación de firma en cada request

**Brute Force:**
- Contraseñas hasheadas con bcrypt (costoso computacionalmente)
- Posibilidad de agregar rate limiting (futura mejora)

## Testing

### Tests Implementados (`tests/test_auth.py`)

**26 tests cubriendo:**

1. **Registro (5 tests):**
   - Registro exitoso
   - Email duplicado
   - Username duplicado
   - Contraseña débil
   - Password hasheado en BD

2. **Login (5 tests):**
   - Login exitoso
   - Login con email
   - Contraseña incorrecta
   - Usuario inexistente
   - Usuario inactivo

3. **Usuario actual (3 tests):**
   - Obtener info con token válido
   - Sin token (401)
   - Token inválido (401)

4. **Verificación de token (2 tests):**
   - Token válido
   - Token inválido

5. **OAuth2 (1 test):**
   - Login con formato OAuth2

6. **Autorización por roles (2 tests):**
   - Admin access
   - Brigada access

7. **Seguridad (2 tests):**
   - Password hasheado
   - Token contiene info correcta

8. **Logout (1 test):**
   - Logout exitoso

### Ejecutar Tests

```bash
# Todos los tests de autenticación
pytest backend/tests/test_auth.py -v

# Test específico
pytest backend/tests/test_auth.py::test_login_success -v

# Con coverage
pytest backend/tests/test_auth.py --cov=backend/api/routes/auth --cov-report=html
```

## Configuración

### Variables de Entorno (`.env`)

```env
# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (para almacenar usuarios)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sirccd_user
POSTGRES_PASSWORD=sirccd_password
POSTGRES_DB=sirccd_db
```

⚠️ **IMPORTANTE:** Cambiar `SECRET_KEY` en producción. Debe ser:
- Al menos 32 caracteres
- Aleatorio y único
- Guardado de forma segura (nunca en Git)

**Generar SECRET_KEY seguro:**
```python
import secrets
print(secrets.token_urlsafe(32))
# Ejemplo output: 'Wx8kJ9nM2pQ3rT5vY7bC1dF4gH6jK8lN0oP2qR4sU6w'
```

## Ejemplos de Uso

### Frontend - Registro y Login

```javascript
// Registro
const register = async (email, username, password) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password })
  });
  return await response.json();
};

// Login
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  
  // Guardar token en localStorage
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify({
    id: data.user_id,
    username: data.username,
    role: data.role
  }));
  
  return data;
};

// Request autenticado
const getProfile = async () => {
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:8000/api/v1/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
};

// Logout
const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  // Opcionalmente, llamar al endpoint de logout
};
```

### Backend - Crear Endpoints Protegidos

```python
from fastapi import APIRouter, Depends
from api.deps import CurrentUser, AdminUser, require_role
from models.user import UserRole

router = APIRouter()

# Endpoint público (sin autenticación)
@router.get("/public")
async def public_endpoint():
    return {"message": "Público"}

# Endpoint protegido (cualquier usuario autenticado)
@router.get("/profile")
async def get_profile(current_user: CurrentUser):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }

# Solo para admins
@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: AdminUser):
    # admin es garantizado ser UserRole.ADMIN
    return {"message": f"Usuario {user_id} eliminado por {admin.username}"}

# Solo supervisores y admins
@router.post(
    "/incidents/assign",
    dependencies=[Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN))]
)
async def assign_incident(incident_id: int, brigade_id: int):
    return {"message": "Incidente asignado"}

# Acceso condicional basado en rol
@router.get("/dashboard")
async def get_dashboard(current_user: CurrentUser):
    if current_user.role == UserRole.ADMIN:
        return {"data": "Panel completo de admin"}
    elif current_user.role == UserRole.SUPERVISOR:
        return {"data": "Panel de supervisor"}
    else:
        return {"data": "Panel básico"}
```

## Próximas Mejoras (Post B-03)

### 1. Refresh Tokens Persistentes
- Almacenar refresh tokens en base de datos
- Permitir revocación de tokens específicos
- Tokens de larga duración para "recordarme"

### 2. Blacklist de Tokens
- Redis para almacenar tokens invalidados
- Logout efectivo (invalidar token antes de expiración)
- Invalidar todos los tokens de un usuario

### 3. Rate Limiting
- Limitar intentos de login (prevenir brute force)
- Límites por IP y por usuario
- Redis para contadores

### 4. Two-Factor Authentication (2FA)
- TOTP (Time-based One-Time Password)
- SMS/Email verification
- Códigos de recuperación

### 5. OAuth2 Social Login
- Login con Google, Facebook, GitHub
- Federated identity
- Link de cuentas sociales

### 6. Email Verification
- Enviar email con token de verificación
- Endpoint para verificar token
- Reenviar email de verificación

### 7. Password Reset
- Solicitar reset por email
- Token de un solo uso con expiración
- Endpoint para cambiar password

### 8. Audit Logging
- Registrar todos los eventos de autenticación
- IP, user agent, timestamp
- Alertas de actividad sospechosa

### 9. Session Management
- Listar sesiones activas del usuario
- Cerrar sesiones individuales
- Cerrar todas las sesiones

## Documentación API

La documentación interactiva está disponible en:

- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc

Incluye:
- Todos los endpoints de autenticación
- Esquemas de request/response
- Botón "Authorize" para probar con tokens
- Ejemplos de uso

## Resolución de Problemas

### Error: "No se pudo validar las credenciales"
- Verificar que el token sea válido
- Verificar que el token no haya expirado
- Verificar formato del header: `Authorization: Bearer {token}`

### Error: "Usuario inactivo"
- El usuario está marcado como inactivo en BD
- Un admin debe activar el usuario

### Error: "Se requiere rol de administrador"
- El endpoint requiere permisos que el usuario no tiene
- Verificar el rol del usuario en `/auth/me`

### Error: "El email ya está registrado"
- Usar un email diferente
- Recuperar cuenta existente

### Token expira muy rápido
- Ajustar `ACCESS_TOKEN_EXPIRE_MINUTES` en settings
- Implementar refresh tokens para renovar

## Estructura de Archivos

```
backend/
├── core/
│   ├── security.py          # JWT y password hashing
│   └── config.py            # Configuración (SECRET_KEY, etc)
├── models/
│   └── user.py              # Modelo User con UserRole enum
├── schemas/
│   ├── user.py              # Schemas de usuario
│   └── auth.py              # Schemas de autenticación
├── api/
│   ├── deps.py              # Dependencias de autenticación/autorización
│   └── routes/
│       └── auth.py          # Endpoints de autenticación
├── tests/
│   └── test_auth.py         # 26 tests de autenticación
└── main.py                  # FastAPI app con rutas registradas
```

## Checklist de Implementación

- [x] Password hashing con bcrypt
- [x] Generación de JWT tokens
- [x] Validación de JWT tokens
- [x] Endpoint de registro
- [x] Endpoint de login
- [x] Endpoint /me (usuario actual)
- [x] Endpoint de logout
- [x] Endpoint de verificación de token
- [x] Endpoint OAuth2 compatible
- [x] Dependencias de autenticación
- [x] Dependencias de autorización (RBAC)
- [x] Tests completos (26 tests)
- [x] Documentación API (Swagger)
- [x] Schemas Pydantic
- [x] Validaciones de entrada
- [x] Manejo de errores
- [x] Actualización de last_login
- [x] Soporte para login con email o username

## Referencias

- [JWT.io](https://jwt.io/) - JWT debugger y documentación
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - Docs oficiales
- [Passlib](https://passlib.readthedocs.io/) - Password hashing
- [Python-JOSE](https://python-jose.readthedocs.io/) - JWT para Python
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
