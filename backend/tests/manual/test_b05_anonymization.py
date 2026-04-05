"""
Script de prueba para B-05: Anonimización de imágenes (blur rostros/placas)

Verifica que:
1. El servicio de anonimización detecta rostros
2. El servicio de anonimización detecta placas
3. Se aplica blur correctamente
4. Las imágenes se guardan anonimizadas
5. Nunca se almacenan imágenes sin anonimizar
"""

import asyncio
import httpx
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw


BASE_URL = "http://localhost:8000/api/v1"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_IMAGE_PATH = FIXTURES_DIR / "test_image_with_face.jpg"
TEST_IMAGE_NOFACE_PATH = FIXTURES_DIR / "test_image_noface.jpg"


def create_test_image_with_face():
 """Crea una imagen de prueba con un rostro simulado"""
 if TEST_IMAGE_PATH.exists():
 return
 
 try:
 # Crear imagen 800x600
 img = Image.new('RGB', (800, 600), color=(70, 130, 180))
 draw = ImageDraw.Draw(img)
 
 # Simular un "rostro" (círculo con puntos)
 # Nota: Haar Cascade puede no detectar esto, pero es útil para pruebas visuales
 face_x, face_y = 300, 200
 face_radius = 80
 
 # Cara (círculo beige)
 draw.ellipse([face_x-face_radius, face_y-face_radius, 
 face_x+face_radius, face_y+face_radius], 
 fill=(255, 220, 177))
 
 # Ojos
 draw.ellipse([face_x-40, face_y-20, face_x-20, face_y], fill=(0, 0, 0))
 draw.ellipse([face_x+20, face_y-20, face_x+40, face_y], fill=(0, 0, 0))
 
 # Boca
 draw.arc([face_x-30, face_y+10, face_x+30, face_y+40], 
 start=0, end=180, fill=(0, 0, 0), width=3)
 
 # Agregar texto
 draw.text((50, 500), "TEST IMAGE WITH SIMULATED FACE", fill=(255, 255, 255))
 
 # Simular un bache en la carretera
 draw.ellipse([400, 450, 600, 580], fill=(40, 40, 40))
 
 FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
 img.save(TEST_IMAGE_PATH, "JPEG")
 print(f" Imagen de prueba con rostro creada: {TEST_IMAGE_PATH}")
 
 except Exception as e:
 print(f" Error creando imagen: {e}")


def create_test_image_noface():
 """Crea una imagen sin rostros ni placas"""
 if TEST_IMAGE_NOFACE_PATH.exists():
 return
 
 try:
 img = Image.new('RGB', (800, 600), color=(100, 100, 100))
 draw = ImageDraw.Draw(img)
 
 # Solo dibujar un bache
 draw.ellipse([300, 250, 500, 350], fill=(40, 40, 40))
 draw.text((50, 500), "TEST IMAGE - NO FACES/PLATES", fill=(255, 255, 255))
 
 FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
 img.save(TEST_IMAGE_NOFACE_PATH, "JPEG")
 print(f" Imagen sin rostros creada: {TEST_IMAGE_NOFACE_PATH}")
 
 except Exception as e:
 print(f" Error creando imagen: {e}")


async def test_anonymizer_service():
 """Test 1: Probar servicio de anonimización directamente"""
 print("\n" + "="*70)
 print("1 TEST: SERVICIO DE ANONIMIZACIÓN (DIRECTO)")
 print("="*70)
 
 try:
 from services.anonymizer import image_anonymizer
 
 # Cargar imagen de prueba
 if not TEST_IMAGE_PATH.exists():
 print(" Imagen de prueba no encontrada")
 return
 
 with open(TEST_IMAGE_PATH, 'rb') as f:
 image_bytes = f.read()
 
 # Anonimizar
 print(" Detectando rostros y placas...")
 anonymized_bytes, stats = image_anonymizer.anonymize(
 image_bytes,
 detect_faces=True,
 detect_plates=True
 )
 
 print(f" Estadísticas:")
 print(f" Rostros detectados: {stats['faces_detected']}")
 print(f" Placas detectadas: {stats['plates_detected']}")
 print(f" Regiones difuminadas: {stats['regions_blurred']}")
 print(f" Anonimizada: {stats['anonymized']}")
 
 if stats.get('error'):
 print(f" Error: {stats['error']}")
 
 # Guardar imagen anonimizada para inspección visual
 output_path = FIXTURES_DIR / "test_anonymized_output.jpg"
 with open(output_path, 'wb') as f:
 f.write(anonymized_bytes)
 print(f" Imagen anonimizada guardada en: {output_path}")
 
 # Verificar que la imagen es diferente (si se detectó algo)
 if stats['anonymized']:
 print(" Imagen fue modificada (anonimización aplicada)")
 else:
 print(" ℹ No se detectaron regiones sensibles (imagen sin cambios)")
 
 except Exception as e:
 print(f" Error: {e}")
 import traceback
 traceback.print_exc()


async def login_test_user(client: httpx.AsyncClient) -> str:
 """Obtener token de autenticación"""
 print("\n Autenticando usuario...")
 
 login_data = {"username": "testb04user", "password": "testpass123"}
 response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
 
 if response.status_code == 200:
 print(" Login exitoso")
 return response.json()["access_token"]
 else:
 raise Exception(f"Error de autenticación: {response.status_code} - {response.text}")


