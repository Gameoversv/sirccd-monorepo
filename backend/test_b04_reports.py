"""
Script de prueba para B-04: Crear Reporte (foto, GPS, descripción)

Prueba el endpoint POST /reportes con diferentes escenarios:
1. Reporte válido con todos los campos
2. Reporte mínimo (solo imagen y GPS)
3. Validaciones de imagen (tamaño, tipo)
4. Validaciones de coordenadas GPS
5. Verificar almacenamiento y BD
"""

import asyncio
import httpx
import os
from pathlib import Path


BASE_URL = "http://localhost:8000/api/v1"
TEST_IMAGE_PATH = Path(__file__).parent / "test_image.jpg"


def create_test_image():
 """Crea una imagen de prueba si no existe"""
 if TEST_IMAGE_PATH.exists():
 return
 
 try:
 from PIL import Image, ImageDraw, ImageFont
 
 # Crear imagen 800x600 con texto
 img = Image.new('RGB', (800, 600), color=(70, 130, 180))
 draw = ImageDraw.Draw(img)
 
 # Dibujar texto
 text = "TEST IMAGE\nBACHE EN CALLE"
 draw.text((300, 250), text, fill=(255, 255, 255))
 
 # Simular un bache (círculo oscuro)
 draw.ellipse([300, 400, 500, 550], fill=(40, 40, 40))
 
 img.save(TEST_IMAGE_PATH, "JPEG")
 print(f" Imagen de prueba creada: {TEST_IMAGE_PATH}")
 
 except ImportError:
 print(" Pillow no instalado. Crea manualmente test_image.jpg")


async def login_test_user(client: httpx.AsyncClient) -> str:
 """Login y obtener token de prueba"""
 print("\n Autenticando usuario de prueba...")
 
 # Intentar login con usuario existente
 login_data = {
 "username": "testb04user",
 "password": "testpass123"
 }
 
 response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
 
 if response.status_code == 200:
 token = response.json()["access_token"]
 print(f" Login exitoso")
 return token
 elif response.status_code == 401:
 print(" Usuario no encontrado. Usa el usuario 'pythonuser' con password 'testpass123'")
 print(" O ejecuta primero test_auth_manual.py para crear el usuario")
 raise Exception("Usuario de prueba no existe")
 else:
 raise Exception(f"Error de autenticación: {response.status_code} - {response.text}")


async def test_create_report_full(client: httpx.AsyncClient, token: str):
 """Test 1: Crear reporte con todos los campos"""
 print("\n" + "="*70)
 print("1 TEST: CREAR REPORTE COMPLETO")
 print("="*70)
 
 if not TEST_IMAGE_PATH.exists():
 print(" test_image.jpg no encontrada. Ejecuta create_test_image() primero.")
 return
 
 # Preparar datos
 data = {
 "latitude": -34.603722,
 "longitude": -58.381592,
 "description": "Bache profundo que afecta el tránsito vehicular",
 "address": "Av. Corrientes 1234",
 "city": "Buenos Aires",
 "province": "Buenos Aires"
 }
 
 files = {
 "image": ("test_report.jpg", open(TEST_IMAGE_PATH, "rb"), "image/jpeg")
 }
 
 headers = {"Authorization": f"Bearer {token}"}
 
 try:
 response = await client.post(
 f"{BASE_URL}/reportes",
 data=data,
 files=files,
 headers=headers,
 timeout=30.0
 )
 
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 201:
 result = response.json()
 print(f" Reporte creado exitosamente!")
 print(f" 🆔 ID: {result['id']}")
 print(f" Tipo detectado: {result['damage_type']}")
 print(f" Severidad: {result['severity']}")
 print(f" Confianza: {result['confidence']:.2%}")
 print(f" URL imagen: {result['image_url']}")
 print(f" GPS: ({result['latitude']}, {result['longitude']})")
 print(f" Descripción: {result['description']}")
 print(f" Creado: {result['created_at']}")
 return result['id']
 else:
 print(f" Error: {response.status_code}")
 print(f" {response.text}")
 return None
 
 except Exception as e:
 print(f" Excepción: {str(e)}")
 return None


async def test_create_report_minimal(client: httpx.AsyncClient, token: str):
 """Test 2: Crear reporte con campos mínimos"""
 print("\n" + "="*70)
 print("2 TEST: CREAR REPORTE MÍNIMO (solo imagen + GPS)")
 print("="*70)
 
 if not TEST_IMAGE_PATH.exists():
 print(" test_image.jpg no encontrada.")
 return
 
 data = {
 "latitude": -34.600000,
 "longitude": -58.380000
 }
 
 files = {
 "image": ("minimal_report.jpg", open(TEST_IMAGE_PATH, "rb"), "image/jpeg")
 }
 
 headers = {"Authorization": f"Bearer {token}"}
 
 try:
 response = await client.post(
 f"{BASE_URL}/reportes",
 data=data,
 files=files,
 headers=headers,
 timeout=30.0
 )
 
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 201:
 result = response.json()
 print(f" Reporte mínimo creado!")
 print(f" 🆔 ID: {result['id']}")
 print(f" Tipo: {result['damage_type']}")
 print(f" Severidad: {result['severity']}")
 return result['id']
 else:
 print(f" Error: {response.status_code} - {response.text}")
 
 except Exception as e:
 print(f" Excepción: {str(e)}")


