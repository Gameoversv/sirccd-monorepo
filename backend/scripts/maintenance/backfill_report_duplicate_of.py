"""
Backfill de reports.duplicate_of_report_id a partir de rejection_reason.

Antes de la migración 008 la membresía de duplicados (M-13) solo quedaba como
texto libre: "Duplicado espacial — cluster M-13 #<n>, reporte primario #<id>".
Este script extrae ese id primario y rellena la nueva FK para los reportes ya
rechazados como duplicados, de modo que los incidentes existentes muestren su
grupo completo.

Ejecutar una sola vez tras aplicar la migración 008:

    python -m scripts.maintenance.backfill_report_duplicate_of
"""

import re
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from models.report import Report, ReportStatus

# Captura el id del reporte primario del texto de rechazo.
_PRIMARY_RE = re.compile(r"reporte primario #(\d+)")


def backfill_report_duplicate_of() -> None:
    db = SessionLocal()
    try:
        candidates = (
            db.query(Report)
            .filter(
                Report.status == ReportStatus.REJECTED,
                Report.duplicate_of_report_id.is_(None),
                Report.rejection_reason.isnot(None),
            )
            .all()
        )

        print(f"[INFO] Reportes rechazados sin FK: {len(candidates)}")
        updated = 0
        skipped = 0

        for report in candidates:
            match = _PRIMARY_RE.search(report.rejection_reason or "")
            if not match:
                skipped += 1
                continue

            primary_id = int(match.group(1))
            if primary_id == report.id:
                skipped += 1
                continue

            report.duplicate_of_report_id = primary_id
            updated += 1

        db.commit()
        print(f"[RESUMEN] actualizados={updated} sin_match={skipped} total={len(candidates)}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_report_duplicate_of()
