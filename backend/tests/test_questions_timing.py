"""Mixed-stage workflow against real services; server-only grading and timing."""
import time
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import httpx
import pytest
from pydantic import ValidationError
from app.task_timing import pending_ms
from app.schemas import TaskInput, TaskFocusInput

URL='http://localhost:8080'
PASSWORD='DevOnly!Python2026'

def test_timing_lease_and_deadline():
    now=datetime.now(timezone.utc)
    a=SimpleNamespace(active_task_id='task',task_last_seen_at=now,deadline=now+timedelta(seconds=60))
    stage=SimpleNamespace(ends_at=now+timedelta(seconds=120))
    assert pending_ms(a,stage,now+timedelta(seconds=10))==10000
    assert pending_ms(a,stage,now+timedelta(seconds=300))==30000
    a.deadline=now+timedelta(seconds=5)
    assert pending_ms(a,stage,now+timedelta(seconds=10))==5000
    stage.ends_at=now+timedelta(seconds=2)
    assert pending_ms(a,stage,now+timedelta(seconds=10))==2000
    a.active_task_id=None
    assert pending_ms(a,stage,now+timedelta(seconds=10))==0
    with pytest.raises(ValidationError):TaskFocusInput(task_id='task',elapsed_ms=900000)

@pytest.mark.parametrize('fields',[{'kind':'code','tests':[]},{'kind':'choice','answer_options':['A','B'],'correct_option':2},{'kind':'choice','answer_options':['A','A'],'correct_option':0},{'kind':'text','tests':[{'input':'','expected':''}]},{'kind':'choice','answer_options':['A','B'],'correct_option':0,'academy_chapter':8}])
def test_invalid_question_configuration(fields):
    with pytest.raises(ValidationError):TaskInput(title='Q',statement='Q',**fields)

