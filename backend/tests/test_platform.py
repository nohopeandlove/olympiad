"""Integration tests against the real Compose services (not a mocked judge)."""
import os, time, uuid, re
from datetime import datetime, timezone, timedelta
import httpx
import pytest

URL=os.getenv('TEST_BASE_URL','http://localhost:8080')
PASSWORD='DevOnly!Python2026'

@pytest.fixture(scope='module')
def clients():
    result={}
    for key in ['admin','school','spo1','spo2']:
        c=httpx.Client(base_url=URL,headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex},timeout=30,trust_env=False)
        r=c.post('/api/auth/login',json={'email':key+'@example.org','password':PASSWORD}); assert r.status_code==200,r.text
        c.headers['X-CSRF-Token']=r.json()['csrf'];result[key]=c
    for o in result['admin'].get('/api/admin/olympiads').json():
        if o['title']=='Deadline test':
            data={k:v for k,v in o.items() if k!='id'};data['status']='draft'
            result['admin'].put('/api/admin/olympiads/'+o['id'],json=data)
    # Repeated runs preserve deadlines, but bind attempts to these test sessions.
    for who in ['school','spo1','spo2']:
        p=result[who].get('/api/profile').json()
        for reg in p['registrations']:
            for attempt in reg['attempts']:
                r=result['admin'].post(f"/api/admin/participants/{reg['id']}/reset-session/{attempt['stage_id']}")
                assert r.status_code==200,r.text
    yield result
    for c in result.values():c.close()

@pytest.fixture(scope='module')
def events(clients):
    rows=clients['admin'].get('/api/admin/olympiads').json()
    result={}
    for typ in ['SCHOOL','SPO']:
        o=next(o for o in rows if o['type']==typ and o['title']==('Олимпиада для школьников' if typ=='SCHOOL' else 'Олимпиада для студентов СПО'))
        stages=clients['admin'].get(f"/api/admin/olympiads/{o['id']}/stages").json()
        s=next(s for s in stages if s['kind']=='qualifying')
        ts=clients['admin'].get(f"/api/admin/stages/{s['id']}/tasks").json()
        result[typ]={'o':o,'s':s,'tasks':ts}
    return result

def wait(c,sid):
    for _ in range(100):
        r=c.get('/api/submissions/'+sid);assert r.status_code==200,r.text
        if r.json()['status'] not in ['Queued','Running']:return r.json()
        time.sleep(.2)
    pytest.fail('Judge timeout')

def test_rbac(clients):
    for c in [clients['school'],clients['spo1']]: assert c.get('/api/admin/olympiads').status_code==403

def test_csrf(clients):
    c=clients['school'];token=c.headers.pop('X-CSRF-Token')
    assert c.post('/api/auth/logout').status_code==403
    c.headers['X-CSRF-Token']=token

def test_cross_olympiad(clients,events):
    for who,other in [('school','SPO'),('spo1','SCHOOL'),('spo2','SCHOOL')]:
        sid=events[other]['s']['id'];tid=events[other]['tasks'][0]['id'];c=clients[who]
        assert c.post(f'/api/stages/{sid}/start').status_code==403
        assert c.get(f'/api/stages/{sid}/tasks').status_code==403
        assert c.post(f'/api/tasks/{tid}/submissions',json={'code':'print(1)','mode':'submit'}).status_code==403
        assert c.get(f'/api/tasks/{tid}/draft').status_code==403

def test_before_stage_start(clients,events):
    oid=events['SCHOOL']['o']['id']
    stages=clients['admin'].get(f'/api/admin/olympiads/{oid}/stages').json()
    main=next(s for s in stages if s['kind']=='main')
    assert clients['school'].post(f"/api/stages/{main['id']}/start").status_code==403
    tasks=clients['admin'].get(f"/api/admin/stages/{main['id']}/tasks").json()
    assert clients['school'].post(f"/api/tasks/{tasks[0]['id']}/submissions",json={'code':'print(1)'}).status_code==403

