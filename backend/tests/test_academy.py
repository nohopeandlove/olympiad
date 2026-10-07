import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
import httpx
import pytest
from app.academy import PACK, task_input
from academy_reference import SOLUTIONS

URL = 'http://localhost:8080'
PASSWORD = 'DevOnly!Python2026'

@pytest.mark.parametrize('chapter', [t for t in PACK['tasks'] if t['kind']=='code'], ids=lambda t: 'chapter-'+str(t['chapter']))
def test_authored_cases(chapter):
    data = task_input(chapter)
    assert len(data.tests) >= 6 and any(c.public for c in data.tests)
    assert any(not c.public for c in data.tests)
    for case in data.tests:
        result = subprocess.run([sys.executable, '-c', SOLUTIONS[chapter['chapter']]], input=case.input+'\n', text=True, capture_output=True, timeout=2)
        assert result.returncode == 0, result.stderr
        assert result.stdout.split() == case.expected.split()

@pytest.fixture(scope='module')
def academy_clients():
    result = {}
    for key in ('admin','school','spo1'):
        client = httpx.Client(base_url=URL, headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex}, timeout=30, trust_env=False)
        response = client.post('/api/auth/login', json={'email':key+'@example.org','password':PASSWORD})
        assert response.status_code == 200, response.text
        client.headers['X-CSRF-Token'] = response.json()['csrf']
        result[key] = client
    yield result
    for client in result.values(): client.close()


def test_atomic_repeatable_import(academy_clients):
    admin = academy_clients['admin']
    assert academy_clients['school'].get('/api/admin/task-packs/academy').status_code == 403
    assert academy_clients['school'].post('/api/admin/adventures/academy',json={'type':'SCHOOL'}).status_code == 403
    before = admin.get('/api/admin/olympiads').json()
    old_counts = {o['id']: [(s['id'], len(admin.get('/api/admin/stages/'+s['id']+'/tasks').json())) for s in admin.get('/api/admin/olympiads/'+o['id']+'/stages').json()] for o in before}
    for audience in ('SCHOOL','SPO'):
        response = admin.post('/api/admin/adventures/academy',json={'type':audience})
        assert response.status_code == 201, response.text
        event = response.json()['olympiad']
        assert event['status'] == next(o['status'] for o in before if o['id']==event['id'])
        repeated = admin.post('/api/admin/adventures/academy',json={'type':audience}).json()
        assert not repeated['created'] and repeated['olympiad']['id'] == event['id']
        stage = admin.get('/api/admin/olympiads/'+event['id']+'/stages').json()
        assert len(stage) == 2 and [s['kind'] for s in stage]==['qualifying','main']
        assert [s['duration_minutes'] for s in stage]==[120,180]
        tasks = [t for s in stage for t in admin.get('/api/admin/stages/'+s['id']+'/tasks').json()]
        assert [t['academy_chapter'] for t in tasks if t['kind']=='code'] == list(range(1,9))
        assert len(tasks)==12 and sum(t['kind']=='choice' for t in tasks)==2 and sum(t['kind']=='text' for t in tasks)==2
        assert sum(t['points'] for t in tasks) == 1000
        public = admin.get('/api/olympiads').json()
        assert (event['id'] in {o['id'] for o in public}) == (event['status']!='draft')
    for oid, stages in old_counts.items():
        for sid, count in stages:
            assert len(admin.get('/api/admin/stages/'+sid+'/tasks').json()) == count
    pack = admin.get('/api/admin/task-packs/academy').json()
    assert 'finale' not in pack and len(pack['tasks']) == 12


def checked(client, submission_id):
    for _ in range(240):
        response=client.get('/api/submissions/'+submission_id)
        assert response.status_code==200,response.text
        row=response.json()
        if row['status'] not in ('Queued','Running'):return row
        time.sleep(.25)
    pytest.fail('Judge did not finish')


def test_eight_chapters_real_judge_and_protected_ending(academy_clients):
    admin, student = academy_clients['admin'], academy_clients['school']
    timestamp = datetime.now(timezone.utc)
    event = {'type':'SCHOOL','title':'Academy E2E '+uuid.uuid4().hex[:8],'description':PACK['intro'],'status':'active','registration_start':(timestamp-timedelta(days=1)).isoformat(),'registration_end':(timestamp+timedelta(days=1)).isoformat()}
    response=admin.post('/api/admin/olympiads',json=event);assert response.status_code==201,response.text
    oid=response.json()['id']
    try:
        stage = {'title':'Восемь глав','kind':'main','starts_at':(timestamp-timedelta(minutes=1)).isoformat(),'ends_at':(timestamp+timedelta(days=1)).isoformat(),'duration_minutes':180}
        response=admin.post('/api/admin/olympiads/'+oid+'/stages',json=stage);assert response.status_code==201,response.text
        sid=response.json()['id']
        # Deliberately import out of order: the participant must still see chapter order.
        tasks = {}
        for chapter in reversed([t for t in PACK['tasks'] if t['kind']=='code']):
            response=admin.post('/api/admin/stages/'+sid+'/tasks',json=task_input(chapter).model_dump()|{'position':chapter['chapter']})
            assert response.status_code==201,response.text
            tasks[chapter['chapter']]=response.json()['id']
        response=student.post('/api/registrations/'+oid,json={'school_class':10,'consent_data':True,'consent_rules':True});assert response.status_code==201,response.text
        assert student.post('/api/stages/'+sid+'/start').status_code==200
        assert student.get('/api/stages/'+sid+'/academy-ending').status_code==403
        assert academy_clients['spo1'].get('/api/stages/'+sid+'/academy-progress').status_code==403
        visible=student.get('/api/stages/'+sid+'/tasks').json()
        assert [t['academy_chapter'] for t in visible]==list(range(1,9))
        assert all('tests' not in t and all(c['public'] for c in t['examples']) for t in visible)
        run=student.post('/api/tasks/'+tasks[8]+'/submissions',json={'mode':'run','code':SOLUTIONS[8]})
        assert run.status_code==202,run.text
        assert checked(student,run.json()['id'])['status']=='Accepted'
        assert student.get('/api/stages/'+sid+'/academy-ending').status_code==403
        for number in range(1,9):
            sent=student.post('/api/tasks/'+tasks[number]+'/submissions',json={'mode':'submit','code':SOLUTIONS[number]})
            assert sent.status_code==202,sent.text
            result=checked(student,sent.json()['id'])
            assert result['status']=='Accepted' and result['score']==100,result
            assert all(set(t)=={'status'} for t in result['result']['tests'])
        progress=student.get('/api/stages/'+sid+'/academy-progress').json()
        assert progress=={'completed_chapters':list(range(1,9)),'ending_unlocked':True}
        ending=student.get('/api/stages/'+sid+'/academy-ending')
        assert ending.status_code==200 and 'забытый ИИ' in ending.json()['text']
        profile=student.get('/api/profile').json()
        assert all(r['olympiad_id']!=oid for r in profile['registrations'])  # Isolated archive events are hidden from the single-adventure cabinet.
        assert student.post('/api/stages/'+sid+'/finish').status_code==200
        assert student.get('/api/stages/'+sid+'/academy-ending').status_code==200
    finally:
        admin.put('/api/admin/olympiads/'+oid,json={**event,'status':'draft'})
