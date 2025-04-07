"""Add feedback model

Revision ID: ddb46ecb8a1f
Revises: 1234567890ab
Create Date: 2025-04-07 14:00:19.930225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddb46ecb8a1f'
down_revision: Union[str, None] = '1234567890ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Проверяем существование таблицы (опционально)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table('feedbacks'):
        return  # или можно вызвать создание таблицы

    # 1. Сначала удаляем старый foreign key
    op.drop_constraint('fk_feedbacks_user_id', 'feedbacks', type_='foreignkey')

    # 2. Меняем тип колонки
    op.alter_column('feedbacks', 'user_email',
           existing_type=sa.UUID(),
           type_=sa.String(),
           existing_nullable=False,
           postgresql_using='user_email::text')

    # 3. Создаем новый foreign key
    op.create_foreign_key(
        'fk_feedbacks_user_email',
        'feedbacks', 'users',
        ['user_email'], ['email'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # 1. Удаляем новый foreign key
    op.drop_constraint('fk_feedbacks_user_email', 'feedbacks', type_='foreignkey')

    # 2. Возвращаем тип колонки
    op.alter_column('feedbacks', 'user_email',
           existing_type=sa.String(),
           type_=sa.UUID(),
           existing_nullable=False,
           postgresql_using='user_email::uuid')

    # 3. Восстанавливаем старый foreign key
    op.create_foreign_key(
        'fk_feedbacks_user_id',
        'feedbacks', 'users',
        ['user_email'], ['id'],
        ondelete='CASCADE'
    )