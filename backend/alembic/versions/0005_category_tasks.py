"""Different category tasks and ten main-stage chapters, preserving live attempts."""
from alembic import op
from sqlalchemy.orm import Session
from app.academy_updates import upgrade_academy_content

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    db = Session(bind=op.get_bind())
    for audience, item, reason in upgrade_academy_content(db):
        print(f'Academy content: {audience}: {item}: {reason}')


def downgrade():
    pass  # Content rollback must never delete students' work.
