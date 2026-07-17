"""
Backfill de enlaces de reportes fusionados en incidentes.

Antes de persistir la membresía, el auto-aprobado fusionaba un reporte duplicado
en un incidente existente (resolve_incident_dedup) pero no guardaba el vínculo:
el reporte quedaba APPROVED, sin incidente propio y sin duplicate_of_report_id.
Por eso un incidente podía "detectar" duplicados sin poder mostrarlos.

Este script recupera esos reportes (APPROVED, sin incidente propio, sin enlace) y
reejecuta la lógica de fusión para enlazarlos al reporte primario de su incidente.
Requiere descargar imágenes + embedding, así que puede tardar.

Ejecutar tras desplegar el fix:

    python -m scripts.maintenance.backfill_merged_report_links
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from models.report import Report, ReportStatus
from models.incident import Incident
from services.report_processing_service import resolve_incident_dedup
from services.deduplication_service import load_image_from_url


def backfill_merged_report_links() -> None:
    db = SessionLocal()
    try:
        # Reportes aprobados que no son primarios de ningún incidente y no están
        # enlazados: candidatos a haber sido fusionados sin persistir el vínculo.
        primary_ids = db.query(Incident.report_id)
        candidates = (
            db.query(Report)
            .filter(
                Report.status == ReportStatus.APPROVED,
                Report.duplicate_of_report_id.is_(None),
                Report.id.notin_(primary_ids),
            )
            .order_by(Report.id.asc())
            .all()
        )

        print(f"[INFO] Reportes candidatos (aprobados, sin incidente ni enlace): {len(candidates)}")
        linked = 0
        no_match = 0
        failed = 0

        for report in candidates:
            try:
                image = load_image_from_url(report.image_url) if report.image_url else None
                incident = resolve_incident_dedup(db, report, image)
                if incident is None:
                    no_match += 1
                    continue

                report.duplicate_of_report_id = incident.report_id
                db.commit()
                linked += 1
                print(f"[OK] Reporte {report.id} -> incidente {incident.id} (primario {incident.report_id})")
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                failed += 1
                print(f"[ERROR] Reporte {report.id}: {exc}")

        print(f"\n[RESUMEN] enlazados={linked} sin_match={no_match} fallidos={failed} total={len(candidates)}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_merged_report_links()
