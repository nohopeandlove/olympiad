"""Authored outputs, independent small-input oracles, and safe data upgrades."""
import random
import subprocess
import sys
from datetime import timedelta
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.academy import PACKS, LEGACY_PACK, academy_id, task_input, create_academy
from app.academy_updates import upgrade_academy_content
from app.models import Base, Olympiad, Stage, Task, TestCase as Case, User, Registration, Attempt, now
from academy_reference import CATEGORY_SOLUTIONS


def run(audience, chapter, inp):
    r = subprocess.run([sys.executable, '-c', CATEGORY_SOLUTIONS[audience][chapter]], input=inp+'\n', capture_output=True, text=True, timeout=2)
    assert r.returncode == 0, r.stderr
    return r.stdout.split()


@pytest.mark.parametrize('audience,definition', [(a,t) for a,p in PACKS.items() for t in p['tasks'] if t['kind']=='code'], ids=lambda v: v if isinstance(v,str) else str(v['chapter']))
def test_every_authored_case(audience, definition):
    data=task_input(definition)
    assert len(data.tests)>=6 and any(c.public for c in data.tests) and any(not c.public for c in data.tests)
    for case in data.tests:
        assert run(audience,definition['chapter'],case.input)==case.expected.split()


def test_pack_structure_and_real_difficulty_difference():
    for pack in PACKS.values():
        qualifying=[t for t in pack['tasks'] if t['stage_kind']=='qualifying']
        main=[t for t in pack['tasks'] if t['stage_kind']=='main']
        assert len(qualifying)==8 and len(main)==10
        assert [t['position'] for t in main]==list(range(1,11)) and main[-1]['chapter']==8
        assert len({t['key'] for t in pack['tasks']})==18
        assert sum(t['points'] for t in qualifying)==600 and sum(t['points'] for t in main)==1000
        assert sum(t['kind']=='choice' for t in qualifying)==2 and sum(t['kind']=='text' for t in qualifying)==2
        for t in pack['tasks']:task_input(t)
    school={t['key']:t for t in PACKS['SCHOOL']['tasks']}
    for t in PACKS['SPO']['tasks']:
        assert t['statement']!=school[t['key']]['statement']
        if t['kind']=='code': assert t['tests']!=school[t['key']]['tests']


def test_random_small_cases_against_brute_force():
    rng=random.Random(711)
    for _ in range(12):
        n=rng.randint(1,15);a=[rng.randint(1,8) for _ in range(n)];k=rng.randint(1,70)
        spans=[j-i for i in range(n) for j in range(i+1,n+1) if sum(a[i:j])>=k]
        assert run('SPO',10,f'{n} {k}\n'+ ' '.join(map(str,a)))==[str(min(spans,default=0))]
        s=''.join(rng.choice('abcd') for _ in range(n))
        lengths=[j-i for i in range(n) for j in range(i+1,n+1) if len(set(s[i:j]))==j-i]
        assert run('SPO',14,s)==[str(max(lengths))]
        assert run('SCHOOL',14,s)==[str(len(set(s)))]
        queries=[(rng.randint(1,n),rng.randint(1,n)) for _ in range(10)];queries=[(min(l,r),max(l,r)) for l,r in queries]
        data=f'{n} 10\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{l} {r}' for l,r in queries)
        assert run('SPO',9,data)==[str(sum(a[l-1:r])) for l,r in queries]
        p=rng.randint(1,5);free=[0]*p;expected=[]
        for duration in a:
            i=min(range(p),key=lambda j:(free[j],j));expected += [str(i+1),str(free[i])];free[i]+=duration
        assert run('SPO',11,f'{p} {n}\n'+' '.join(map(str,a)))==expected
        h,w=rng.randint(1,4),rng.randint(1,4);grid=[[rng.randint(0,9) for _ in range(w)] for _ in range(h)]
        def paths(r,c,total):
            if grid[r][c]<0:return []
            total+=grid[r][c]
            if (r,c)==(h-1,w-1):return [total]
            return (paths(r+1,c,total) if r+1<h else [])+(paths(r,c+1,total) if c+1<w else [])
        inp=f'{h} {w}\n'+'\n'.join(' '.join(map(str,row)) for row in grid)
        assert run('SCHOOL',13,inp)==[str(min(paths(0,0,0)))]
        grid[rng.randrange(h)][rng.randrange(w)]=-1
        inp=f'{h} {w}\n'+'\n'.join(' '.join(map(str,row)) for row in grid)
        assert run('SPO',13,inp)==[str(min(paths(0,0,0),default=-1))]


