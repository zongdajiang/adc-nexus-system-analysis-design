"""Exercise the release Docker image against a dedicated loopback CI database.

Never accepts hosted connection strings. No business writes apart from the
application's normal synthetic seed/migrations; no administrator login.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
assert os.environ.get('ADC_CONTAINER_CHECK') == 'true', 'Explicit isolated-container check required'
uri = urllib.parse.urlparse(os.environ['DATABASE_URL'])
assert uri.scheme == 'postgresql' and uri.hostname in ('localhost', '127.0.0.1')
assert uri.path.startswith('/adc_container_'), 'Only a dedicated adc_container_* fixture is allowed'
assert os.name != 'nt', 'Uses Linux host networking; run in the Linux CI job'
version = ET.parse(root / 'pom.xml').getroot().find('{http://maven.apache.org/POM/4.0.0}version').text
image = 'adc-nexus:release-check'
name = 'adc-release-check-' + secrets.token_hex(6)
guard_name = name + '-guard'
environment = {
    **os.environ, 'APP_ENV': 'PRODUCTION', 'DEMO_MODE': 'false', 'SEED_DATA': 'true',
    'PORT': '8090', 'TZ': 'Asia/Shanghai', 'ADMIN_PASSWORD': secrets.token_urlsafe(32),
    'PGPASSWORD': urllib.parse.unquote(uri.password or ''),
}
checks = []


def run(*args, check=True):
    return subprocess.run(args, env=environment, capture_output=True, text=True,
                          encoding='utf-8', timeout=120, check=check)


def record(label, condition):
    assert condition, label
    checks.append({'name': label, 'passed': True})
    print('PASS', label, flush=True)


def request(path, expected=200):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8090' + path, timeout=10) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, body = error.code, error.read()
    assert status == expected, (path, status)
    return body


def ready():
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            data = json.loads(request('/api/health'))
            if data.get('ok'):
                return data
        except (OSError, ValueError, AssertionError):
            pass
        time.sleep(1)
    raise AssertionError('Container did not reach healthy state')


def start():
    run('docker', 'run', '--detach', '--name', name, '--network', 'host',
        '--memory', '512m', *[arg for key in ('DATABASE_URL', 'APP_ENV', 'DEMO_MODE',
        'SEED_DATA', 'PORT', 'TZ', 'ADMIN_PASSWORD') for arg in ('--env', key)], image)
    return ready()


def snapshot():
    rows = {}
    for table in ('organizations', 'clinics', 'dentists', 'patients', 'appointments', 'clinical_visits'):
        query = ('SELECT count(*),md5(coalesce(string_agg(row_to_json(t)::text,\'\' '
                 'ORDER BY row_to_json(t)::text),\'\')) FROM ' + table + ' t')
        value = run('psql', '-h', uri.hostname, '-p', str(uri.port or 5432),
                    '-U', urllib.parse.unquote(uri.username or ''), '-d', uri.path[1:],
                    '-At', '-v', 'ON_ERROR_STOP=1', '-c', query).stdout.strip().split('|')
        rows[table] = {'rows': int(value[0]), 'content_md5': value[1]}
    return rows


try:
    guard_env = environment.copy()
    guard_env.pop('DATABASE_URL', None)
    guard = subprocess.run(['docker', 'run', '--rm', '--name', guard_name,
                            '--env', 'APP_ENV=PRODUCTION', image], env=guard_env,
                           capture_output=True, text=True, encoding='utf-8', timeout=30)
    record('Production refuses an absent external database',
           guard.returncode != 0 and '托管部署必须配置 PostgreSQL' in guard.stderr)
    health = start()
    record('Production image boots with PostgreSQL and the expected JDBC version',
           health['database'] == 'PostgreSQL' and health['data_access'] == 'JAVA_JDBC'
           and health['version'] == version and health['synthetic'] and not health['demo_mode'])
    record('Container runs as unprivileged UID 10001', run('docker', 'exec', name, 'id', '-u').stdout.strip() == '10001')
    record('The container memory limit is 512 MiB',
           int(run('docker', 'inspect', '--format', '{{.HostConfig.Memory}}', name).stdout) == 512 * 1024 * 1024)
    for path in ('/', '/practice-setup.js', '/followups.js', '/setup.css'):
        record('Public asset is available: ' + path, bool(request(path)))
    for path in ('/api/patients', '/api/followups', '/api/resources', '/api/admin/access'):
        record('Unauthenticated request is denied: ' + path, bool(request(path, 401)))
    original = snapshot()
    record('Synthetic clinic and patient data were seeded', original['patients']['rows'] > 0 and original['clinics']['rows'] > 0)
    run('docker', 'restart', name)
    ready()
    record('Business row contents survive a container restart', snapshot() == original)
    run('docker', 'rm', '--force', name)
    start()
    record('Business row contents survive replacement of the ephemeral container', snapshot() == original)
    result = {
        'passed': True, 'version': version, 'commit_sha': os.environ.get('GITHUB_SHA'),
        'image_id': run('docker', 'inspect', '--format', '{{.Image}}', name).stdout.strip(),
        'dockerfile_sha256': hashlib.sha256((root / 'Dockerfile').read_bytes()).hexdigest(),
        'checks': checks, 'memory_bytes': 512 * 1024 * 1024,
        'persisted_table_counts': {key: value['rows'] for key, value in original.items()},
        'production_mode': True, 'database': 'isolated loopback PostgreSQL',
        'hosted_deployment_verified': False, 'render_neon_credentials_used': False,
    }
    (root / 'qa/container-release-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
finally:
    # Only these uniquely named containers belong to this run. Never prune Docker.
    run('docker', 'rm', '--force', name, check=False)
