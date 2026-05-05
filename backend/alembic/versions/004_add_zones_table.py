"""add zones table

Revision ID: 004
Revises: 003
Create Date: 2026-05-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column(
            "boundary",
            Geography(geometry_type="POLYGON", srid=4326),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_zones_id"), "zones", ["id"], unique=False)
    op.create_index(op.f("ix_zones_name"), "zones", ["name"], unique=True)
    op.create_index(op.f("ix_zones_code"), "zones", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_zones_code"), table_name="zones")
    op.drop_index(op.f("ix_zones_name"), table_name="zones")
    op.drop_index(op.f("ix_zones_id"), table_name="zones")
    op.drop_table("zones")
