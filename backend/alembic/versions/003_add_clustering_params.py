"""add clustering params to priority_settings

Revision ID: 003
Revises: 002
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "priority_settings",
        sa.Column("clustering_eps_meters", sa.Integer(), nullable=False, server_default="50"),
    )
    op.add_column(
        "priority_settings",
        sa.Column("clustering_min_samples", sa.Integer(), nullable=False, server_default="2"),
    )


def downgrade() -> None:
    op.drop_column("priority_settings", "clustering_min_samples")
    op.drop_column("priority_settings", "clustering_eps_meters")