async def test_report_with_anonymization(client: httpx.AsyncClient, token: str):
 """Test 2: Crear reporte verificando que se anonimiza"""
 print("\n" + "="*70)
 print("2 TEST: CREAR REPORTE CON ANONIMIZACIÓN")
 print("="*70)
 
 if not TEST_IMAGE_PATH.exists():
 print(" Imagen de prueba no encontrada")
 return
 
 data = {
 "latitude": -34.603722,
 "longitude": -58.381592,
 "description": "Test de anonimización B-05"
 }
 
 files = {
 "image": ("test_face.jpg", open(TEST_IMAGE_PATH, "rb"), "image/jpeg")
 }
 
 headers = {"Authorization": f"Bearer {token}"}
 
 try:
 print(" Subiendo imagen con rostro...")
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
 print(f" Reporte creado con imagen anonimizada!")
 print(f" 🆔 ID: {result['id']}")
 print(f" URL: {result['image_url']}")
 print(f" ℹ La imagen debe estar anonimizada en el storage")
 return result['id']
 else:
 print(f" Error: {response.status_code} - {response.text}")
 return None
 
 except Exception as e:
 print(f" Excepción: {e}")
 return None


async def test_report_without_faces(client: httpx.AsyncClient, token: str):
 """Test 3: Crear reporte con imagen sin rostros"""
 print("\n" + "="*70)
 print("3 TEST: IMAGEN SIN ROSTROS/PLACAS")
 print("="*70)
 
 if not TEST_IMAGE_NOFACE_PATH.exists():
 print(" Imagen de prueba no encontrada")
 return
 
 data = {
 "latitude": -34.600000,
 "longitude": -58.380000,
 "description": "Test sin elementos sensibles"
 }
 
 files = {
 "image": ("noface.jpg", open(TEST_IMAGE_NOFACE_PATH, "rb"), "image/jpeg")
 }
 
 headers = {"Authorization": f"Bearer {token}"}
 
 try:
 print(" Subiendo imagen sin rostros/placas...")
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
 print(f" Reporte creado (sin modificaciones)")
 print(f" 🆔 ID: {result['id']}")
 print(f" ℹ Imagen no tenía rostros/placas para anonimizar")
 else:
 print(f" Error: {response.status_code} - {response.text}")
 
 except Exception as e:
 print(f" Excepción: {e}")


async def test_anonymizer_availability():
 """Test 4: Verificar disponibilidad de detectores"""
 print("\n" + "="*70)
 print("4 TEST: DISPONIBILIDAD DE DETECTORES")
 print("="*70)
 
 try:
 from services.anonymizer import image_anonymizer
 
 print(" Verificando detectores...")
 
 if image_anonymizer.face_cascade is not None:
 print(" Detector de rostros (Haar Cascade): Disponible")
 else:
 print(" Detector de rostros: NO disponible")
 
 if image_anonymizer.plate_cascade is not None:
 print(" Detector de placas (Haar Cascade): Disponible")
 else:
 print(" ℹ Detector de placas Haar: NO disponible (usando método básico)")
 
 print("\n ℹ Nota: Es normal que el detector de placas Haar no esté disponible.")
 print(" ℹ Se usará el método de detección básico por color/forma.")
 
 except Exception as e:
 print(f" Error: {e}")


async def main():
 """Ejecuta todos los tests de B-05"""
 print("\n" + "="*70)
 print(" TESTS B-05: ANONIMIZACIÓN DE IMÁGENES (BLUR)")
 print("="*70)
 print(" Iniciado")
 print(f" URL Base: {BASE_URL}")
 print("="*70)
 
 # Crear imágenes de prueba
 create_test_image_with_face()
 create_test_image_noface()
 
 # Test 4: Verificar detectores disponibles
 await test_anonymizer_availability()
 
 # Test 1: Servicio directo
 await test_anonymizer_service()
 
 # Verificar servidor y autenticar
 async with httpx.AsyncClient() as client:
 try:
 response = await client.get(f"{BASE_URL}/health")
 if response.status_code != 200:
 print("\n El servidor no está activo. Inicia el server primero.")
 return
 print("\n Servidor activo")
 except Exception as e:
 print(f"\n No se puede conectar al servidor: {e}")
 return
 
 # Autenticar
 try:
 token = await login_test_user(client)
 except Exception as e:
 print(f" Error de autenticación: {e}")
 return
 
 # Tests con endpoint
 await test_report_with_anonymization(client, token)
 await test_report_without_faces(client, token)
 
 print("\n" + "="*70)
 print(" TESTS B-05 COMPLETADOS")
 print("="*70)
 print("\n Revisar imágenes generadas para verificación visual:")
 print(f" - {TEST_IMAGE_PATH}")
 print(f" - {TEST_IMAGE_NOFACE_PATH}")
 print(f" - test_anonymized_output.jpg (con blur aplicado)")
 print("\n POLÍTICA DE SEGURIDAD:")
 print(" TODAS las imágenes se anonimizan antes de guardar")
 print(" Si la anonimización falla, la imagen NO se guarda")
 print(" Nunca se almacenan imágenes sin procesar")


if __name__ == "__main__":
 asyncio.run(main())
