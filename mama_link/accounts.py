"""Local prototype accounts; server-side sessions and isolated records."""
import hashlib
import hmac
import json
import secrets
import time
from uuid import uuid4


def initialize(store):
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT UNIQUE, salt TEXT, password TEXT, role TEXT, profile TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT, expires REAL)')
        db.execute('CREATE TABLE IF NOT EXISTS imports (id TEXT PRIMARY KEY, owner TEXT, payload TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS connections (owner TEXT PRIMARY KEY, enabled INTEGER)')


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()


def register(store, username, password, profile):
    uid, salt = str(uuid4()), secrets.token_hex(16)
    with store.connect() as db:
        db.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)',
                   (uid, username.lower(), salt, password_hash(password, salt), 'woman', json.dumps(profile)))
    return uid


def login(store, username, password):
    with store.connect() as db:
        row = db.execute('SELECT id, salt, password FROM users WHERE username=?', (username.lower(),)).fetchone()
    salt = row[1] if row else '00' * 16
    valid = hmac.compare_digest(password_hash(password, salt), row[2] if row else '0' * 128)
    return row[0] if row and valid else None


def session(store, uid):
    token = secrets.token_hex(32)
    with store.connect() as db:
        db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
        db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (hashlib.sha256(token.encode()).hexdigest(), uid, time.time() + 12 * 3600))
    return token


def revoke(store, token):
    with store.connect() as db:
        db.execute('DELETE FROM sessions WHERE token=?', (hashlib.sha256(token.encode()).hexdigest(),))


def identity(store, token):
    with store.connect() as db:
        row = db.execute('SELECT u.id, u.username, u.role, u.profile FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?',
                         (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
    return {'id': row[0], 'username': row[1], 'role': row[2], 'profile': json.loads(row[3])} if row else None
