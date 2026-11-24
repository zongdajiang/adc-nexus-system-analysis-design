"""Run the local Chrome checks on a new, disposable demo database."""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.request import urlopen


root = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
with TemporaryDirectory(prefix="adc-responsive-") as data, socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    base = f"http://127.0.0.1:{port}"
    password = secrets.token_urlsafe(24)
    env = {**os.environ, "APP_ENV": "DEMO", "DEMO_MODE": "true", "SEED_DATA": "true",
           "DEMO_SCENARIO_MODE": "daily", "ADMIN_PASSWORD": password,
           "DATA_DIR": data, "PORT": str(port), "BIND_ADDRESS": "127.0.0.1", "ADC_RESPONSIVE_ADMIN": password}
    for name in ("DATABASE_URL", "ADC_TEST_NOW", "ADC_TEST_NOW_FILE", "ADC_TEST_LEGACY_PATIENT_WEB"):
        env.pop(name, None)
    args = [env.get("ADC_JAVA", "java"), "-Dfile.encoding=UTF-8", "-jar", "target/adc-nexus.jar"]
    with (output/"fixture.log").open("wb") as log:
        server = subprocess.Popen(args, cwd=root, env=env, stdout=log, stderr=log)
        try:
            for _ in range(180):
                if server.poll() is not None:
                    raise RuntimeError("Demo fixture exited during start")
                try:
                    with urlopen(base+"/api/health", timeout=2) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(.2)
            else:
                raise RuntimeError("Demo fixture did not become ready")
            subprocess.run([env.get("ADC_NODE", "node"), str(root/"tools/verify_responsive.mjs"),
                            base, str(output), *sys.argv[2:]], cwd=root, env=env, check=True)
        finally:
            server.terminate()
            server.wait(timeout=15)
