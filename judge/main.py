"""Trusted judge gateway. Docker socket belongs here only, never in API/worker.
No user code runs in this process. Inputs are sent over stdin to isolated containers.
"""
import os, secrets, threading, time, json, logging
import docker
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, ConfigDict

app=FastAPI(title='Isolated judge')
client=docker.from_env()
slots=threading.BoundedSemaphore(2)
IMAGE=os.getenv('SANDBOX_IMAGE','olympiad-sandbox:local')
TOKEN=os.environ['JUDGE_TOKEN']

class Case(BaseModel):
    model_config=ConfigDict(extra='forbid')
    input: str=Field(max_length=100000)
    expected: str=Field(max_length=100000)
class Job(BaseModel):
    model_config=ConfigDict(extra='forbid')
    code: str=Field(max_length=50000)
    time_limit: int=Field(ge=1,le=10)
    memory_limit: int=Field(ge=32,le=256)
    tests: list[Case]=Field(min_length=1,max_length=50)
    public_run: bool=False

def execute(job,case):
    container=None; sock=None
    try:
        container=client.containers.create(IMAGE,network_mode='none',user='0:0',read_only=True,cap_drop=['ALL'],cap_add=['SETUID','SETGID','KILL'],security_opt=['no-new-privileges:true'],pids_limit=16,mem_limit=f'{job.memory_limit}m',memswap_limit=f'{job.memory_limit}m',nano_cpus=1_000_000_000,ulimits=[docker.types.Ulimit(name='nofile',soft=32,hard=32),docker.types.Ulimit(name='fsize',soft=1048576,hard=1048576),docker.types.Ulimit(name='cpu',soft=job.time_limit,hard=job.time_limit+1)],tmpfs={'/tmp':'rw,noexec,nosuid,nodev,size=8m,mode=1777'},stdin_open=True,detach=True,log_config=docker.types.LogConfig(type='json-file',config={'max-size':'16m','max-file':'1'}),environment={})
        sock=container.attach_socket(params={'stdin':1,'stdout':0,'stderr':0,'stream':1})
        container.start()
        payload=json.dumps({'code':job.code,'input':case.input,'timeout':job.time_limit}).encode()+b'\n'
        sock._sock.sendall(payload); sock.close(); sock=None
        started=time.monotonic()
        while True:
            container.reload()
            if container.status=='exited': break
            if time.monotonic()-started>job.time_limit+3:
                container.kill(); return {'status':'Time Limit Exceeded'}
            time.sleep(.025)
        if container.attrs['State'].get('OOMKilled'): return {'status':'Memory Limit Exceeded'}
        # Only the root supervisor writes to this channel; user stdout/stderr are captured.
        data=container.logs(stdout=True,stderr=False)
        if len(data)>16 * 1024 * 1024: return {'status':'System Error'}
        result=json.loads(data)
        if result['status']=='OK':
            result['status']='Accepted' if result['stdout'].split()==case.expected.split() else 'Wrong Answer'
        # Compare the full bounded output first; shorten only the displayed console.
        result['stdout']=result.get('stdout','')[:16384]
        result['stderr']=result.get('stderr','')[:4096]
        return result
    except Exception:
        logging.exception('Sandbox infrastructure failure')
        return {'status':'System Error'}
    finally:
        if sock: sock.close()
        if container: container.remove(force=True)

@app.get('/health')
def health():
    client.ping(); client.images.get(IMAGE); return {'status':'ok'}

@app.post('/judge')
def judge(job:Job,authorization:str=Header(default='')):
    if not TOKEN or not secrets.compare_digest(authorization,'Bearer '+TOKEN): raise HTTPException(403,'Forbidden')
    if not slots.acquire(blocking=False): raise HTTPException(503,'Judge busy')
    try:
        results=[execute(job,c) for c in job.tests]
        passed=sum(r['status']=='Accepted' for r in results)
        status=next((r['status'] for r in results if r['status']!='Accepted'),'Accepted')
        data={'status':status,'passed':passed,'total':len(results)}
        if job.public_run: data['tests']=results
        else: data['tests']=[{'status':r['status']} for r in results]
        return data
    finally: slots.release()