@pytest.mark.parametrize('who,typ,code',[('school','SCHOOL','print(sum(map(int,input().split())))'),('spo1','SPO','print(sum(x*x for x in map(int,input().split())))'),('spo2','SPO','print(sum(x*x for x in map(int,input().split())))')])
def test_full_judge_workflow(clients,events,who,typ,code):
    c=clients[who];e=events[typ];sid=e['s']['id'];tid=e['tasks'][0]['id']
    a=c.post(f'/api/stages/{sid}/start');assert a.status_code==200,a.text
    a2=c.post(f'/api/stages/{sid}/start');assert a.json()['deadline']==a2.json()['deadline']
    ts=c.get(f'/api/stages/{sid}/tasks');assert ts.status_code==200
    assert all('tests' not in t for t in ts.json())
    assert len(ts.json()[0]['examples'])==1
    hidden=e['tasks'][0]['tests'][1];assert hidden['id'] not in ts.text
    r=c.put(f'/api/tasks/{tid}/draft',json={'code':code});assert r.status_code==200
    assert c.get(f'/api/tasks/{tid}/draft').json()['code']==code
    s=c.post(f'/api/tasks/{tid}/submissions',json={'code':code,'mode':'submit'});assert s.status_code==202,s.text
    checked=wait(c,s.json()['id']);assert checked['status']=='Accepted',checked
    assert checked['score']==100
    assert all(set(t)=={'status'} for t in checked['result']['tests'])
    assert clients['spo1' if who=='school' else 'school'].get('/api/submissions/'+s.json()['id']).status_code==403
    ev=c.post(f'/api/anti-cheat/{sid}',json={'event_type':'TAB_HIDDEN','metadata':{}});assert ev.status_code==200
    rows=clients['admin'].get(f"/api/admin/olympiads/{e['o']['id']}/events").json()
    assert any(x['event_type']=='TAB_HIDDEN' for x in rows)
    ranking=c.get(f"/api/results/{e['o']['id']}").json()
    assert all(r['school_class'] is not None for r in ranking) if typ=='SCHOOL' else all(r['course'] in (1,2) for r in ranking)

def test_second_session(clients,events):
    c=httpx.Client(base_url=URL,headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex},trust_env=False)
    r=c.post('/api/auth/login',json={'email':'school@example.org','password':PASSWORD});c.headers['X-CSRF-Token']=r.json()['csrf']
    sid=events['SCHOOL']['s']['id']
    assert c.post(f'/api/stages/{sid}/start').status_code==409
    c.close()

def test_judge_errors(clients,events):
    c=clients['school'];tid=events['SCHOOL']['tasks'][0]['id']
    for code,expected in [('print(0)','Wrong Answer'),('while True: pass','Time Limit Exceeded'),('def broken(','Interpreter Error'),('raise ValueError("boom")','Runtime Error')]:
        s=c.post(f'/api/tasks/{tid}/submissions',json={'code':code,'mode':'run'});assert s.status_code==202,s.text
        assert wait(c,s.json()['id'])['status']==expected

def test_sandbox_isolation(clients,events):
    c=clients['school'];tid=events['SCHOOL']['tasks'][0]['id']
    code='''import os,socket
assert os.getuid()==65534
assert not os.path.exists('/var/run/docker.sock')
assert not os.path.exists('/app')
assert not os.access('/judge-result',os.W_OK)
assert 'DATABASE_URL' not in os.environ
for host in ['postgres','redis','backend','example.com']:
    try:
        socket.create_connection((host,5432),timeout=.1)
        print('NETWORK_LEAK')
    except OSError: pass
print('ISOLATED')
'''
    s=c.post(f'/api/tasks/{tid}/submissions',json={'code':code,'mode':'run'});assert s.status_code==202
    result=wait(c,s.json()['id']);assert result['status']=='Wrong Answer',result
    assert result['result']['tests'][0]['stdout'].strip()=='ISOLATED'

def test_registration_and_email(clients,events):
    unique=uuid.uuid4().hex[:10]
    for typ,level in [('SCHOOL',10),('SPO',1),('SPO',2)]:
        body={'olympiad_id':events[typ]['o']['id'],'email':f'{unique}-{typ}-{level}@example.org','password':PASSWORD,'confirm_password':PASSWORD,'last_name':'Тестов','first_name':'Участник','birth_date':'2008-01-01','phone':'+79001234567','region':'Регион','city':'Город','organization':'Учебная организация','consent_data':True,'consent_rules':True}
        body['school_class' if typ=='SCHOOL' else 'course']=level
        c=httpx.Client(base_url=URL,headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex},trust_env=False)
        r=c.post('/api/auth/register',json=body);assert r.status_code==201,r.text
        assert c.post('/api/auth/login',json={'email':body['email'],'password':PASSWORD}).status_code==403
        with httpx.Client(base_url='http://localhost:8025',trust_env=False) as mail:
            messages=mail.get('/api/v1/messages').json()['messages']
            msg=next(m for m in messages if any(to['Address']==body['email'].lower() for to in m['To']))
            full=mail.get('/api/v1/message/'+msg['ID']).json()
            token=re.search(r'token=([\w-]+)',full['Text']).group(1)
        assert c.post('/api/auth/verify',params={'token':token}).status_code==200
        assert c.post('/api/auth/login',json={'email':body['email'],'password':PASSWORD}).status_code==200
        c.close()

