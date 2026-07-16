"""ensanchar users.phone para el texto cifrado (S-03)

El modelo pasó a EncryptedString(200) al cifrar el campo, pero la columna
siguió siendo la varchar(20) que creó la migración inicial. Con
FIELD_ENCRYPTION_KEY configurada, el cifrado Fernet de un telefono ocupa ~100
caracteres y el registro fallaba con 500:

    psycopg2.errors.StringDataRightTruncation:
    value too long for type character varying(20)

En desarrollo no se notaba porque sin FIELD_ENCRYPTION_KEY el valor se guarda
en claro y si cabe en 20.

Revision ID: 006
Revises: 001_sla_fields
Create Date: 2026-07-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "001_sla_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "phone",
        existing_type=sa.String(length=20),
        type_=sa.String(length=200),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Los telefonos cifrados no caben en 20: truncarlos los haria indescifrables.
    op.execute("UPDATE users SET phone = NULL WHERE length(phone) > 20")
    op.alter_column(
        "users",
        "phone",
        existing_type=sa.String(length=200),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
