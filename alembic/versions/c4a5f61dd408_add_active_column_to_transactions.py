
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c4a5f61dd408'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('active', sa.Boolean(), nullable=False))
    op.drop_constraint(op.f('transactions_idempotency_key_key'), 'transactions', type_='unique')
    op.drop_index(op.f('ix_transactions_idempotency_key'), table_name='transactions')
    op.create_index(op.f('ix_transactions_idempotency_key'), 'transactions', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_idempotency_key'), table_name='transactions')
    op.create_index(op.f('ix_transactions_idempotency_key'), 'transactions', ['idempotency_key'], unique=False)
    op.create_unique_constraint(op.f('transactions_idempotency_key_key'), 'transactions', ['idempotency_key'], postgresql_nulls_not_distinct=False)
    op.drop_column('transactions', 'active')
