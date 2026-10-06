import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Boolean, JSON, UniqueConstraint, Date
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(default='participant')
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str] = mapped_column(String(100), default='')
    birth_date: Mapped[datetime] = mapped_column(Date)
    phone: Mapped[str] = mapped_column(String(30))
    region: Mapped[str] = mapped_column(String(150))
    city: Mapped[str] = mapped_column(String(150))
    organization: Mapped[str] = mapped_column(String(300))
    verified: Mapped[bool] = mapped_column(default=False)
    blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Olympiad(Base):
    __tablename__ = 'olympiads'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default='')
    rules: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(default='draft')
    registration_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    allowed_classes: Mapped[list] = mapped_column(JSON, default=lambda: [7,8,9,10,11])
    ranking_visible: Mapped[bool] = mapped_column(default=False)

class Registration(Base):
    __tablename__ = 'olympiad_registrations'
    __table_args__ = (UniqueConstraint('user_id','olympiad_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    olympiad_id: Mapped[str] = mapped_column(ForeignKey('olympiads.id'))
    school_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    course: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group: Mapped[str] = mapped_column(String(100), default='')
    status: Mapped[str] = mapped_column(default='registered')
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Stage(Base):
    __tablename__ = 'stages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    olympiad_id: Mapped[str] = mapped_column(ForeignKey('olympiads.id'))
    title: Mapped[str] = mapped_column(String(150))
    kind: Mapped[str] = mapped_column(default='qualifying')
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=120)

class Attempt(Base):
    __tablename__ = 'participants'
    __table_args__ = (UniqueConstraint('registration_id','stage_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    registration_id: Mapped[str] = mapped_column(ForeignKey('olympiad_registrations.id'))
    stage_id: Mapped[str] = mapped_column(ForeignKey('stages.id'))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_hash: Mapped[str] = mapped_column(String(64))
    finished: Mapped[bool] = mapped_column(default=False)

class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    olympiad_id: Mapped[str] = mapped_column(ForeignKey('olympiads.id'))
    stage_id: Mapped[str] = mapped_column(ForeignKey('stages.id'))
    title: Mapped[str] = mapped_column(String(200))
    statement: Mapped[str] = mapped_column(Text)
    input_description: Mapped[str] = mapped_column(Text, default='')
    output_description: Mapped[str] = mapped_column(Text, default='')
    constraints: Mapped[str] = mapped_column(Text, default='')
    difficulty: Mapped[str] = mapped_column(default='normal')
    time_limit: Mapped[int] = mapped_column(default=2)
    memory_limit: Mapped[int] = mapped_column(default=128)
    points: Mapped[int] = mapped_column(default=100)

class TestCase(Base):
    __tablename__ = 'test_cases'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    task_id: Mapped[str] = mapped_column(ForeignKey('tasks.id'))
    input: Mapped[str] = mapped_column(Text)
    expected: Mapped[str] = mapped_column(Text)
    public: Mapped[bool] = mapped_column(default=False)

class Submission(Base):
    __tablename__ = 'submissions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    olympiad_id: Mapped[str] = mapped_column(ForeignKey('olympiads.id'))
    stage_id: Mapped[str] = mapped_column(ForeignKey('stages.id'))
    task_id: Mapped[str] = mapped_column(ForeignKey('tasks.id'))
    code: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(default='submit')
    status: Mapped[str] = mapped_column(default='Queued')
    score: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SubmissionResult(Base):
    __tablename__ = 'submission_results'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey('submissions.id'), unique=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)

class Draft(Base):
    __tablename__ = 'drafts'
    __table_args__ = (UniqueConstraint('user_id','task_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    task_id: Mapped[str] = mapped_column(ForeignKey('tasks.id'))
    code: Mapped[str] = mapped_column(Text, default='')

class Session(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Verification(Base):
    __tablename__ = 'email_verifications'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class AntiCheatEvent(Base):
    __tablename__ = 'anti_cheat_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    participant_id: Mapped[str] = mapped_column(ForeignKey('olympiad_registrations.id'))
    olympiad_id: Mapped[str] = mapped_column(ForeignKey('olympiads.id'))
    stage_id: Mapped[str] = mapped_column(ForeignKey('stages.id'))
    event_type: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    metadata_json: Mapped[dict] = mapped_column('metadata', JSON, default=dict)
    severity: Mapped[str] = mapped_column(default='info')

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
