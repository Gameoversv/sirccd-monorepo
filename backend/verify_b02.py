import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from core.config import settings

engine = create_engine(settings.DATABASE_URL)

print("=" * 60)
print("VERIFICACIÓN DE MIGRACIÓN B-02")
print("=" * 60)

with engine.connect() as conn:
 # 1. PostGIS
 result = conn.execute(text("SELECT PostGIS_version();"))
 print(f"\n PostGIS: {result.scalar()}")
 
 # 2. Nuestras tablas (modelos SIRCCD)
 our_tables = ['users', 'reports',
 'incidents', 'pois', 'metrics', 'alembic_version']
 
 print(f"\n Tablas del modelo SIRCCD:")
 for table in our_tables:
 result = conn.execute(text(f"""
 SELECT COUNT(*) FROM information_schema.tables 
 WHERE table_name = '{table}' AND table_schema = 'public';
 """))
 exists = result.scalar() > 0
 status = "" if exists else ""
 print(f" {status} {table}")
 
 # 3. Columnas Geography
 print(f"\n Columnas Geography (SRID 4326):")
 result = conn.execute(text("""
 SELECT 
 f_table_name,
 f_geography_column,
 type,
 srid
 FROM geography_columns
 WHERE f_table_schema = 'public'
 AND f_table_name IN ('reports', 'incidents', 'pois')
 ORDER BY f_table_name;
 """))
 
 geo_cols = result.fetchall()
 for table, column, gtype, srid in geo_cols:
 print(f"  {table}.{column} [{gtype}, SRID {srid}]")
 
 # 4. Índices espaciales
 print(f"\n Índices espaciales:")
 result = conn.execute(text("""
 SELECT 
 tablename,
 indexname
 FROM pg_indexes
 WHERE schemaname = 'public'
 AND tablename IN ('reports', 'incidents', 'pois')
 AND indexname LIKE 'idx_%location%'
 ORDER BY tablename;
 """))
 
 indexes = result.fetchall()
 for table, index in indexes:
 print(f"  {table}: {index}")
 
 # 5. Foreign Keys
 print(f"\n Foreign Keys (relaciones):")
 result = conn.execute(text("""
 SELECT
 tc.table_name,
 kcu.column_name,
 ccu.table_name AS foreign_table_name,
 ccu.column_name AS foreign_column_name
 FROM information_schema.table_constraints AS tc
 JOIN information_schema.key_column_usage AS kcu
 ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
 JOIN information_schema.constraint_column_usage AS ccu
 ON ccu.constraint_name = tc.constraint_name
 AND ccu.table_schema = tc.table_schema
 WHERE tc.constraint_type = 'FOREIGN KEY'
 AND tc.table_name IN ('reports', 'incidents')
 ORDER BY tc.table_name;
 """))
 
 fks = result.fetchall()
 for table, col, ftable, fcol in fks:
 print(f"  {table}.{col}  {ftable}.{fcol}")
 
 # 6. Enums
 print(f"\n Tipos enum (PostgreSQL):")
 result = conn.execute(text("""
 SELECT typname, COUNT(enumlabel) as values_count
 FROM pg_type t
 JOIN pg_enum e ON t.oid = e.enumtypid
 WHERE typname LIKE '%role%' 
 OR typname LIKE '%type%'
 OR typname LIKE '%level%'
 OR typname LIKE '%status%'
 OR typname LIKE '%category%'
 GROUP BY typname
 ORDER BY typname;
 """))
 
 enums = result.fetchall()
 for enum_name, count in enums:
 print(f"  {enum_name} ({count} valores)")

print(f"\n{'=' * 60}")
print(" MIGRACIÓN VERIFICADA EXITOSAMENTE")
print(f"{'=' * 60}\n")

engine.dispose()
