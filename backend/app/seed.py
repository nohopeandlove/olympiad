"""Development accounts for the one official adventure, without legacy demo events."""
from datetime import date, timedelta
from sqlalchemy import select
from .db import SessionLocal
from .models import User, Registration, Stage, now
from .security import hasher
from .config import settings
from .academy import create_academy

PASSWORD='DevOnly!Python2026'
def main():
    if settings.app_env!='development':raise RuntimeError('Development seed запрещён в production')
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email=='admin@example.org')):
            print('Seed уже существует');return
        fresh=not db.scalar(select(User.id).limit(1))
        users=[]
        for email,last,first,role in [('admin@example.org','Администратор','Платформы','admin'),('school@example.org','Иванов','Алексей','participant'),('spo1@example.org','Петрова','Мария','participant'),('spo2@example.org','Смирнов','Дмитрий','participant')]:
            user=db.scalar(select(User).where(User.email==email))
            if not user:
                user=User(email=email,password_hash=hasher.hash(PASSWORD),last_name=last,first_name=first,role=role,birth_date=date(2008,5,15),phone='+79000000000',region='Челябинская область',city='Челябинск',organization='Демонстрационная образовательная организация',verified=True)
                db.add(user);db.flush()
            users.append(user)
        for audience,members in [('SCHOOL',[(users[1],10)]),('SPO',[(users[2],1),(users[3],2)])]:
            event,_=create_academy(db,audience)
            if fresh:
                timestamp=now();event.status='active';event.registration_start=timestamp-timedelta(days=1);event.registration_end=timestamp+timedelta(days=7)
                for stage in db.scalars(select(Stage).where(Stage.olympiad_id==event.id)):
                    stage.starts_at=timestamp-timedelta(hours=1) if stage.kind=='qualifying' else timestamp+timedelta(days=8)
                    stage.ends_at=timestamp+timedelta(days=7 if stage.kind=='qualifying' else 9)
            for user,level in members:
                if not db.scalar(select(Registration).where(Registration.user_id==user.id,Registration.olympiad_id==event.id)):
                    db.add(Registration(user_id=user.id,olympiad_id=event.id,school_class=level if audience=='SCHOOL' else None,course=level if audience=='SPO' else None))
        db.commit();print('Development seed создан: одно приключение, школьники и СПО')
if __name__=='__main__':main()
