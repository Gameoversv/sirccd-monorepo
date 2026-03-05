"""
Script para crear incidentes a partir de reportes existentes

Este script convierte reportes aprobados en incidentes.
"""

import sys
from pathlib import Path

# Añadir el directorio backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from models.report import Report, ReportStatus
from models.incident import Incident, IncidentStatus, PriorityLevel
from services.priority_service import get_priority_service


def create_incidents_from_reports():
    """Convierte todos los reportes PROCESSING/APPROVED en incidentes"""
    
    db = SessionLocal()
    try:
        # Contar reportes e incidentes existentes
        total_reports = db.query(Report).count()
        total_incidents = db.query(Incident).count()
        
        print(f"\n[INFO] Estado actual de la base de datos:")
        print(f"  - Reportes totales: {total_reports}")
        print(f"  - Incidentes totales: {total_incidents}")
        
        # Obtener reportes que pueden convertirse a incidentes
        # Filtrar: sin incidente asociado y en estado PROCESSING o APPROVED
        eligible_reports = db.query(Report).filter(
            ~Report.id.in_(
                db.query(Incident.report_id)
            ),
            Report.status.in_([ReportStatus.PROCESSING, ReportStatus.APPROVED])
        ).all()
        
        print(f"\n[INFO] Reportes elegibles para convertir: {len(eligible_reports)}")
        
        if len(eligible_reports) == 0:
            print("\n[OK] No hay reportes que convertir a incidentes.")
            return
        
        # Obtener servicio de priorización
        priority_service = get_priority_service(db)
        
        # Crear incidentes
        created_count = 0
        for report in eligible_reports:
            try:
                # Crear nuevo incidente
                new_incident = Incident(
                    report_id=report.id,
                    reported_by=report.user_id,
                    location=report.location,
                    address=report.address,
                    city=report.city,
                    province=report.province,
                    damage_type=report.damage_type,
                    severity=report.severity,
                    priority=PriorityLevel.MEDIA,  # Placeholder, se calculará después
                    priority_score=0.0,
                    status=IncidentStatus.OPEN,
                    before_image_url=report.image_url,
                    notes=report.description
                )
                
                db.add(new_incident)
                db.flush()  # Para obtener el ID
                
                # Calcular prioridad
                try:
                    priority_level, score = priority_service.calculate_priority(new_incident)
                    new_incident.priority = priority_level
                    new_incident.priority_score = score
                except Exception as e:
                    print(f"  [WARN] No se pudo calcular prioridad para incidente {new_incident.id}: {e}")
                
                created_count += 1
                print(f"  [OK] Incidente #{new_incident.id} creado desde reporte #{report.id} (Prioridad: {new_incident.priority}, Score: {new_incident.priority_score:.2f})")
                
            except Exception as e:
                print(f"  [ERROR] Error creando incidente para reporte #{report.id}: {e}")
                db.rollback()
                continue
        
        # Commit final
        if created_count > 0:
            db.commit()
            print(f"\n[SUCCESS] Se crearon {created_count} incidentes exitosamente.")
        else:
            print(f"\n[WARN] No se pudo crear ningún incidente.")
        
    except Exception as e:
        print(f"\n[ERROR] Error general: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  CONVERTIR REPORTES A INCIDENTES")
    print("=" * 60)
    
    create_incidents_from_reports()
    
    print("\n" + "=" * 60)
    print("  PROCESO COMPLETADO")
    print("=" * 60)
