"""Add new column to verify code model

Revision ID: 584f54b78e86
Revises: ddb46ecb8a1f
Create Date: 2025-04-16 11:13:28.403515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '584f54b78e86'
down_revision: Union[str, None] = 'ddb46ecb8a1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    codetype = postgresql.ENUM(
        'for_registration',
        'for_reset_password',
        name='codetype'
    )
    codetype.create(op.get_bind())

    op.add_column(
        'verify_codes',
        sa.Column(
            'type',
            codetype,
            nullable=True,
            server_default='for_registration'  # Дефолтное значение
        )
    )

    op.alter_column('verify_codes', 'type', nullable=False)


def downgrade() -> None:
    op.drop_column('verify_codes', 'type')

    codetype = postgresql.ENUM(
        'for_registration',
        'for_reset_password',
        name='codetype'
    )
    codetype.drop(op.get_bind())