async def test_invalid_gps(client: httpx.AsyncClient, token: str):
 """Test 3: Validar coordenadas GPS inválidas"""
 print("\n" + "="*70)
 print("3 TEST: VALIDACIÓN DE GPS INVÁLIDO")
 print("="*70)
 
 invalid_coords = [
 (91.0, -58.0, "Latitud > 90"),
 (-91.0, -58.0, "Latitud < -90"),
 (-34.0, 181.0, "Longitud > 180"),
 (-34.0, -181.0, "Longitud < -180"),
 ]
 
 for lat, lng, description in invalid_coords:
 print(f"\n Probando: {description} ({lat}, {lng})")
 
 data = {
 "latitude": lat,
 "longitude": lng
 }
 
 files = {
 "image": ("test.jpg", open(TEST_IMAGE_PATH, "rb"), "image/jpeg")
 }
 
 headers = {"Authorization": f"Bearer {token}"}
 
 try:
 response = await client.post(
 f"{BASE_URL}/reportes",
 data=data,
 files=files,
 headers=headers,
 timeout=30.0
 )
 
 if response.status_code == 422:
 print(f" Validación correcta - rechazado (422)")
 else:
 print(f" Debería rechazar pero status: {response.status_code}")
 
 except Exception as e:
 print(f" Excepción: {str(e)}")


async def test_get_report(client: httpx.AsyncClient, token: str, report_id: int):
 """Test 4: Obtener reporte por ID"""
 print("\n" + "="*70)
 print(f"4 TEST: OBTENER REPORTE ID={report_id}")
 print("="*70)
 
 headers = {"Authorization": f"Bearer {token}"}
 
 try:
 response = await client.get(
 f"{BASE_URL}/reportes/{report_id}",
 headers=headers
 )
 
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 200:
 result = response.json()
 print(f" Reporte obtenido correctamente")
 print(f" 🆔 ID: {result['id']}")
 print(f" Usuario: {result['user_id']}")
 print(f" Tipo: {result['damage_type']}")
 print(f" Severidad: {result['severity']}")
 print(f" GPS: ({result['latitude']:.6f}, {result['longitude']:.6f})")
 print(f" Ciudad: {result.get('city', 'N/A')}")
 print(f" Estado: {result['status']}")
 else:
 print(f" Error: {response.status_code} - {response.text}")
 
 except Exception as e:
 print(f" Excepción: {str(e)}")


async def test_unauthorized_access(client: httpx.AsyncClient):
 """Test 5: Intentar crear reporte sin autenticación"""
 print("\n" + "="*70)
 print("5 TEST: ACCESO SIN AUTENTICACIÓN")
 print("="*70)
 
 data = {
 "latitude": -34.6,
 "longitude": -58.4
 }
 
 files = {
 "image": ("test.jpg", open(TEST_IMAGE_PATH, "rb"), "image/jpeg")
 }
 
 try:
 response = await client.post(
 f"{BASE_URL}/reportes",
 data=data,
 files=files,
 timeout=30.0
 )
 
 print(f" Status Code: {response.status_code}")
 
 if response.status_code == 401:
 print(f" Acceso sin token rechazado correctamente")
 else:
 print(f" Debería rechazar (401) pero status: {response.status_code}")
 
 except Exception as e:
 print(f" Excepción: {str(e)}")


async def main():
 """Ejecuta todos los tests"""
 print("\n" + "="*70)
 print(" TESTS B-04: ENDPOINT CREAR REPORTE")
 print("="*70)
 print(f" Iniciado: {asyncio.get_event_loop().time()}")
 print(f" URL Base: {BASE_URL}")
 print("="*70)
 
 # Crear imagen de prueba
 create_test_image()
 
 # Verificar que el servidor está activo
 async with httpx.AsyncClient() as client:
 try:
 response = await client.get(f"{BASE_URL}/health")
 if response.status_code != 200:
 print(" El servidor no está activo. Inicia el server primero.")
 return
 print(" Servidor activo\n")
 except Exception as e:
 print(f" No se puede conectar al servidor: {e}")
 print(" Ejecuta: cd backend && python -m uvicorn main:app --reload")
 return
 
 # Autenticar
 try:
 token = await login_test_user(client)
 except Exception as e:
 print(f" Error de autenticación: {e}")
 return
 
 # Ejecutar tests
 report_id = await test_create_report_full(client, token)
 
 if report_id:
 await test_get_report(client, token, report_id)
 
 await test_create_report_minimal(client, token)
 await test_invalid_gps(client, token)
 await test_unauthorized_access(client)
 
 print("\n" + "="*70)
 print(" TESTS COMPLETADOS")
 print("="*70)


if __name__ == "__main__":
 asyncio.run(main())
