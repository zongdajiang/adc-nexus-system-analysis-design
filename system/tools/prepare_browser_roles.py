"""Install temporary passwords in an explicitly isolated browser fixture only.

Receives role/password pairs on stdin; never prints or stores plaintext passwords.
This helper cannot operate on data/adc-nexus.sqlite or a hosted database.
"""
import argparse
import base64
import hashlib
import json
import secrets
import sqlite3
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--fixture', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
folder = (root / args.fixture).resolve()
assert folder.parent == (root / 'data').resolve()
assert folder.name.startswith('browser-fixture-') and (folder / 'server.log').is_file()
database = folder / 'adc-nexus.sqlite'
assert database.is_file()
roles = json.load(sys.stdin)
assert set(roles) == {'FRONT_DESK','DENTIST','CASHIER','CLINIC_MANAGER','HQ_OPERATIONS','HQ_FINANCE','PATIENT','ADMIN'}
with sqlite3.connect(database) as connection:
    for role, password in roles.items():
        assert isinstance(password, str) and len(password) >= 24
        user = 'jdbc-owner' if role == 'ADMIN' else 'jdbc-demo-' + role.lower()
        salt = secrets.token_bytes(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000, 32)
        result = connection.execute('UPDATE app_users SET password_salt=?,password_hash=?,password_iterations=600000 WHERE id=?',
                                    (base64.b64encode(salt).decode(),base64.b64encode(hashed).decode(),user))
        assert result.rowcount == 1
print('Prepared 8 isolated synthetic role logins. No existing local accounts were touched.')
