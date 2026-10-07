"""Validate deploy topology without starting services or using real credentials."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ENV = '''SITE_DOMAIN=olympiad.example.org
ACME_EMAIL=ops@example.org
PUBLIC_ORIGIN=https://olympiad.example.org
POSTGRES_PASSWORD={password}
JUDGE_TOKEN={token}
JUDGE_URL=https://judge.olympiad.example.org
SMTP_HOST=smtp.example.org
SMTP_PORT=587
SMTP_FROM=ops@example.org
SMTP_STARTTLS=true
JUDGE_DOMAIN=judge.olympiad.example.org
APP_SERVER_IP=192.0.2.10
'''.format(password='a'*64, token='b'*64)


def config(files, env_file):
    cmd = ['docker', 'compose', '--env-file', str(env_file)]
    for file in files:
        cmd += ['-f', file]
    return subprocess.run(cmd+['config', '--format', 'json'], cwd=ROOT, capture_output=True, text=True, timeout=30)


def main():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env') as fixture:
        fixture.write(EXAMPLE_ENV)
        fixture.flush()
        for name, files in [('app', ['compose.yaml', 'compose.production.yaml']), ('judge', ['compose.judge.yaml'])]:
            result = config(files, fixture.name)
            if result.returncode:
                raise RuntimeError(f'{name}: invalid Compose configuration')
            data = json.loads(result.stdout)
            active = {key: value for key, value in data['services'].items() if not value.get('profiles')}
            assert {key for key, value in active.items() if value.get('ports')} == {'caddy'}
            assert {p['published'] for p in active['caddy']['ports']} == {'80', '443'}
            if name == 'app':
                assert 'judge' not in active and 'mailpit' not in active and 'sandbox-image' not in active
                assert set(active['worker']['depends_on']) == {'backend'}
                assert set(active['worker']['networks']) == {'data', 'web'}
                assert not any('docker.sock' in v.get('source', '') for s in active.values() for v in s.get('volumes', []))
                for who in ('backend', 'worker'):
                    env = active[who]['environment']
                    assert env['APP_ENV'] == 'production' and env['PUBLIC_ORIGIN'].startswith('https://')
                    assert env['JUDGE_URL'].startswith('https://') and env['SMTP_HOST'] != 'mailpit'
                    assert env['SMTP_STARTTLS'] == 'true'
            else:
                assert not {'postgres', 'redis', 'backend', 'worker'} & active.keys()
                assert not active['judge'].get('ports')
                assert data['networks']['judging']['internal']
            print(f'{name}: deploy topology passed')
    for example, files in [('.env.production.example', ['compose.yaml', 'compose.production.yaml']), ('.env.judge.example', ['compose.judge.yaml'])]:
        assert config(files, ROOT/example).returncode != 0, 'Empty credentials must reject configuration'
    print('Empty deploy examples refuse startup')


if __name__ == '__main__':
    main()
