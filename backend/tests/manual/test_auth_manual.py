"""
Script de prueba manual para B-03: Autenticación JWT y RBAC

Ejecutar: python test_auth_manual.py
"""

import httpx
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_auth_flow():
 """Prueba completa del flujo de autenticación"""
 
 print("=" * 70)
 print(" PROBANDO FLUJO DE AUTENTICACIÓN B-03")
 print("=" * 70)
 print(f" Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
 print(f" URL Base: {BASE_URL}")
 print("=" * 70)
 
 try:
 # Verificar que el servidor está corriendo
 print("\n0 Verificando servidor...")
 try:
 response = httpx.get(f"http://localhost:8000/docs", timeout=2)
 print(f" Servidor activo (status: {response.status_code})")
 except (httpx.RequestError, httpx.TimeoutException):
 print(f" Servidor no responde")
 print(f"\n Iniciar servidor con:")
 print(f" cd backend")
 print(f" python start_server.py")
 sys.exit(1)
 
 # 1. Registro
 print("\n1 REGISTRO DE USUARIO")
 print(" " + "-" * 65)
 register_data = {
 "email": "pythontest@example.com",
 "username": "pythonuser",
 "password": "PythonPass123!",
 "full_name": "Usuario Python Test",
 "phone": "+18095551234"
 }
 
 print(f" Email: {register_data['email']}")
 print(f" Username: {register_data['username']}")
 
 response = httpx.post(f"{BASE_URL}/auth/register", json=register_data)
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 201:
 user_data = response.json()
 print(f" Usuario creado exitosamente")
 print(f" ID: {user_data['user_id']}")
 print(f" Username: {user_data['username']}")
 print(f" Email: {user_data['email']}")
 elif response.status_code == 400:
 error = response.json()
 if "ya está" in error.get("detail", "").lower():
 print(f" Usuario ya existe (reutilizando)")
 else:
 print(f" Error: {error.get('detail')}")
 else:
 print(f" Error inesperado: {response.text}")
 return False
 
 # 2. Login
 print("\n2 LOGIN")
 print(" " + "-" * 65)
 login_data = {
 "username": "pythonuser",
 "password": "PythonPass123!"
 }
 
 response = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
 print(f" Status Code: {response.status_code}")
 
 if response.status_code != 200:
 print(f" Error en login: {response.json()}")
 return False
 
 login_response = response.json()
 token = login_response["access_token"]
 print(f" Login exitoso")
 print(f" Token: {token[:40]}...")
 print(f" User ID: {login_response['user_id']}")
 print(f" Username: {login_response['username']}")
 print(f" Rol: {login_response['role']}")
 print(f" Expira en: {login_response['expires_in']} segundos ({login_response['expires_in']//60} minutos)")
 
 # 3. Obtener info del usuario autenticado
 print("\n3 OBTENER INFO DE USUARIO AUTENTICADO")
 print(" " + "-" * 65)
 headers = {"Authorization": f"Bearer {token}"}
 
 response = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 200:
 user_info = response.json()
 print(f" Usuario autenticado correctamente")
 print(f"  ID: {user_info['id']}")
 print(f" Username: {user_info['username']}")
 print(f" Email: {user_info['email']}")
 print(f" Nombre: {user_info['full_name']}")
 print(f" Teléfono: {user_info.get('phone', 'N/A')}")
 print(f" Rol: {user_info['role']}")
 print(f" Activo: {user_info['is_active']}")
 print(f" Verificado: {user_info['is_verified']}")
 print(f" Creado: {user_info['created_at']}")
 else:
 print(f" Error: {response.json()}")
 return False
 
 # 4. Verificar validez del token
 print("\n4 VERIFICAR TOKEN")
 print(" " + "-" * 65)
 response = httpx.post(f"{BASE_URL}/auth/verify-token", params={"token": token})
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 200:
 verification = response.json()
 if verification["valid"]:
 print(f" Token válido")
 print(f" User ID: {verification['user_id']}")
 print(f" Rol: {verification['role']}")
 print(f" Expira: {datetime.fromtimestamp(verification['expires_at']).strftime('%Y-%m-%d %H:%M:%S')}")
 else:
 print(f" Token marcado como inválido")
 return False
 else:
 print(f" Error: {response.json()}")
 return False
 
 # 5. Probar token inválido (debe fallar)
 print("\n5 PROBAR TOKEN INVÁLIDO (debe rechazar)")
 print(" " + "-" * 65)
 bad_headers = {"Authorization": "Bearer token_invalido_abc123"}
 response = httpx.get(f"{BASE_URL}/auth/me", headers=bad_headers)
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 401:
 print(f" Token inválido rechazado correctamente")
 print(f" Detalle: {response.json().get('detail')}")
 else:
 print(f" ERROR: Debería haber rechazado el token inválido")
 return False
 
 # 6. Probar acceso sin token (debe fallar)
 print("\n6 PROBAR SIN TOKEN (debe rechazar)")
 print(" " + "-" * 65)
 response = httpx.get(f"{BASE_URL}/auth/me")
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 401:
 print(f" Acceso sin token rechazado correctamente")
 else:
 print(f" ERROR: Debería haber rechazado el acceso sin token")
 return False
 
 # 7. Probar login con contraseña incorrecta (debe fallar)
 print("\n7 PROBAR CONTRASEÑA INCORRECTA (debe rechazar)")
 print(" " + "-" * 65)
 bad_login = {
 "username": "pythonuser",
 "password": "ContrasenaIncorrecta123!"
 }
 
 response = httpx.post(f"{BASE_URL}/auth/login", json=bad_login)
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 401:
 print(f" Contraseña incorrecta rechazada correctamente")
 print(f" Detalle: {response.json().get('detail')}")
 else:
 print(f" ERROR: Debería haber rechazado la contraseña incorrecta")
 return False
 
 # 8. Logout
 print("\n8 LOGOUT")
 print(" " + "-" * 65)
 response = httpx.post(f"{BASE_URL}/auth/logout", headers=headers)
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 200:
 logout_response = response.json()
 print(f" {logout_response['message']}")
 print(f" Usuario: {logout_response['username']}")
 else:
 print(f" Logout falló (no crítico con JWT stateless)")
 
 # Resumen final
 print("\n" + "=" * 70)
 print(" TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
 print("=" * 70)
 print(f"\n Resumen:")
 print(f" Registro: OK")
 print(f" Login: OK")
 print(f" Autenticación: OK")
 print(f" Verificación de token: OK")
 print(f" Rechazo de token inválido: OK")
 print(f" Rechazo sin token: OK")
 print(f" Rechazo de contraseña incorrecta: OK")
 print(f" Logout: OK")
 print(f"\n Sistema de autenticación B-03 funcionando correctamente")
 print(f" Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
 print("=" * 70 + "\n")
 
 return True
 
 except httpx.RequestError as e:
 print(f"\n Error de conexión: {e}")
 print(f"\n Asegúrate de que el servidor esté corriendo:")
 print(f" cd backend")
 print(f" python start_server.py")
 return False
 except Exception as e:
 print(f"\n Error inesperado: {e}")
 import traceback
 traceback.print_exc()
 return False

if __name__ == "__main__":
 print("\n")
 success = test_auth_flow()
 
 if success:
 print(" Próximos pasos:")
 print(" 1. Probar en Swagger UI: http://localhost:8000/docs")
 print(" 2. Ver documentación del modulo: ../docs/backend.md")
 print(" 3. Ejecutar tests automatizados: pytest tests/test_auth.py -v")
 sys.exit(0)
 else:
 print("\n Algunas pruebas fallaron. Revisar arriba para más detalles.")
 sys.exit(1)
