import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from core.config import settings

engine = create_engine(settings.DATABASE_URL)

print("=" * 60)
print("PRUEBA DE QUERIES GEOESPACIALES")
print("=" * 60)

with engine.connect() as conn:
 # Crear usuario de prueba
 print("\n1. Creando usuario de prueba...")
 result = conn.execute(text("""
 INSERT INTO users (
 username,
 email,
 hashed_password,
 full_name,
 role
 ) VALUES (
 'test_user',
 'test@example.com',
 'hashed_password_placeholder',
 'Test User',
 'CIUDADANO'
 )
 ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username
 RETURNING id;
 """))
 conn.commit()
 user_id = result.scalar()
 print(f" Usuario creado (ID: {user_id})")
 
 # Insertar un reporte de prueba
 print("\n2. Insertando reporte de prueba...")
 conn.execute(text(f"""
 INSERT INTO reports (
 user_id,
 location,
 damage_type,
 severity,
 confidence,
 status,
 image_url
 ) VALUES (
 {user_id},
 ST_GeogFromText('POINT(-69.9342 18.4861)'),
 'BACHE',
 'ALTA',
 0.95,
 'PENDING',
 'http://minio.example.com/test-image.jpg'
 );
 """))
 conn.commit()
 print(" Reporte insertado (Santo Domingo)")
 
 # Contar reportes
 result = conn.execute(text("SELECT COUNT(*) FROM reports;"))
 count = result.scalar()
 print(f"\n3. Total reportes: {count}")
 
 # Query geoespacial: distancia
 print("\n4. Calculando distancia desde centro de Santo Domingo...")
 result = conn.execute(text("""
 SELECT 
 id,
 damage_type,
 severity,
 ST_AsText(location::geometry) as coords,
 ST_Distance(
 location,
 ST_GeogFromText('POINT(-69.9312 18.4861)')
 ) as distance_meters
 FROM reports
 LIMIT 5;
 """))
 
 rows = result.fetchall()
 print(" ID | Tipo | Severidad | Coords | Distancia (m)")
 print(" " + "-" * 75)
 for row in rows:
 print(f" {row[0]:2d} | {row[1]:6s} | {row[2]:9s} | {row[3]:20s} | {row[4]:.2f}")
 
 # Query geoespacial: búsqueda por radio
 print("\n5. Buscando reportes dentro de 1km...")
 result = conn.execute(text("""
 SELECT COUNT(*)
 FROM reports
 WHERE ST_DWithin(
 location,
 ST_GeogFromText('POINT(-69.9312 18.4861)'),
 1000
 );
 """))
 nearby = result.scalar()
 print(f" Encontrados {nearby} reportes dentro de 1km")
 
 # Limpiar datos de prueba
 conn.execute(text("DELETE FROM reports WHERE user_id = :user_id;"), {"user_id": user_id})
 conn.execute(text("DELETE FROM users WHERE id = :user_id;"), {"user_id": user_id})
 conn.commit()
 print("\n6. Datos de prueba eliminados")

print(f"\n{'=' * 60}")
print(" QUERIES GEOESPACIALES FUNCIONANDO CORRECTAMENTE")
print(f"{'=' * 60}\n")

engine.dispose()
