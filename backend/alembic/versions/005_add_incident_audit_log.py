"""add incident audit log table

Revision ID: 005
Revises: 004
Create Date: 2026-05-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incident_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("incident_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("old_value", sa.String(length=500), nullable=True),
        sa.Column("new_value", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incident_audit_logs_id"), "incident_audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_incident_audit_logs_incident_id"), "incident_audit_logs", ["incident_id"], unique=False)
    op.create_index(op.f("ix_incident_audit_logs_event_type"), "incident_audit_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_incident_audit_logs_created_at"), "incident_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_incident_audit_logs_created_at"), table_name="incident_audit_logs")
    op.drop_index(op.f("ix_incident_audit_logs_event_type"), table_name="incident_audit_logs")
    op.drop_index(op.f("ix_incident_audit_logs_incident_id"), table_name="incident_audit_logs")
    op.drop_index(op.f("ix_incident_audit_logs_id"), table_name="incident_audit_logs")
    op.drop_table("incident_audit_logs")
