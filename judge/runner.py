"""Runs inside the disposable unprivileged sandbox, never in the trusted services."""
import json, subprocess, selectors, time, os
from pathlib import Path

def oom_count():
    try:
        data=dict(line.split() for line in Path('/sys/fs/cgroup/memory.events').read_text().splitlines())
        return int(data.get('oom_kill',0))
    except OSError: return 0

job=json.loads(input())
Path('/tmp/main.py').write_text(job['code'])
result={'status':'Runtime Error','stdout':'','stderr':''}
try:
    compile(job['code'],'main.py','exec')
except SyntaxError as e:
    result.update(status='Interpreter Error',stderr=str(e)[:4096])
else:
    with open('/tmp/input','w+') as stdin:
        stdin.write(job['input']); stdin.seek(0)
        def drop_privileges():
            os.setgroups([]); os.setgid(65534); os.setuid(65534)
        oom_before=oom_count()
        p=subprocess.Popen(['python3','-I','-B','/tmp/main.py'],stdin=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=drop_privileges)
        selector=selectors.DefaultSelector()
        selector.register(p.stdout,selectors.EVENT_READ,'stdout'); selector.register(p.stderr,selectors.EVENT_READ,'stderr')
        output={'stdout':bytearray(),'stderr':bytearray()}; start=time.monotonic(); limited=False; timed=False
        while selector.get_map():
            if time.monotonic()-start>job['timeout']:
                timed=True; p.kill(); break
            for key,_ in selector.select(.025):
                chunk=key.fileobj.read1(4096)
                if not chunk: selector.unregister(key.fileobj); continue
                output[key.data].extend(chunk)
                if sum(len(v) for v in output.values())>32768:
                    limited=True; p.kill(); break
            if limited: break
        p.wait(timeout=1)
        result={'status':'Time Limit Exceeded' if timed or p.returncode==-24 else 'Runtime Error' if limited or p.returncode else 'OK','stdout':bytes(output['stdout'][:16384]).decode(errors='replace'),'stderr':bytes(output['stderr'][:16384]).decode(errors='replace')}
        if oom_count()>oom_before or 'MemoryError' in result['stderr']: result['status']='Memory Limit Exceeded'
print(json.dumps(result),flush=True)
