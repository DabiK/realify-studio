"""Persistent production core. No image API: the only live provider is Codex CLI."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path


from domain import ROOT, CONCEPTS, uid, text, validate_post


class Store:
    def __init__(self, runtime):
        self._connections = threading.local()
        self.runtime = Path(runtime).resolve()
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime / 'studio.sqlite'
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS packs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, pack_id TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS stories (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, expires REAL NOT NULL);
            ''')
        if not self.projects():
            self.put_project({'id': 'realify', 'name': 'Realify AI', 'universe': 'One Piece',
                              'direction': 'One Piece made physically real. Photographic cinema and fictional candid film sets. Recognizable characters absorbed in action, invisible observer camera, no eye contact with the viewer, motivated natural light and tactile costumes. No text in generated images.',
                              'subjects': CONCEPTS[0]['subjects'], 'reference_files': [], 'ratio': '2:3', 'auto_next': True})
        tokenfile = self.runtime / 'access-code'
        if not tokenfile.exists():
            fd = os.open(tokenfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(secrets.token_urlsafe(24))
        self.access_code = tokenfile.read_text().strip()

    @contextmanager
    def db(self):
        existing = getattr(self._connections, "db", None)
        if existing is not None:
            yield existing
            return
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        self._connections.db = db
        try:
            with db:
                yield db
        finally:
            self._connections.db = None
            db.close()

    def projects(self):
        with self.db() as db:
            return [json.loads(r['data']) for r in db.execute('SELECT data FROM projects')]

    def put_project(self, project):
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO projects VALUES (?, ?)', (project['id'], json.dumps(project)))

    def project(self, pid):
        return next((p for p in self.projects() if p['id'] == pid), None)

    def create_project(self, data):
        project = {'id': uid(), 'name': text(data.get('name'), 80), 'universe': text(data.get('universe'), 160),
                   'direction': text(data.get('direction'), 3000), 'subjects': [text(s, 100) for s in data.get('subjects', [])],
                   'reference_files': [], 'ratio': data.get('ratio', '2:3'), 'auto_next': True}
        if not 1 <= len(project['subjects']) <= 20 or project['ratio'] not in ['2:3', '1:1', '3:2']:
            raise ValueError('Choisir 1 à 20 sujets et un format valide.')
        self.put_project(project)
        return project

    def update_project(self, pid, data):
        project = self.project(pid)
        if not project:
            raise ValueError('Projet introuvable.')
        subjects = [text(s, 100) for s in data.get('subjects', [])]
        if not 1 <= len(subjects) <= 20 or data.get('ratio') not in ['2:3', '1:1', '3:2'] or type(data.get('auto_next')) is not bool:
            raise ValueError('Sujets, format ou automatisation invalides.')
        if subjects != project['subjects']:
            project['custom_subjects'] = True
        project.update(universe=text(data.get('universe'), 160), direction=text(data.get('direction'), 3000),
                       subjects=subjects, ratio=data['ratio'], auto_next=data['auto_next'])
        self.put_project(project)
        return project

    def packs(self, project_id=None):
        with self.db() as db:
            rows = db.execute('SELECT data FROM packs WHERE project_id=?', (project_id,)) if project_id else db.execute('SELECT data FROM packs')
            return sorted((json.loads(r['data']) for r in rows), key=lambda p: p['created'], reverse=True)

    def pack(self, pid):
        with self.db() as db:
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if row is None:
                raise ValueError('Pack introuvable.')
            return json.loads(row['data'])

    @staticmethod
    def save_pack(db, pack):
        db.execute('INSERT OR REPLACE INTO packs VALUES (?, ?, ?)', (pack['id'], pack['project_id'], json.dumps(pack)))

    def jobs(self):
        with self.db() as db:
            jobs = [{**json.loads(r['data']), 'state': r['state']} for r in db.execute('SELECT * FROM jobs ORDER BY created DESC')]
        for job in jobs:
            if job['state'] == 'running':
                folder = self.runtime / 'jobs' / job['id'] / 'images'
                job['received_slots'] = [key for key in job['slots'] if (folder / f'{key}.png').is_file()]
            else:
                job['received_slots'] = job.get('completed_slots', [])
        return jobs

    def _queue(self, db, pack, slots, correction=''):
        if db.execute("SELECT 1 FROM jobs WHERE pack_id=? AND state IN ('queued','running')", (pack['id'],)).fetchone():
            raise ValueError('Ce pack a déjà une génération en cours.')
        jobs_today = db.execute('SELECT data FROM jobs WHERE created >= ?', (time.time() - 86400,)).fetchall()
        requested = sum(len(json.loads(r['data'])['slots']) for r in jobs_today)
        if requested + len(slots) > int(os.environ.get('STUDIO_DAILY_IMAGES', '40')):
            raise ValueError('Limite locale de demandes d’images sur 24 h atteinte. Les générations et reprises comptent dans cette limite.')
        job = {'id': uid(), 'pack_id': pack['id'], 'slots': slots, 'correction': correction,
               'created': time.time(), 'message': 'En attente', 'completed_slots': []}
        db.execute('INSERT INTO jobs VALUES (?, ?, ?, ?, ?)', (job['id'], pack['id'], 'queued', job['created'], json.dumps(job)))
        return job

    def create_pack(self, data, db=None):
        project = self.project(data.get('project_id'))
        if not project:
            raise ValueError('Projet introuvable.')
        previous = self.packs(project['id'])
        concept_id = data.get('concept_id', 'auto')
        if project['id'] == 'realify':
            concept = next((c for c in CONCEPTS if c['id'] == concept_id), None) if concept_id != 'auto' else CONCEPTS[len(previous) % len(CONCEPTS)]
            if not concept:
                raise ValueError('Concept introuvable.')
            if project.get('custom_subjects'):
                concept = {**concept, 'subjects': project['subjects']}
        else:
            concept = {'id': 'custom', 'title': f"{project['name']} · Série {len(previous) + 1:02}",
                       'family': project['universe'], 'scene': project['direction'], 'subjects': project['subjects']}
        count = data.get('count', 5)
        if type(count) is not int or not 1 <= count <= 5:
            raise ValueError('Choisir de 1 à 5 images par batch.')
        if 'subjects' in data:
            subjects_override = data['subjects']
            if not isinstance(subjects_override, list) or not 1 <= len(subjects_override) <= 20:
                raise ValueError('Choisir de 1 à 20 sujets.')
            concept = {**concept, 'subjects': [text(s, 100) for s in subjects_override]}
        subjects = [concept['subjects'][i % len(concept['subjects'])] for i in range(count)]
        keys = ['cover', 'slide_2', 'slide_3', 'slide_4', 'slide_5'][:count]
        slots = [{'key': key, 'subject': subjects[i], 'versions': [], 'active': None} for i, key in enumerate(keys)]
        pack = {'id': uid(), 'project_id': project['id'], 'title': concept['title'], 'concept': concept,
                'created': time.time(), 'status': 'queued', 'slots': slots, 'ratio': project['ratio'],
                'notes': text(data.get('notes', ''), 2000, False),
                'caption': '', 'post': None, 'feedback': [], 'published_at': None, 'publication_url': ''}
        if db is not None:
            self.save_pack(db, pack)
            self._queue(db, pack, keys)
        else:
            with self.db() as db:
                if not db.in_transaction:
                    db.execute('BEGIN IMMEDIATE')
                self.save_pack(db, pack)
                self._queue(db, pack, keys)
        return pack

    def correct(self, pid, data):
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Pack introuvable.')
            pack = json.loads(row['data'])
            slot = next((s for s in pack['slots'] if s['key'] == data.get('slot')), None)
            if not slot or not slot['active']:
                raise ValueError('Cette image n’est pas encore disponible.')
            instruction = text(data.get('instruction'), 1500)
            pack['feedback'].append({'created': time.time(), 'slot': slot['key'], 'text': instruction, 'kind': 'correction'})
            self.save_pack(db, pack)
            return self._queue(db, pack, [slot['key']], instruction)

    def retry(self, jid):
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
            if not row or row['state'] != 'failed':
                raise ValueError('Seul un travail en échec peut être repris.')
            old = json.loads(row['data'])
            pack = json.loads(db.execute('SELECT data FROM packs WHERE id=?', (old['pack_id'],)).fetchone()['data'])
            missing = [s for s in old['slots'] if s not in old.get('completed_slots', [])]
            if not missing and pack.get('post'):
                raise ValueError('Toutes les images de ce travail sont déjà disponibles.')
            return self._queue(db, pack, missing, old['correction'])

    def restore(self, pid, data):
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Pack introuvable.')
            pack = json.loads(row['data'])
            if db.execute("SELECT 1 FROM jobs WHERE pack_id=? AND state IN ('running','queued')", (pid,)).fetchone():
                raise ValueError('Attendre la fin de la génération avant de restaurer une version.')
            slot = next((s for s in pack['slots'] if s['key'] == data.get('slot')), None)
            if not slot or not any(v['file'] == data.get('file') for v in slot['versions']):
                raise ValueError('Version introuvable.')
            slot['active'] = data['file']
            self.save_pack(db, pack)
        return pack

    def feedback(self, pid, data):
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Post introuvable.')
            pack = json.loads(row['data'])
            pack['feedback'].append({'id': uid(), 'created': time.time(), 'text': text(data.get('text'), 1500), 'kind': 'direction', 'resolved_at': None})
            self.save_pack(db, pack)
        return pack

    def resolve_feedback(self, pid, data):
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            pack = self.pack(pid)
            feedback = next((f for f in pack['feedback'] if f.get('id') and f['id'] == data.get('feedback_id')), None)
            if not feedback:
                raise ValueError('Retour introuvable.')
            feedback['resolution'] = text(data.get('resolution'), 1500)
            feedback['resolved_at'] = time.time()
            self.save_pack(db, pack)
        return pack

    def metadata(self, pid, data):
        post = validate_post(data)
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Post introuvable.')
            pack = json.loads(row['data'])
            pack['post'] = post
            pack['title'] = post['title']
            pack['caption'] = post['description'] + '\n\n' + ' '.join(post['hashtags'])
            self.save_pack(db, pack)
        return pack

    def publish(self, pid, data):
        with self.db() as db:
            if not db.in_transaction:
                db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Post introuvable.')
            pack = json.loads(row['data'])
            if pack['published_at']:
                return {'pack': pack, 'next': None}
            if pack['status'] != 'ready' or not pack.get('post'):
                raise ValueError('Terminer les images et la fiche avant de marquer le post publié.')
            if db.execute("SELECT 1 FROM jobs WHERE pack_id=? AND state IN ('queued','running')", (pid,)).fetchone():
                raise ValueError('Une retouche est encore en cours.')
            url = text(data.get('url', ''), 400, False)
            if url:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.scheme != 'https' or parsed.hostname not in ['www.tiktok.com', 'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']:
                    raise ValueError('Utiliser un lien TikTok HTTPS.')
            pack['published_at'] = time.time()
            pack['publication_url'] = url
            self.save_pack(db, pack)
        result = {'pack': pack, 'next': None}
        if self.project(pack['project_id']).get('auto_next') and not any(not p['published_at'] for p in self.packs(pack['project_id'])):
            try:
                if pack.get('story_id'):
                    from stories import StoryService
                    service = StoryService(self)
                    story = service.story(pack['story_id'])
                    if len(story['episodes']) < len(story['outline']):
                        result['next'] = service.execute('story.next', {'story_id': story['id']}, f"auto-next-{pid}")
                else:
                    result['next'] = self.create_pack({'project_id': pack['project_id']})
            except ValueError as exc:
                result['next_error'] = str(exc)
        return result

    def authenticate(self, code):
        if not isinstance(code, str) or not secrets.compare_digest(code, self.access_code):
            return None
        token = secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires < ?', (time.time(),))
            db.execute('INSERT INTO sessions VALUES (?, ?)', (hashlib.sha256(token.encode()).hexdigest(), time.time() + 30 * 86400))
        return token

    def authorized(self, token):
        with self.db() as db:
            return db.execute('SELECT 1 FROM sessions WHERE token_hash=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone() is not None

    def media_path(self, name):
        root = (self.runtime / 'media').resolve()
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.suffix.lower() not in ['.png', '.jpg', '.webp']:
            raise ValueError('Image introuvable.')
        return path


# Compatibility import; the production worker is maintained independently.
from worker import Worker
