"""The public catalogue is one adventure, filtered by authenticated category."""
import uuid
import httpx
import pytest
from app.academy import academy_id

URL='http://localhost:8080'

@pytest.fixture(scope='module')
def readers():
    clients={'guest':httpx.Client(base_url=URL,trust_env=False)}
    for who in ('school','spo1','spo2','admin'):
        c=httpx.Client(base_url=URL,headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex},trust_env=False)
        r=c.post('/api/auth/login',json={'email':who+'@example.org','password':'DevOnly!Python2026'});assert r.status_code==200,r.text
        c.headers['X-CSRF-Token']=r.json()['csrf'];clients[who]=c
    yield clients
    for c in clients.values():c.close()

def test_one_adventure_for_guests(readers):
    rows=readers['guest'].get('/api/olympiads').json()
    assert {o['id'] for o in rows}=={academy_id('SCHOOL'),academy_id('SPO')}
    assert len(rows)==2  # Two category records inside the single public adventure.
    for event in rows:
        assert [s['kind'] for s in event['stages']]==['qualifying','main']
        assert [len(s['chapters']) for s in event['stages']]==[8,4]
        assert 'correct_option' not in str(event) and 'rubric' not in str(event)

@pytest.mark.parametrize('who,category',[('school','SCHOOL'),('spo1','SPO'),('spo2','SPO')])
def test_category_is_enforced_in_catalogue_links_and_ranking(readers,who,category):
    c=readers[who];own=academy_id(category);foreign=academy_id('SPO' if category=='SCHOOL' else 'SCHOOL')
    rows=c.get('/api/olympiads').json();assert len(rows)==1 and rows[0]['id']==own
    assert c.get('/api/olympiads/'+own).status_code==200
    assert c.get('/api/olympiads/'+foreign).status_code in (403,404)
    assert c.get('/api/results/'+foreign).status_code in (403,404)
    assert c.get('/api/admin/olympiads?current=true').status_code==403
    profile=c.get('/api/profile').json()
    assert profile['category']==category
    assert len(profile['registrations'])==1 and profile['registrations'][0]['olympiad_id']==own
    assert all(s['olympiad_id']==own for s in profile['submissions'])
    # The migration carries over existing enrolment without relabelling education.
    registration=profile['registrations'][0]
    if category=='SCHOOL':assert registration['school_class'] in (10,11) and registration['course'] is None
    else:assert registration['course'] in (1,2) and registration['school_class'] is None
    stages=readers['admin'].get('/api/admin/olympiads/'+foreign+'/stages').json()
    for stage in stages:
        assert c.get('/api/stages/'+stage['id']+'/tasks').status_code==403
        assert c.post('/api/stages/'+stage['id']+'/start').status_code==403

def test_legacy_events_stay_in_database_but_not_public_interface(readers):
    admin=readers['admin']
    all_events=admin.get('/api/admin/olympiads').json()
    current=admin.get('/api/admin/olympiads?current=true').json()
    assert {o['id'] for o in current}=={academy_id('SCHOOL'),academy_id('SPO')}
    legacy=next(o for o in all_events if o['id'] not in {o['id'] for o in current})
    assert len(all_events)>len(current)
    for who in ('guest','school','spo1'):
        assert readers[who].get('/api/olympiads/'+legacy['id']).status_code==404
    assert admin.get('/api/olympiads/'+legacy['id']).status_code==200
    assert admin.get('/api/admin/olympiads/'+legacy['id']+'/stages').json()
    assert admin.get('/api/admin/olympiads/'+legacy['id']+'/participants').status_code==200
