"""
Backfill del desglose de prioridad (priority_breakdown) de los incidentes.

Contexto: GET /incidents/{id}/priority-breakdown recalculaba el factor de
duplicados con similitud visual (descarga de imágenes + ResNet50) en cada
apertura del incidente, tardando ~30s. Ahora el desglose se persiste en la
columna incidents.priority_breakdown. Este script lo calcula una vez, del lado
del servidor (sin el timeout del cliente), para los incidentes que aún no lo
tienen.

Ejecutar una sola vez tras aplicar la migración 007:

    python -m scripts.maintenance.backfill_priority_breakdown        # solo faltantes
    python -m scripts.maintenance.backfill_priority_breakdown --all  # recalcular todos
"""

import sys
from pathlib import Path

# Raíz del backend en el path (…/backend), para importar db/, models/, services/.
backend_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from models.incident import Incident
from services.priority_service import get_priority_service


def backfill_priority_breakdown(recalc_all: bool = False) -> None:
    db = SessionLocal()
    try:
        query = db.query(Incident)
        if not recalc_all:
            query = query.filter(Incident.priority_breakdown.is_(None))
        incidents = query.order_by(Incident.id.asc()).all()

        total = len(incidents)
        print(f"[INFO] Incidentes a procesar: {total} (recalc_all={recalc_all})")
        if total == 0:
            print("[OK] Nada que hacer.")
            return

        priority_service = get_priority_service(db)
        done = 0
        failed = 0

        for incident in incidents:
            try:
                incident.priority_breakdown = priority_service.calculate_priority_breakdown(
                    incident, visual_dedup=True
                )
                db.commit()
                done += 1
                print(f"[OK] Incidente {incident.id} ({done}/{total})")
            except Exception as exc:  # noqa: BLE001 - registrar y continuar
                db.rollback()
                failed += 1
                print(f"[ERROR] Incidente {incident.id}: {exc}")

        print(f"\n[RESUMEN] procesados={done} fallidos={failed} total={total}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_priority_breakdown(recalc_all="--all" in sys.argv)
