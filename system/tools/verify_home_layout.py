"""Check the bounded homepage patch; browser measurements are collected separately."""
import argparse
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--baseline-jar', required=True, type=Path)
args = parser.parse_args()
jar = ROOT / 'target/adc-nexus.jar'
digest = lambda data: hashlib.sha256(data).hexdigest()
checks = []


def check(name, passed):
    assert passed, name
    checks.append({'name': name, 'passed': True})
    print('PASS', name)


with zipfile.ZipFile(args.baseline_jar) as old, zipfile.ZipFile(jar) as new:
    old_files = {n: digest(old.read(n)) for n in old.namelist() if not n.endswith('/')}
    new_files = {n: digest(new.read(n)) for n in new.namelist() if not n.endswith('/')}
    check('No JAR entries added or removed', old_files.keys() == new_files.keys())
    changed = sorted(n for n in old_files if old_files[n] != new_files[n])
    check('Only homepage stylesheet and CSS cache key changed',
          changed == ['web/index.html', 'web/practice.css'])
    marker = b'/* Public site:'
    check('Workspace and authentication CSS preserved byte-for-byte',
          old.read('web/practice.css').split(marker)[0] == new.read('web/practice.css').split(marker)[0])
    check('HTML change is only the homepage CSS cache key',
          old.read('web/index.html').replace(b'/practice.css?v=1.4.0-rc1',
                                             b'/practice.css?v=1.4.0-layout1') == new.read('web/index.html'))
    for resource in ('practice.css', 'index.html'):
        url = 'http://127.0.0.1:8087/' + (resource if resource != 'index.html' else '')
        with urllib.request.urlopen(url, timeout=5) as response:
            check('Served ' + resource + ' matches current JAR',
                  digest(response.read()) == new_files['web/' + resource])

qa_dir = ROOT / 'qa/home-layout-20261022'
measurements = json.loads((qa_dir / 'measurements-final.json').read_text('utf-8'))
slides = json.loads((qa_dir / 'slides-final.json').read_text('utf-8'))
check('Ten viewport cases recorded', len(measurements) == 10)
check('All measured alignment, overflow, header and image checks passed',
      all(all(case['checks'].values()) for case in measurements))
check('Three distinct slide layouts passed',
      len(slides) == 3 and len({s['slide'] for s in slides}) == 3
      and all(all(s['checks'].values()) for s in slides))
proofs = {}
for filename, count in [('homepage-contract-tests.json', 32), ('clinic-ui-tests.json', 20),
                        ('practice-ui-tests.json', 32), ('web-request-tests.json', 10)]:
    proof_file = ROOT / 'qa' / filename
    proof = json.loads(proof_file.read_text('utf-8-sig'))
    proofs[filename] = {'expected_checks': count, 'sha256': digest(proof_file.read_bytes())}
    check(filename + ' passed', bool(proof.get('passed')))

result = {
    'date': '2026-10-22', 'version': '1.4.0-rc1', 'patch': 'homepage-layout1',
    'passed': True, 'jar_sha256': digest(jar.read_bytes()),
    'baseline_jar_sha256': digest(args.baseline_jar.read_bytes()),
    'changed_jar_entries': changed, 'unchanged_jar_entries': len(old_files) - len(changed),
    'scope_checks': checks, 'viewport_cases': measurements, 'slide_cases': slides,
    'regression_checks_rerun': 94, 'regression_proofs': proofs,
    'full_database_and_role_regression_rerun': False,
    'historical_468_checks_relabelled_as_current': False,
    'public_deployment_verified': False,
}
(ROOT / 'qa/home-layout-review-20261022.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('COMPLETE bounded layout review; historical backend evidence retains its original JAR hash.')
