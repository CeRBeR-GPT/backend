"""Add plan expire date to transaction model

Revision ID: a074d5a43533
Revises: 2432d3e603b0
Create Date: 2025-04-18 21:49:21.732938

"""
from typing import Sequence, Union
from datetime import date, timedelta

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = 'a074d5a43533'
down_revision: Union[str, None] = '2432d3e603b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('plan_expire_date', sa.Date(), nullable=True))

    expire_date = date.today() + timedelta(days=28)

    op.execute(
        text("UPDATE transactions SET plan_expire_date = :expire_date WHERE plan_expire_date IS NULL")
        .bindparams(expire_date=expire_date)
    )

    op.alter_column('transactions', 'plan_expire_date', nullable=False)


def downgrade() -> None:
    op.drop_column('transactions', 'plan_expire_date')
