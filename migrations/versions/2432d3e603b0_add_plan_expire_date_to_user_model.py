"""Add plan expire date to user model

Revision ID: 2432d3e603b0
Revises: 584f54b78e86
Create Date: 2025-04-18 11:02:38.540319

"""
from typing import Sequence, Union
from datetime import datetime, timedelta

from alembic import op
import sqlalchemy as sa

revision: str = '2432d3e603b0'
down_revision: Union[str, None] = '584f54b78e86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('plan_expire_date', sa.Date(), nullable=True))
    expire_date = (datetime.utcnow() + timedelta(days=28)).date()

    op.execute(
        sa.text("UPDATE users SET plan_expire_date = :expire_date WHERE plan_expire_date IS NULL")
        .bindparams(expire_date=expire_date)
    )

    op.alter_column('users', 'plan_expire_date', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'plan_expire_date')
