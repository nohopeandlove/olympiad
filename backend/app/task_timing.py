"""Count one visible task per attempt, using server time and a bounded lease."""
from datetime import timedelta
from sqlalchemy import select
from .models import TaskTime, now

LEASE_SECONDS=30

def pending_ms(attempt, stage, timestamp):
    if not attempt.active_task_id or not attempt.task_last_seen_at:return 0
    end=min(timestamp,attempt.deadline,stage.ends_at,attempt.task_last_seen_at+timedelta(seconds=LEASE_SECONDS))
    return max(0,int((end-attempt.task_last_seen_at).total_seconds()*1000))

def checkpoint(db, attempt, stage, timestamp=None):
    timestamp=timestamp or now()
    if attempt.active_task_id:
        row=db.scalar(select(TaskTime).where(TaskTime.attempt_id==attempt.id,TaskTime.task_id==attempt.active_task_id))
        if row:row.elapsed_ms+=pending_ms(attempt,stage,timestamp)
    attempt.task_last_seen_at=timestamp

def snapshot(db, attempt, stage, timestamp=None):
    timestamp=timestamp or now()
    rows=[]
    for timing in db.scalars(select(TaskTime).where(TaskTime.attempt_id==attempt.id)):
        active=attempt.active_task_id==timing.task_id and not attempt.finished
        until=min(attempt.deadline,stage.ends_at,attempt.task_last_seen_at+timedelta(seconds=LEASE_SECONDS)) if active and attempt.task_last_seen_at else None
        rows.append({'task_id':timing.task_id,'elapsed_ms':timing.elapsed_ms+(pending_ms(attempt,stage,timestamp) if active else 0),'active_until':until if until and until>timestamp else None})
    return {'timings':rows,'server_time':timestamp}
