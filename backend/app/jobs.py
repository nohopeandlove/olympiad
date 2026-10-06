import httpx
from celery import Celery
from sqlalchemy import select
from .config import settings
from .db import SessionLocal
from .models import Submission, Task, TestCase, SubmissionResult, Notification

celery = Celery('olympiad', broker=settings.redis_url)
celery.conf.update(task_serializer='json', accept_content=['json'], worker_prefetch_multiplier=1, task_soft_time_limit=580, task_time_limit=600, broker_connection_retry_on_startup=True)

@celery.task(name='judge_submission')
def judge_submission(id):
    with SessionLocal() as db:
        s=db.get(Submission,id)
        if not s or s.status!='Queued': return
        s.status='Running'; db.commit()
        task=db.get(Task,s.task_id)
        cases=list(db.scalars(select(TestCase).where(TestCase.task_id==task.id)))
        if s.mode=='run': cases=[c for c in cases if c.public]
        try:
            if not cases: raise ValueError('No tests')
            with httpx.Client(timeout=550,trust_env=False) as client:
                response=client.post(settings.judge_url+'/judge',headers={'Authorization':'Bearer '+settings.judge_token},json={'code':s.code,'time_limit':task.time_limit,'memory_limit':task.memory_limit,'tests':[{'input':c.input,'expected':c.expected} for c in cases],'public_run':s.mode=='run'})
                response.raise_for_status(); result=response.json()
            s.status=result['status']
            s.score=(task.points*result['passed']//len(cases)) if s.mode=='submit' else 0
            # The judge never returns hidden input/output, stdout or exception text for official submissions.
            db.add(SubmissionResult(submission_id=id,detail=result))
        except Exception:
            s.status='System Error'; s.score=0
            db.add(SubmissionResult(submission_id=id,detail={'message':'Ошибка инфраструктуры проверки. Обратитесь к администратору.'}))
        db.add(Notification(user_id=s.user_id,message=f'Проверка «{task.title}»: {s.status}, {s.score} баллов'))
        db.commit()
