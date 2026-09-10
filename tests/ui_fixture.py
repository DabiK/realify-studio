"""Disposable browser fixture. Deliberately never starts a live Codex worker."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from studio import Store, Worker
from server import make_server
from test_studio import fake_provider

with tempfile.TemporaryDirectory(prefix='studio-ui-') as temp:
    store = Store(temp)
    store.access_code = 'browser-test-only'
    store.create_pack({'project_id': 'realify'})
    Worker(store, fake_provider).run_one()
    print('Disposable UI fixture ready', flush=True)
    make_server(store, port=8788).serve_forever()
