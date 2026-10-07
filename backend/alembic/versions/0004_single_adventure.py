"""Install the single adventure and retain legacy events as stored history."""
from alembic import op
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.academy import create_academy
from app.models import Olympiad, Registration, User
revision='0004'
down_revision='0003'
branch_labels=None
depends_on=None

def upgrade():
    db=Session(bind=op.get_bind())
    for audience in ('SCHOOL','SPO'):
        event,created=create_academy(db,audience)
        # Publish an unused draft so updating an existing installation needs no import button.
        if event.status=='draft':event.status='scheduled'
        db.flush()
        existing=set(db.scalars(select(Registration.user_id).where(Registration.olympiad_id==event.id)))
        legacy=db.scalars(select(Registration).join(Olympiad,Olympiad.id==Registration.olympiad_id).where(Olympiad.type==audience,Registration.olympiad_id!=event.id).order_by(Registration.consent_at.desc())).all()
        for old in legacy:
            if old.user_id in existing or db.get(User,old.user_id).role=='admin':continue
            db.add(Registration(user_id=old.user_id,olympiad_id=event.id,school_class=old.school_class,course=old.course,group=old.group,status=old.status,consent_at=old.consent_at))
            existing.add(old.user_id)
        db.flush()
    # Old submissions, attempts, deadlines and registrations are deliberately retained.

def downgrade():
    pass  # Never delete participant data when rolling back the catalogue view.
