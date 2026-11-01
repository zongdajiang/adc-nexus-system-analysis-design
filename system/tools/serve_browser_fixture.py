"""Reopen an existing isolated browser fixture with the latest JAR; never the user's local DB."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import time
from verify import Client

parser=argparse.ArgumentParser();parser.add_argument('--fixture',required=True)
root=Path(__file__).resolve().parents[1]
folder=(root/parser.parse_args().fixture).resolve()
assert folder.parent==(root/'data').resolve() and folder.name.startswith('browser-fixture-')
assert (folder/'server.log').is_file() and (folder/'adc-nexus.sqlite').is_file()
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
env={**os.environ,'DEMO_MODE':'true','APP_ENV':'TEST','ADC_TEST_NOW':'2026-12-31T08:00:00',
     'DATA_DIR':str(folder),'BIND_ADDRESS':'127.0.0.1','PORT':str(port)}
env.pop('DATABASE_URL',None)
with (folder/'server-reopened.log').open('w',encoding='utf-8') as log:
    child=subprocess.Popen([os.environ.get('ADC_JAVA','java'),'--enable-native-access=ALL-UNNAMED',
        '-Dfile.encoding=UTF-8','-jar','target/adc-nexus.jar'],cwd=root,env=env,stdout=log,stderr=log,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:
        base='http://127.0.0.1:'+str(port)
        for _ in range(200):
            try:Client(base).request('/health');break
            except Exception:
                if child.poll() is not None:raise RuntimeError('Isolated fixture failed to start')
                time.sleep(.15)
        else:raise RuntimeError('Isolated fixture health timeout')
        print('READY '+base+'/#/login',flush=True)
        print('Latest JAR, existing isolated synthetic fixture. Enter stops this child.',flush=True)
        input()
    finally:
        child.terminate()
        try:child.wait(timeout=15)
        except subprocess.TimeoutExpired:child.kill();child.wait()
        print('Owned fixture stopped; synthetic data retained.',flush=True)
