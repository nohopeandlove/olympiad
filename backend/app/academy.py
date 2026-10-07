"""The authored task pack. Tests and the ending stay on the backend."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from datetime import timedelta
from sqlalchemy import select
from .models import Olympiad, Stage, Task, TestCase, Submission, now
from .schemas import TaskInput

CONTENT = Path(__file__).parent / 'content'
LEGACY_PACK = json.loads((CONTENT / 'academy.json').read_text())
PACKS = {audience: json.loads((CONTENT / filename).read_text()) for audience, filename in
         [('SCHOOL', 'academy_school_v3.json'), ('SPO', 'academy_spo_v3.json')]}
PACK = PACKS['SPO']

def category_pack(audience):
    return PACKS[audience]

def task_input(chapter):
    fields = {k: v for k, v in chapter.items() if k not in {'chapter', 'stars', 'topic', 'key', 'stage_kind'}}
    return TaskInput(**fields, academy_chapter=chapter['chapter'])

def academy_id(audience):
    return str(uuid5(NAMESPACE_URL, PACK['key'] + ':' + audience))

def create_academy(db, audience):
    """One atomic, repeatable import per audience; do not alter existing events."""
    oid = academy_id(audience)
    existing = db.get(Olympiad, oid)
    if existing:
        return existing, False
    pack = category_pack(audience)
    timestamp = now()
    event = Olympiad(id=oid, type=audience, title=pack['title'], description=pack['intro'],
        rules=pack['rules'],
        status='draft', registration_start=timestamp,
        registration_end=timestamp + timedelta(days=7), ranking_visible=False)
    db.add(event)
    db.flush()
    for index, definition in enumerate(pack['stages']):
        stage = Stage(olympiad_id=oid, **definition,
            starts_at=timestamp + timedelta(days=8 + index * 2),
            ends_at=timestamp + timedelta(days=9 + index * 2))
        db.add(stage)
        db.flush()
        for chapter in pack['tasks']:
            if chapter['stage_kind'] != stage.kind: continue
            data = task_input(chapter)
            task = Task(olympiad_id=oid, stage_id=stage.id, **data.model_dump(exclude={'tests'}))
            db.add(task)
            db.flush()
            for case in data.tests:
                db.add(TestCase(task_id=task.id, **case.model_dump()))
    return event, True

def ordered_tasks(rows):
    return sorted(rows, key=lambda task: (task.position or task.academy_chapter or 999, task.title))

def completed_chapters(db, user_id, stage_id):
    return sorted(set(db.scalars(select(Task.academy_chapter).join(Submission, Submission.task_id==Task.id)
        .where(Task.stage_id==stage_id, Task.academy_chapter.is_not(None),
               Submission.stage_id==stage_id, Submission.user_id==user_id,
               Submission.mode=='submit', Submission.status=='Accepted'))))