@pytest.fixture
def db():
    engine=create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as session:yield session
    engine.dispose()


def legacy_event(db,audience):
    event,_=create_academy(db,audience)
    stages=list(db.scalars(select(Stage).where(Stage.olympiad_id==event.id)))
    # Recreate the unchanged v2 content in an otherwise fresh fixture.
    for stage in stages:
        for task in list(db.scalars(select(Task).where(Task.stage_id==stage.id))):
            db.query(Case).filter_by(task_id=task.id).delete();db.delete(task)
        db.flush()
        stage.story_intro=next(s['story_intro'] for s in LEGACY_PACK['stages'] if s['kind']==stage.kind)
        for definition in LEGACY_PACK['tasks']:
            if definition['stage_kind']!=stage.kind:continue
            data=task_input(definition);task=Task(olympiad_id=event.id,stage_id=stage.id,**data.model_dump(exclude={'tests'}));db.add(task);db.flush()
            for case in data.tests:db.add(Case(task_id=task.id,**case.model_dump()))
    db.flush()
    return event,stages


def test_existing_tasks_keep_ids_and_update_is_repeatable(db):
    for audience in ('SCHOOL','SPO'):legacy_event(db,audience)
    ids=set(db.scalars(select(Task.id)))
    deadlines=[(s.id,s.starts_at,s.ends_at,s.duration_minutes) for s in db.scalars(select(Stage))]
    assert not upgrade_academy_content(db)
    first=[(t.id,t.statement,t.position) for t in db.scalars(select(Task).order_by(Task.id))]
    assert len(first)==36 and ids<=set(t[0] for t in first)
    assert not upgrade_academy_content(db)
    assert first==[(t.id,t.statement,t.position) for t in db.scalars(select(Task).order_by(Task.id))]
    assert deadlines==[(s.id,s.starts_at,s.ends_at,s.duration_minutes) for s in db.scalars(select(Stage))]


def test_started_stage_and_manually_edited_task_are_preserved(db):
    event,stages=legacy_event(db,'SCHOOL')
    main=next(s for s in stages if s.kind=='main');qual=next(s for s in stages if s.kind=='qualifying')
    custom=db.scalar(select(Task).where(Task.stage_id==qual.id,Task.academy_chapter==2));custom.statement='Авторское условие учителя'
    user=User(email='fixture@example.org',password_hash='fixture',role='participant',first_name='A',last_name='B',verified=True,birth_date=now().date(),phone='fixture',region='fixture',city='fixture',organization='fixture');db.add(user);db.flush()
    reg=Registration(user_id=user.id,olympiad_id=event.id,school_class=10);db.add(reg);db.flush()
    attempt=Attempt(registration_id=reg.id,stage_id=main.id,session_hash='fixture',deadline=now()+timedelta(hours=1));db.add(attempt);db.flush()
    before=[(t.id,t.statement) for t in db.scalars(select(Task).where(Task.stage_id==main.id).order_by(Task.id))]
    report=upgrade_academy_content(db)
    assert any(r[2]=='started: preserved' for r in report) and any(r[2]=='edited: preserved' for r in report)
    assert before==[(t.id,t.statement) for t in db.scalars(select(Task).where(Task.stage_id==main.id).order_by(Task.id))]
    assert custom.statement=='Авторское условие учителя'