def test_invalid_registration(clients,events):
    body={'school_class':10,'course':1,'consent_data':True,'consent_rules':True}
    assert clients['admin'].post('/api/registrations/'+events['SCHOOL']['o']['id'],json=body).status_code==422
    assert clients['admin'].post('/api/registrations/'+events['SPO']['o']['id'],json={**body,'course':3,'school_class':None}).status_code==422

def test_ranking_hidden_and_export(clients,events):
    c=clients['admin'];o=events['SCHOOL']['o'];body={k:v for k,v in o.items() if k!='id'}
    body['ranking_visible']=False
    assert c.put('/api/admin/olympiads/'+o['id'],json=body).status_code==200
    assert clients['school'].get('/api/results/'+o['id']).status_code==403
    body['ranking_visible']=True;c.put('/api/admin/olympiads/'+o['id'],json=body)
    r=c.get('/api/admin/olympiads/'+o['id']+'/export');assert r.status_code==200 and 'ФИО' in r.text

def test_expired_deadline_and_finish(clients):
    c=clients['admin'];now=datetime.now(timezone.utc)
    o={'type':'SCHOOL','title':'Deadline test','status':'active','registration_start':(now-timedelta(days=1)).isoformat(),'registration_end':(now+timedelta(days=1)).isoformat()}
    r=c.post('/api/admin/olympiads',json=o);assert r.status_code==201,r.text;oid=r.json()['id']
    assert c.post('/api/registrations/'+oid,json={'school_class':10,'consent_data':True,'consent_rules':True}).status_code==201
    stage={'title':'Короткий этап','kind':'qualifying','starts_at':(now-timedelta(minutes=1)).isoformat(),'ends_at':(datetime.now(timezone.utc)+timedelta(seconds=2)).isoformat(),'duration_minutes':1}
    sid=c.post(f'/api/admin/olympiads/{oid}/stages',json=stage).json()['id']
    tid=c.post(f'/api/admin/stages/{sid}/tasks',json={'title':'Test','statement':'Test','tests':[{'input':'','expected':'1','public':False}]}).json()['id']
    a=c.post(f'/api/stages/{sid}/start');assert a.status_code==200,a.text
    time.sleep(2.2)
    assert c.post(f'/api/tasks/{tid}/submissions',json={'code':'print(1)'}).status_code==403
    assert c.post(f'/api/stages/{sid}/start').status_code==403
    o['status']='draft'
    assert c.put(f'/api/admin/olympiads/{oid}',json=o).status_code==200


def test_same_login_second_tab(clients,events):
    c=clients['school'];previous=c.headers['X-Exam-Session']
    c.headers['X-Exam-Session']=uuid.uuid4().hex
    assert c.post('/api/stages/'+events['SCHOOL']['s']['id']+'/start').status_code==409
    assert c.get('/api/stages/'+events['SCHOOL']['s']['id']+'/tasks').status_code==409
    c.headers['X-Exam-Session']=previous

def test_output_memory_and_process_limits(clients,events):
    c=clients['school'];tid=events['SCHOOL']['tasks'][0]['id']
    for code,status in [('while True: print("x"*10000)','Runtime Error'),('a=bytearray(400*1024*1024)','Memory Limit Exceeded')]:
        s=c.post(f'/api/tasks/{tid}/submissions',json={'code':code,'mode':'run'});assert s.status_code==202,s.text
        result=wait(c,s.json()['id']);assert result['status']==status,result
    code="""import subprocess
children=[]
try:
    for _ in range(100): children.append(subprocess.Popen(['python3','-c','import time; time.sleep(5)']))
except BlockingIOError: print('PIDS_LIMITED')
"""
    s=c.post(f'/api/tasks/{tid}/submissions',json={'code':code,'mode':'run'});assert s.status_code==202
    result=wait(c,s.json()['id']);assert 'PIDS_LIMITED' in result['result']['tests'][0]['stdout'],result

