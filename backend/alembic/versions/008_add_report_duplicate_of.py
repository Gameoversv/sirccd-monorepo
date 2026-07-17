"""agrupar duplicados: reports.duplicate_of_report_id

Persiste la membresía de los clusters de duplicados (M-13). Hasta ahora el
vínculo del duplicado con su primario solo quedaba como texto libre en
rejection_reason y el cluster_id se recalculaba en cada corrida, así que no había
forma fiable de listar, desde un incidente, los reportes agrupados. Esta columna
FK (self-referential a reports.id) lo hace explícito: el primario tiene NULL y
cada duplicado apunta a su primario.

Revision ID: 008
Revises: 007
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("duplicate_of_report_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_reports_duplicate_of_report_id",
        "reports",
        ["duplicate_of_report_id"],
    )
    op.create_foreign_key(
        "fk_reports_duplicate_of_report_id",
        "reports",
        "reports",
        ["duplicate_of_report_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_reports_duplicate_of_report_id", "reports", type_="foreignkey"
    )
    op.drop_index("ix_reports_duplicate_of_report_id", table_name="reports")
    op.drop_column("reports", "duplicate_of_report_id")
