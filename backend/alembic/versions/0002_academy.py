"""Keep the chapter order and identity when an adventure task is edited."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('tasks', sa.Column('academy_chapter', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('tasks', 'academy_chapter')
