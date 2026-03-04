#!/usr/bin/env python
"""Script para verificar la migración de base de datos."""
import sys
from sqlalchemy import create_engine, inspect, text
from core.config import settings

def verify_migration():
 """Verificar que las tablas y PostGIS estén configurados correctamente."""
 print(f"Conectando a: {settings.DATABASE_URL}")
 engine = create_engine(settings.DATABASE_URL)
 
 try:
 with engine.connect() as conn:
 # Verificar PostGIS
 result = conn.execute(text("SELECT PostGIS_version();"))
 postgis_version = result.scalar()
 print(f"\n PostGIS instalado: {postgis_version}")
 
 # Verificar tablas
 inspector = inspect(engine)
 tables = inspector.get_table_names()
 print(f"\n Tablas creadas ({len(tables)}):")
 for table in sorted(tables):
 print(f" - {table}")
 
 # Verificar columnas de Geography
 geo_columns = []
 for table in tables:
 columns = inspector.get_columns(table)
 for col in columns:
 if 'geography' in str(col['type']).lower():
 geo_columns.append(f"{table}.{col['name']}")
 
 print(f"\n Columnas Geography ({len(geo_columns)}):")
 for col in geo_columns:
 print(f" - {col}")
 
 # Verificar índices espaciales
 result = conn.execute(text("""
 SELECT tablename, indexname 
 FROM pg_indexes 
 WHERE schemaname = 'public' AND indexname LIKE '%location%'
 ORDER BY tablename, indexname;
 """))
 indexes = result.fetchall()
 print(f"\n Índices espaciales ({len(indexes)}):")
 for table, index in indexes:
 print(f" - {table}: {index}")
 
 # Verificar extensiones
 result = conn.execute(text("""
 SELECT extname, extversion 
 FROM pg_extension 
 WHERE extname IN ('postgis', 'postgis_topology');
 """))
 extensions = result.fetchall()
 print(f"\n Extensiones PostgreSQL:")
 for name, version in extensions:
 print(f" - {name} v{version}")
 
 print("\n Migración verificada exitosamente!")
 return True
 
 except Exception as e:
 print(f"\n Error de verificación: {e}")
 return False
 finally:
 engine.dispose()

if __name__ == "__main__":
 success = verify_migration()
 sys.exit(0 if success else 1)
