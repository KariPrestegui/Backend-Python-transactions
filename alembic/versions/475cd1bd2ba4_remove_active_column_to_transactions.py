from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '475cd1bd2ba4'
down_revision: Union[str, None] = 'c4a5f61dd408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('transactions', 'active')


def downgrade() -> None:
    op.add_column('transactions', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=False))
