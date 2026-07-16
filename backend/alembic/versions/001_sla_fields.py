"""add sla_deadline to incidents and create sla_configs table (P-06)

Revision ID: 001_sla_fields
Revises: 005
Create Date: 2026-05-05
"""

from alembic import op
import sqlalchemy as sa

revision = "001_sla_fields"
# Depende de la cadena 001..005: altera la tabla `incidents`, que crea la
# migracion inicial. Con down_revision = None quedaba como una segunda raiz,
# dejando dos heads ("Multiple head revisions are present") y ordenandose
# antes de que `incidents` existiera.
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("sla_deadline", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_incidents_sla_deadline", "incidents", ["sla_deadline"])

    op.create_table(
        "sla_configs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sla_hours_baja", sa.Float(), nullable=False, server_default="72.0"),
        sa.Column("sla_hours_media", sa.Float(), nullable=False, server_default="48.0"),
        sa.Column("sla_hours_alta", sa.Float(), nullable=False, server_default="24.0"),
        sa.Column("sla_hours_critica", sa.Float(), nullable=False, server_default="8.0"),
        sa.Column("warning_threshold_pct", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_index("ix_incidents_sla_deadline", table_name="incidents")
    op.drop_column("incidents", "sla_deadline")
    op.drop_table("sla_configs")
