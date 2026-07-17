"""persistir el desglose de prioridad del incidente

La vista de detalle llama a GET /incidents/{id}/priority-breakdown al abrir el
incidente. Ese desglose recalculaba el factor de duplicados con similitud visual
(descarga de imágenes de MinIO + embedding ResNet50) de forma síncrona, tardando
~30s y provocando timeouts (499). Se persiste el desglose en una columna JSON
para servirlo de inmediato; se rellena al recalcular la prioridad o vía backfill.

Revision ID: 007
Revises: 006
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("priority_breakdown", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("incidents", "priority_breakdown")
