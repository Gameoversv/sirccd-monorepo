"""add priority settings table

Revision ID: 002
Revises: 001
Create Date: 2026-04-12 19:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "priority_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("weight_severity", sa.Float(), nullable=False, server_default="0.35"),
        sa.Column("weight_age", sa.Float(), nullable=False, server_default="0.20"),
        sa.Column("weight_damage_type", sa.Float(), nullable=False, server_default="0.15"),
        sa.Column("weight_location", sa.Float(), nullable=False, server_default="0.20"),
        sa.Column("weight_duplicates", sa.Float(), nullable=False, server_default="0.10"),
        sa.Column("poi_radius_meters", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("duplicate_radius_meters", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("duplicate_time_window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_priority_settings_id"), "priority_settings", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_priority_settings_id"), table_name="priority_settings")
    op.drop_table("priority_settings")

