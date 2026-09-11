import hashlib
import importlib.util
import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image
from studio import ROOT, Store, Worker, validate_post
from server import make_server

POST = {'title': 'Post de test', 'description': 'Images de test uniquement.', 'hashtags': ['#Test']}


def fake_provider(job, folder):
    """Explicit test fixture, never used by the production server."""
    brief = json.loads((folder / 'brief.json').read_text())
    size = {'2:3': (512, 768), '1:1': (512, 512), '3:2': (768, 512)}[brief['ratio']]
    for i, key in enumerate(job['slots']):
        Image.new('RGB', size, (30 + i * 10, 70, 40)).save(folder / 'images' / f'{key}.png')
    (folder / 'post.json').write_text(json.dumps(POST))


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def ready(self):
        p = self.store.create_pack({'project_id': 'realify'})
        Worker(self.store, fake_provider).run_one()
        return self.store.pack(p['id'])

    def test_real_analytics_preserve_all_daily_rows(self):
        spec = importlib.util.spec_from_file_location('analyze', ROOT / 'scripts/analyze.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = module.build()
        self.assertEqual(data['totals']['Video Views'], 3487296)
        self.assertEqual(data['totals']['Likes'], 126117)
        self.assertEqual(len(data['daily']), 365)
        self.assertEqual(len(data['posts']), 15)
        self.assertEqual(data['followers']['current'], 6520)
        self.assertEqual(data['last30']['Video Views'], 908)
        self.assertTrue(all(h['days'] == 7 for h in data['followers']['hourly_activity']))

    def test_generation_correction_and_restore_preserve_other_images(self):
        p = self.ready()
        self.assertEqual(p['status'], 'ready')
        self.assertEqual(len(p['slots']), 5)
        originals = {s['key']: s['active'] for s in p['slots']}
        digests = {k: hashlib.sha256(self.store.media_path(v).read_bytes()).hexdigest() for k, v in originals.items()}
        job = self.store.correct(p['id'], {'slot': 'cover', 'instruction': 'Ajouter le texte BONJOUR.'})
        with self.assertRaises(ValueError):
            self.store.correct(p['id'], {'slot': 'cover', 'instruction': 'Double demande'})
        Worker(self.store, fake_provider).run_one()
        updated = self.store.pack(p['id'])
        self.assertEqual(len(updated['feedback']), 1)
        self.assertEqual(len(updated['slots'][0]['versions']), 2)
        self.assertEqual(updated['post'], p['post'])
        for slot in updated['slots'][1:]:
            self.assertEqual(slot['active'], originals[slot['key']])
        for key, filename in originals.items():
            self.assertEqual(hashlib.sha256(self.store.media_path(filename).read_bytes()).hexdigest(), digests[key])
        self.store.restore(p['id'], {'slot': 'cover', 'file': originals['cover']})
        self.assertEqual(self.store.pack(p['id'])['slots'][0]['active'], originals['cover'])

    def test_partial_failure_resumes_only_missing_slots(self):
        p = self.store.create_pack({'project_id': 'realify'})
        def partial(job, folder):
            subset = {**job, 'slots': job['slots'][:2]}
            fake_provider(subset, folder)
            raise RuntimeError('Quota simulated')
        Worker(self.store, partial).run_one()
        failed = self.store.jobs()[0]
        self.assertEqual(failed['state'], 'failed')
        self.assertEqual(len(failed['completed_slots']), 2)
        original = self.store.pack(p['id'])['slots'][0]['active']
        retry = self.store.retry(failed['id'])
        self.assertEqual(len(retry['slots']), 3)
        Worker(self.store, fake_provider).run_one()
        complete = self.store.pack(p['id'])
        self.assertEqual(complete['status'], 'ready')
        self.assertEqual(complete['slots'][0]['active'], original)

    def test_correction_can_succeed_on_an_incomplete_pack(self):
        p = self.store.create_pack({'project_id': 'realify'})
        def partial(job, folder):
            fake_provider({**job, 'slots': ['cover']}, folder)
            (folder / 'post.json').unlink()
        Worker(self.store, partial).run_one()
        job = self.store.correct(p['id'], {'slot': 'cover', 'instruction': 'Moment spontané.'})
        Worker(self.store, fake_provider).run_one()
        result = next(j for j in self.store.jobs() if j['id'] == job['id'])
        self.assertEqual(result['state'], 'completed')
        self.assertEqual(self.store.pack(p['id'])['status'], 'failed')
        self.assertEqual(len(self.store.pack(p['id'])['slots'][0]['versions']), 2)

    def test_missing_metadata_can_resume_without_new_images(self):
        p = self.store.create_pack({'project_id': 'realify'})
        def no_metadata(job, folder):
            fake_provider(job, folder)
            (folder / 'post.json').unlink()
        Worker(self.store, no_metadata).run_one()
        self.assertEqual(self.store.pack(p['id'])['status'], 'failed')
        retry = self.store.retry(self.store.jobs()[0]['id'])
        self.assertEqual(retry['slots'], [])
        Worker(self.store, fake_provider).run_one()
        self.assertEqual(self.store.pack(p['id'])['status'], 'ready')

    def test_generic_project_brief_is_isolated(self):
        project = self.store.create_project({'name': 'Botanique', 'universe': 'Plantes', 'direction': 'Natural morning light', 'subjects': ['Orchidée'], 'ratio': '1:1'})
        p = self.store.create_pack({'project_id': project['id']})
        Worker(self.store, fake_provider).run_one()
        job = self.store.jobs()[0]
        brief = json.loads((self.store.runtime / 'jobs' / job['id'] / 'brief.json').read_text())
        self.assertEqual(brief['project']['universe'], 'Plantes')
        self.assertEqual(brief['style_reference_images'], [])
        self.assertEqual(brief['ratio'], '1:1')
        self.assertTrue(all(s['subject'] == 'Orchidée' for s in brief['requested_slots']))
        self.assertEqual(self.store.packs('realify'), [])
        self.assertEqual(self.store.pack(p['id'])['status'], 'ready')

    def test_feedback_is_project_scoped_and_reaches_next_job(self):
        p = self.ready()
        self.store.feedback(p['id'], {'text': 'Plus de lumière naturelle.'})
        new = self.store.create_pack({'project_id': 'realify'})
        Worker(self.store, fake_provider).run_one()
        job = self.store.jobs()[0]
        brief = json.loads((self.store.runtime / 'jobs' / job['id'] / 'brief.json').read_text())
        self.assertIn('Plus de lumière naturelle.', json.dumps(brief, ensure_ascii=False))
        self.assertNotEqual(new['concept']['id'], p['concept']['id'])

    def test_mark_published_prepares_next_once(self):
        p = self.ready()
        result = self.store.publish(p['id'], {'url': 'https://www.tiktok.com/@test/video/123'})
        self.assertIsNotNone(result['next'])
        self.assertEqual(len(self.store.packs()), 2)
        self.store.publish(p['id'], {})
        self.assertEqual(len(self.store.packs()), 2)

    def test_paused_auto_next(self):
        p = self.ready()
        project = self.store.project('realify')
        self.store.update_project('realify', {**project, 'auto_next': False})
        self.assertIsNone(self.store.publish(p['id'], {})['next'])
        self.assertEqual(len(self.store.packs()), 1)

    def test_recovery_does_not_silently_regenerate(self):
        p = self.store.create_pack({'project_id': 'realify'})
        with self.store.db() as db:
            db.execute("UPDATE jobs SET state='running'")
        Worker(self.store, fake_provider).recover()
        self.assertEqual(self.store.jobs()[0]['state'], 'failed')
        self.assertEqual(self.store.pack(p['id'])['status'], 'failed')
        self.assertFalse(Worker(self.store, fake_provider).run_one())

    def test_bad_output_cannot_be_ready(self):
        p = self.store.create_pack({'project_id': 'realify'})
        def bad(job, folder):
            (folder / 'images/cover.png').write_text('not an image')
            (folder / 'post.json').write_text(json.dumps(POST))
        Worker(self.store, bad).run_one()
        self.assertEqual(self.store.pack(p['id'])['status'], 'failed')
        self.assertTrue(all(not s['active'] for s in self.store.pack(p['id'])['slots']))

    def test_auth_and_paths(self):
        self.assertIsNone(self.store.authenticate('wrong'))
        session = self.store.authenticate(self.store.access_code)
        self.assertTrue(self.store.authorized(session))
        self.assertFalse(self.store.authorized('invalid'))
        with self.assertRaises(ValueError):
            self.store.media_path('../../access-code')
        with self.assertRaises(ValueError):
            validate_post({**POST, 'hashtags': ['#invalid tag']})
        self.assertEqual(validate_post({**POST, 'description': 'A\\nB'})['description'], 'A\nB')


class HttpTests(unittest.TestCase):
    ready = StudioTests.ready

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.httpd = make_server(self.store, port=0)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.httpd.server_port}'

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, data=None, cookie=None, origin=None):
        headers = {}
        if cookie: headers['Cookie'] = cookie
        if origin: headers['Origin'] = origin
        if data is not None: headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.base + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        return urllib.request.urlopen(request)

    def login(self):
        response = self.request('/api/login', {'code': self.store.access_code})
        self.assertIn('HttpOnly', response.headers['Set-Cookie'])
        return response.headers['Set-Cookie'].split(';')[0]

    def test_http_auth_csrf_download_and_logout(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/state')
        self.assertEqual(exc.exception.code, 401)
        exc.exception.close()
        cookie = self.login()
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/packs', {'project_id': 'realify'}, cookie, 'https://evil.example')
        self.assertEqual(exc.exception.code, 403)
        exc.exception.close()
        p = self.ready()
        download = self.request(f'/api/packs/{p["id"]}/download', cookie=cookie)
        self.assertEqual(download.headers['Content-Type'], 'application/zip')
        with zipfile.ZipFile(io.BytesIO(download.read())) as z:
            self.assertEqual(len([n for n in z.namelist() if n.endswith('.png')]), 5)
            self.assertEqual(json.loads(z.read('post.json')), POST)
            self.assertEqual(z.namelist()[0], '01_cover.png')
        self.request('/api/logout', {}, cookie)
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.request('/api/state', cookie=cookie)
        self.assertEqual(exc.exception.code, 401)
        exc.exception.close()


if __name__ == '__main__':
    unittest.main()
