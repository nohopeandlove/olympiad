"""Conservative v2 → v3 content update; never rewrite a started stage."""
from sqlalchemy import select, delete
from .academy import academy_id, category_pack, LEGACY_PACK, task_input
from .models import Olympiad, Stage, Task, TestCase, Attempt


LEGACY_RULES = '## Миссия\nОтборочный этап: четыре задачи на Python и четыре контрольных вопроса (600 баллов). Основной этап продолжает сюжет: четыре задачи на Python (400 баллов). Максимум — 1000 баллов. Код оценивается по доле пройденных тестов; вопросы с выбором ответа — автоматически, развёрнутые ответы — преподавателем. На контрольный вопрос можно отправить один окончательный ответ. Задания можно решать в любом порядке внутри этапа. Финал откроется после принятого официального решения «Последнего протокола». Решайте самостоятельно.'

def matches(task, definition, db):
    data = task_input(definition)
    if any(getattr(task, key) != value for key, value in data.model_dump(exclude={'tests'}).items()):
        return False
    actual = sorted((c.input, c.expected, c.public) for c in db.scalars(select(TestCase).where(TestCase.task_id == task.id)))
    expected = sorted((c.input, c.expected, c.public) for c in data.tests)
    return actual == expected


def upgrade_academy_content(db):
    report = []
    for audience in ('SCHOOL', 'SPO'):
        oid = academy_id(audience)
        event = db.get(Olympiad, oid)
        if not event:
            continue
        pack = category_pack(audience)
        for stage in db.scalars(select(Stage).where(Stage.olympiad_id == oid)).all():
            if db.scalar(select(Attempt.id).where(Attempt.stage_id == stage.id).limit(1)):
                report.append((audience, stage.kind, 'started: preserved'))
                continue
            existing = list(db.scalars(select(Task).where(Task.stage_id == stage.id)))
            old_by_key = {t['key']: t for t in LEGACY_PACK['tasks'] if t['stage_kind'] == stage.kind}
            for definition in (t for t in pack['tasks'] if t['stage_kind'] == stage.kind):
                # Original code chapters have stable identities; controls are matched by original position.
                if definition['chapter'] is not None:
                    found = next((t for t in existing if t.academy_chapter == definition['chapter']), None)
                else:
                    legacy = old_by_key[definition['key']]
                    found = next((t for t in existing if t.kind == legacy['kind'] and t.position == legacy['position']), None)
                data = task_input(definition)
                if found:
                    legacy = old_by_key.get(definition['key'])
                    if matches(found, definition, db):
                        continue  # Repeatable: already installed.
                    if not legacy or not matches(found, legacy, db):
                        report.append((audience, found.title, 'edited: preserved'))
                        continue
                    for key, value in data.model_dump(exclude={'tests'}).items():
                        setattr(found, key, value)
                    db.execute(delete(TestCase).where(TestCase.task_id == found.id))
                    task = found
                else:
                    task = Task(olympiad_id=oid, stage_id=stage.id, **data.model_dump(exclude={'tests'}))
                    db.add(task)
                    db.flush()
                    existing.append(task)
                for case in data.tests:
                    db.add(TestCase(task_id=task.id, **case.model_dump()))
                db.flush()
            # Preserve manually changed stage descriptions.
            old_stage = next((s for s in LEGACY_PACK['stages'] if s['kind'] == stage.kind), None)
            new_stage = next((s for s in pack['stages'] if s['kind'] == stage.kind), None)
            if old_stage and new_stage and stage.story_intro == old_stage['story_intro']:
                stage.story_intro = new_stage['story_intro']
        # Rules must not promise new content when a live stage had to remain unchanged.
        if not db.scalar(select(Attempt.id).join(Stage, Stage.id == Attempt.stage_id).where(Stage.olympiad_id == oid).limit(1)):
            if event.rules == LEGACY_RULES:
                event.rules = pack['rules']
        db.flush()
    return report
