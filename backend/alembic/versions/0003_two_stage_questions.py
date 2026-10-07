"""Mixed tasks, manual assessment and durable server-side task timers."""
from alembic import op
import sqlalchemy as sa
revision='0003'
down_revision='0002'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('stages',sa.Column('story_intro',sa.Text(),nullable=False,server_default=''))
    op.add_column('participants',sa.Column('active_task_id',sa.String(36),nullable=True))
    op.add_column('participants',sa.Column('task_last_seen_at',sa.DateTime(timezone=True),nullable=True))
    for column in [sa.Column('kind',sa.String(20),nullable=False,server_default='code'),sa.Column('position',sa.Integer(),nullable=False,server_default='0'),sa.Column('answer_options',sa.JSON(),nullable=False,server_default='[]'),sa.Column('correct_option',sa.Integer(),nullable=True),sa.Column('rubric',sa.Text(),nullable=False,server_default='')]:
        op.add_column('tasks',column)
    op.add_column('submissions',sa.Column('review_feedback',sa.Text(),nullable=False,server_default=''))
    op.add_column('submissions',sa.Column('reviewed_by',sa.String(36),sa.ForeignKey('users.id'),nullable=True))
    op.add_column('submissions',sa.Column('reviewed_at',sa.DateTime(timezone=True),nullable=True))
    op.create_table('task_times',sa.Column('id',sa.String(36),primary_key=True),sa.Column('attempt_id',sa.String(36),sa.ForeignKey('participants.id'),nullable=False),sa.Column('task_id',sa.String(36),sa.ForeignKey('tasks.id'),nullable=False),sa.Column('elapsed_ms',sa.Integer(),nullable=False),sa.Column('first_opened_at',sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint('attempt_id','task_id'))
    op.execute("UPDATE olympiads SET allowed_classes='[10,11]'::json WHERE type='SCHOOL'")

def downgrade():
    op.drop_table('task_times')
    for name in ['reviewed_at','reviewed_by','review_feedback']:op.drop_column('submissions',name)
    for name in ['rubric','correct_option','answer_options','position','kind']:op.drop_column('tasks',name)
    op.drop_column('participants','task_last_seen_at');op.drop_column('participants','active_task_id')
    op.drop_column('stages','story_intro')
