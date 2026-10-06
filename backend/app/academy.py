"""The authored task pack. Tests and the ending stay on the backend."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from datetime import timedelta
from sqlalchemy import select
from .models import Olympiad, Stage, Task, TestCase, Submission, now
from .schemas import TaskInput

PACK = json.loads((Path(__file__).parent / 'content' / 'academy.json').read_text())

def task_input(chapter):
    fields = {k: v for k, v in chapter.items() if k not in {'chapter', 'stars', 'topic'}}
    return TaskInput(**fields, academy_chapter=chapter['chapter'])

def academy_id(audience):
    return str(uuid5(NAMESPACE_URL, PACK['key'] + ':' + audience))

def create_academy(db, audience):
    """One atomic, repeatable import per audience; do not alter existing events."""
    oid = academy_id(audience)
    existing = db.get(Olympiad, oid)
    if existing:
        return existing, False
    timestamp = now()
    event = Olympiad(id=oid, type=audience, title=PACK['title'], description=PACK['intro'],
        rules='## Миссия\nВосстановите работу Академии, решив восемь задач на Python 3. '
              'Главы расположены по порядку сюжета, но решения можно отправлять в любом порядке. '
              'Все задания оцениваются в 100 баллов; максимум — 800. '
              'Баллы начисляются по доле пройденных проверок. Решайте самостоятельно. '
              'Время этапа контролируется сервером. Финал откроется после принятого официального решения последней задачи.',
        status='draft', registration_start=timestamp,
        registration_end=timestamp + timedelta(days=7), ranking_visible=False)
    db.add(event)
    db.flush()
    stage = Stage(olympiad_id=oid, title='Сбой в Академии Алгоритмов · восемь глав', kind='main',
        starts_at=timestamp + timedelta(days=8), ends_at=timestamp + timedelta(days=9), duration_minutes=180)
    db.add(stage)
    db.flush()
    for chapter in PACK['tasks']:
        data = task_input(chapter)
        task = Task(olympiad_id=oid, stage_id=stage.id, **data.model_dump(exclude={'tests'}))
        db.add(task)
        db.flush()
        for case in data.tests:
            db.add(TestCase(task_id=task.id, **case.model_dump()))
    return event, True

def ordered_tasks(rows):
    return sorted(rows, key=lambda task: task.academy_chapter or 99)

def completed_chapters(db, user_id, stage_id):
    return sorted(set(db.scalars(select(Task.academy_chapter).join(Submission, Submission.task_id==Task.id)
        .where(Task.stage_id==stage_id, Task.academy_chapter.is_not(None),
               Submission.stage_id==stage_id, Submission.user_id==user_id,
               Submission.mode=='submit', Submission.status=='Accepted'))))
