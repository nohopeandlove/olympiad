"""Run real sandbox regressions via the trusted worker's private judge network."""
import subprocess
import pytest

@pytest.mark.parametrize('code,expected,status', [
    ("print('x'*60000)", 'x'*60000, 'Accepted'),
    ("print('Я'*40000)", 'Я'*40000, 'Accepted'),
    ("print('x'*60000+'bad')", 'x'*60000, 'Wrong Answer'),
    ('while True: print("x"*10000)', '', 'Runtime Error'),
    ('while True: pass', '', 'Time Limit Exceeded'),
    ('a=bytearray(400*1024*1024)', '', 'Memory Limit Exceeded'),
], ids=['long-correct','unicode-correct','wrong-tail','output-limit','cpu-limit','memory-limit'])
def test_full_comparison_and_bounded_sandbox(code, expected, status):
    payload={'code':code,'time_limit':2,'memory_limit':128,'tests':[{'input':'','expected':expected}],'public_run':True}
    source=f'''import httpx
from app.config import settings
with httpx.Client(timeout=30,trust_env=False) as c:
 r=c.post(settings.judge_url+'/judge',headers={{'Authorization':'Bearer '+settings.judge_token}},json={payload!r})
 assert r.status_code==200,r.status_code
 data=r.json()
 assert data['status']=={status!r},data['status']
 assert len(data['tests'][0].get('stdout',''))<=16384
 assert len(data['tests'][0].get('stderr',''))<=4096
 print(data['status'])
'''
    result=subprocess.run(['docker','compose','exec','-T','worker','python','-'],input=source,text=True,capture_output=True,timeout=40)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()==status