def test_brute_force_protection():
    email=uuid.uuid4().hex+'@example.org'
    with httpx.Client(base_url=URL,headers={'Origin':URL},trust_env=False) as c:
        for _ in range(10):
            assert c.post('/api/auth/login',json={'email':email,'password':'incorrect-password'}).status_code==401
        assert c.post('/api/auth/login',json={'email':email,'password':'incorrect-password'}).status_code==429

@pytest.mark.parametrize('typ,code',[('SCHOOL','a,b=map(int,input().split()); print(a+b)'),('SPO','a,b=map(int,input().split()); print(a*b)')])
def test_admin_to_new_participant_complete_flow(clients,typ,code):
    admin=clients['admin'];timestamp=datetime.now(timezone.utc);suffix=uuid.uuid4().hex[:10]
    event={'type':typ,'title':'E2E '+suffix,'status':'active','registration_start':(timestamp-timedelta(days=1)).isoformat(),'registration_end':(timestamp+timedelta(days=1)).isoformat(),'ranking_visible':True}
    created=admin.post('/api/admin/olympiads',json=event);assert created.status_code==201,created.text;oid=created.json()['id']
    try:
        stage={'title':'Отборочный этап','kind':'qualifying','starts_at':(timestamp-timedelta(minutes=1)).isoformat(),'ends_at':(timestamp+timedelta(hours=2)).isoformat(),'duration_minutes':60}
        r=admin.post(f'/api/admin/olympiads/{oid}/stages',json=stage);assert r.status_code==201,r.text;sid=r.json()['id']
        task={'title':'Арифметика','statement':'Вычислите результат','points':80,'tests':[{'input':'2 3\n','expected':'5\n' if typ=='SCHOOL' else '6\n','public':True},{'input':'-2 4\n','expected':'2\n' if typ=='SCHOOL' else '-8\n','public':False}]}
        r=admin.post(f'/api/admin/stages/{sid}/tasks',json=task);assert r.status_code==201,r.text;tid=r.json()['id']
        profile={'olympiad_id':oid,'email':suffix+'@example.org','password':PASSWORD,'confirm_password':PASSWORD,'last_name':'Новый','first_name':'Участник','birth_date':'2008-01-01','phone':'+79001234567','region':'Р','city':'Г','organization':'О','consent_data':True,'consent_rules':True}
        profile['school_class' if typ=='SCHOOL' else 'course']=10 if typ=='SCHOOL' else 2
        with httpx.Client(base_url=URL,headers={'Origin':URL,'X-Exam-Session':uuid.uuid4().hex},trust_env=False) as c:
            r=c.post('/api/auth/register',json=profile);assert r.status_code==201,r.text
            with httpx.Client(base_url='http://localhost:8025',trust_env=False) as mail:
                message=next(m for m in mail.get('/api/v1/messages').json()['messages'] if any(to['Address']==profile['email'] for to in m['To']))
                content=mail.get('/api/v1/message/'+message['ID']).json()['Text']
            token=re.search(r'token=([\w-]+)',content).group(1)
            assert c.post('/api/auth/verify',params={'token':token}).status_code==200
            login=c.post('/api/auth/login',json={'email':profile['email'],'password':PASSWORD});assert login.status_code==200,login.text
            c.headers['X-CSRF-Token']=login.json()['csrf']
            assert c.post(f'/api/stages/{sid}/start').status_code==200
            assert len(c.get(f'/api/stages/{sid}/tasks').json()[0]['examples'])==1
            assert admin.put(f'/api/admin/tasks/{tid}',json=task).status_code==409
            s=c.post(f'/api/tasks/{tid}/submissions',json={'code':code});assert s.status_code==202,s.text
            judged=wait(c,s.json()['id']);assert judged['status']=='Accepted' and judged['score']==80,judged
            rows=c.get(f'/api/results/{oid}').json();assert len(rows)==1 and rows[0]['score']==80
            assert c.post(f'/api/stages/{sid}/finish').status_code==200
            assert c.post(f'/api/tasks/{tid}/submissions',json={'code':code}).status_code==403
    finally:
        event['status']='draft';admin.put('/api/admin/olympiads/'+oid,json=event)


def test_cannot_self_change_educational_category(clients,events):
    assert clients['school'].post('/api/registrations/'+events['SPO']['o']['id'],json={'course':1,'consent_data':True,'consent_rules':True}).status_code==403
    assert clients['spo1'].post('/api/registrations/'+events['SCHOOL']['o']['id'],json={'school_class':10,'consent_data':True,'consent_rules':True}).status_code==403
