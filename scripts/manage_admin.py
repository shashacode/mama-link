"""Explicit local administrator promotion; never grants roles through registration."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mama_link.core import ROOT
from mama_link.storage import Store
from mama_link.accounts import initialize

parser = argparse.ArgumentParser(description='Promote an existing local demo account to administrator')
parser.add_argument('username')
args = parser.parse_args()
store = Store(ROOT / '.local/mama-link.sqlite3')
initialize(store)
with store.connect() as db:
    changed = db.execute("UPDATE users SET role='admin' WHERE username=?", (args.username.lower(),)).rowcount
if not changed:
    parser.error('Create that account in the local app first')
print('Administrator access enabled for the named local account. Reload the app.')