def test_mixed_stage_answers_review_and_timing():
    clients={}
    for who in ('admin','school','spo1'):
        c=httpx.Client(base_url=URL,headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex},trust_env=False,timeout=30)
        r=c.post('/api/auth/login',json={'email':who+'@example.org','password':PASSWORD});assert r.status_code==200,r.text
        c.headers['X-CSRF-Token']=r.json()['csrf'];clients[who]=c
    admin,student,other=clients.values()
    now=datetime.now(timezone.utc)
    event={'type':'SCHOOL','title':'Mixed stages '+uuid.uuid4().hex[:8],'status':'active','registration_start':(now-timedelta(days=1)).isoformat(),'registration_end':(now+timedelta(days=1)).isoformat(),'ranking_visible':True}
    r=admin.post('/api/admin/olympiads',json=event);assert r.status_code==201,r.text;oid=r.json()['id']
    try:
        def create_stage(kind,starts):
            r=admin.post('/api/admin/olympiads/'+oid+'/stages',json={'kind':kind,'title':kind,'story_intro':'История '+kind,'starts_at':starts.isoformat(),'ends_at':(now+timedelta(hours=3)).isoformat(),'duration_minutes':60});assert r.status_code==201,r.text;return r.json()['id']
        sid=create_stage('qualifying',now-timedelta(minutes=1));main=create_stage('main',now+timedelta(hours=1))
        fields=[{'kind':'code','title':'Python','statement':'Print 1','position':1,'tests':[{'input':'','expected':'1','public':True},{'input':'','expected':'1','public':False}]},{'kind':'choice','title':'Choice','statement':'Select B','points':30,'position':2,'answer_options':['A','B'],'correct_option':1},{'kind':'text','title':'Text','statement':'Explain','points':50,'position':3,'rubric':'PRIVATE_RUBRIC'}]
        fields.append({**fields[1],'title':'Second choice','position':4})
        tids=[]
        for t in fields:
            r=admin.post('/api/admin/stages/'+sid+'/tasks',json=t);assert r.status_code==201,r.text;tids.append(r.json()['id'])
        r=admin.post('/api/admin/stages/'+main+'/tasks',json=fields[1]);assert r.status_code==201;foreign=r.json()['id']
        assert student.post('/api/registrations/'+oid,json={'school_class':9,'consent_data':True,'consent_rules':True}).status_code==422
        r=student.post('/api/registrations/'+oid,json={'school_class':10,'consent_data':True,'consent_rules':True});assert r.status_code==201,r.text
        assert student.post('/api/stages/'+main+'/start').status_code==403
        assert student.post('/api/stages/'+sid+'/start').status_code==200
        visible=student.get('/api/stages/'+sid+'/tasks');assert visible.status_code==200
        assert [t['kind'] for t in visible.json()]==['code','choice','text','choice']
        assert 'correct_option' not in visible.text and 'PRIVATE_RUBRIC' not in visible.text and 'rubric' not in visible.text
        public=other.get('/api/olympiads').text;assert 'PRIVATE_RUBRIC' not in public and 'Select B' not in public
        assert other.get('/api/stages/'+sid+'/task-times').status_code==403
        assert student.get('/api/admin/olympiads/'+oid+'/task-times').status_code==403
        assert student.post('/api/stages/'+sid+'/task-focus',json={'task_id':foreign}).status_code==403
        assert student.post('/api/stages/'+sid+'/task-focus',json={'task_id':tids[1],'elapsed_ms':999999}).status_code==422
        assert student.post('/api/stages/'+sid+'/task-focus',json={'task_id':tids[1]}).status_code==200
        time.sleep(.15)
        paused=student.post('/api/stages/'+sid+'/task-focus',json={'task_id':None}).json()
        one=next(r for r in paused['timings'] if r['task_id']==tids[1]);assert 100<=one['elapsed_ms']<3000 and one['active_until'] is None
        time.sleep(.1)
        assert student.get('/api/stages/'+sid+'/task-times').json()['timings'][0]['elapsed_ms']==one['elapsed_ms']
        assert student.post('/api/stages/'+sid+'/task-focus',json={'task_id':tids[2]}).status_code==200
        time.sleep(.15)
        timing=admin.get('/api/admin/olympiads/'+oid+'/task-times');assert timing.status_code==200
        rows=timing.json()['timings'];assert len(rows)==4
        assert sum(bool(t['active_until']) for t in rows)==1
        assert next(t for t in rows if t['task_id']==tids[2])['elapsed_ms']>=100
        invalid=student.post('/api/tasks/'+tids[1]+'/answers',json={'option_index':8});assert invalid.status_code==422
        sent=student.post('/api/tasks/'+tids[1]+'/answers',json={'option_index':1});assert sent.status_code==201,sent.text
        assert sent.json()['status']=='Accepted' and sent.json()['score']==30
        assert student.post('/api/tasks/'+tids[1]+'/answers',json={'option_index':0}).status_code==409
        wrong=student.post('/api/tasks/'+tids[3]+'/answers',json={'option_index':0});assert wrong.status_code==201 and wrong.json()['status']=='Wrong Answer' and wrong.json()['score']==0
        assert student.post('/api/tasks/'+tids[2]+'/submissions',json={'code':'text'}).status_code==422
        assert student.post('/api/tasks/'+tids[2]+'/answers',json={'answer':'   '}).status_code==422
        sent=student.post('/api/tasks/'+tids[2]+'/answers',json={'answer':'My explanation'});assert sent.status_code==201,sent.text
        subid=sent.json()['id'];assert sent.json()['status']=='Pending Review' and sent.json()['score']==0
        assert other.get('/api/submissions/'+subid).status_code==403
        assert student.post('/api/admin/submissions/'+subid+'/review',json={'score':50}).status_code==403
        assert admin.post('/api/admin/submissions/'+subid+'/review',json={'score':51}).status_code==422
        assert admin.get('/api/submissions/'+subid).json()['task']['rubric']=='PRIVATE_RUBRIC'
        result=admin.post('/api/admin/submissions/'+subid+'/review',json={'score':40,'feedback':'Good reasoning'});assert result.status_code==200,result.text
        own=student.get('/api/submissions/'+subid).json();assert own['status']=='Reviewed' and own['score']==40 and own['review_feedback']=='Good reasoning'
        assert 'rubric' not in own['task']
        ranking=admin.get('/api/admin/olympiads/'+oid+'/ranking').json();assert next(r for r in ranking if r['name'].startswith('Иванов'))['score']==70
        profile=student.get('/api/profile').json();assert any('40 / 50' in n['message'] for n in profile['notifications'])
        assert admin.post('/api/admin/stages/'+sid+'/tasks',json=fields[0]).status_code==409
        assert student.post('/api/stages/'+sid+'/finish').status_code==200
        assert all(t['active_until'] is None for t in student.get('/api/stages/'+sid+'/task-times').json()['timings'])
        assert student.post('/api/stages/'+sid+'/task-focus',json={'task_id':tids[0]}).status_code==403
        assert student.post('/api/tasks/'+tids[0]+'/answers',json={'answer':'x'}).status_code==403
    finally:
        admin.put('/api/admin/olympiads/'+oid,json={**event,'status':'draft'})
        for client in clients.values():client.close()
