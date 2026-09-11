"""Persistent production core. No image API: the only live provider is Codex CLI."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
CONCEPTS = [
    {'id': 'villains', 'title': 'Les visages de la terreur', 'family': 'Instants cinéma',
     'reason': 'Le post méchants atteint 1,8 M de vues. Tester le cadrage, sans supposer que le sujet suffit.',
     'scene': 'Observed live-action moments in a lived-in pirate palace. Characters absorbed in an activity, unposed gestures, motivated natural light and physically credible materials.',
     'subjects': ['Donquixote Doflamingo', 'Kaido', 'Crocodile', 'Big Mom', 'Rob Lucci'],
     'image': 'doflamingo.jpg'},
    {'id': 'backstage', 'title': 'Quand la caméra s’arrête', 'family': 'Coulisses fictives',
     'reason': 'La Part 3 des coulisses atteint 7,49 % d’interactions, dans les 15 posts exportés.',
     'scene': 'Fictional behind-the-scenes photographs of a One Piece film production. Camera rigs and crew, natural daylight, candid between-takes moments, realistic props.',
     'subjects': ['Portgas D. Ace', 'Shanks', 'Nico Robin', 'Crocodile', 'Donquixote Doflamingo'],
     'image': 'ace.jpg'},
    {'id': 'creatures', 'title': 'Ils prennent vie', 'family': 'Créatures réalistes',
     'reason': 'Les Minks atteignent 57 k vues. Une piste secondaire pour répliquer un essai de cadrage.',
     'scene': 'Observed live-action creatures interacting with a lush pirate forest, physically credible fur and skin, recognizable silhouettes and spontaneous movement.',
     'subjects': ['Nekomamushi', 'Inuarashi', 'Carrot', 'Jinbe', 'Tony Tony Chopper'],
     'image': 'kaido.jpg'},
]


def uid():
    return uuid.uuid4().hex


def text(value, maximum=2000, required=True):
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        raise ValueError('Texte absent ou trop long.')
    return value.strip()


def validate_post(data):
    title = text(data.get('title'), 120)
    description = text(data.get('description'), 1800).replace('\\n', '\n')
    tags = data.get('hashtags')
    if not isinstance(tags, list) or not 1 <= len(tags) <= 5:
        raise ValueError('La fiche doit contenir 1 à 5 hashtags pertinents.')
    import re
    if any(not isinstance(t, str) or not re.fullmatch(r'#[\w]{1,60}', t) for t in tags):
        raise ValueError('Hashtag invalide.')
    return {'title': title, 'description': description, 'hashtags': list(dict.fromkeys(tags))}


class Store:
    def __init__(self, runtime):
        self.runtime = Path(runtime).resolve()
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime / 'studio.sqlite'
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS packs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, pack_id TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, data TEXT NOT NULL);
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
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        try:
            with db:
                yield db
        finally:
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
            return [{**json.loads(r['data']), 'state': r['state']} for r in db.execute('SELECT * FROM jobs ORDER BY created DESC')]

    def _queue(self, db, pack, slots, correction=''):
        if db.execute("SELECT 1 FROM jobs WHERE pack_id=? AND state IN ('queued','running')", (pack['id'],)).fetchone():
            raise ValueError('Ce pack a déjà une génération en cours.')
        jobs_today = db.execute('SELECT data FROM jobs WHERE created >= ?', (time.time() - 86400,)).fetchall()
        requested = sum(len(json.loads(r['data'])['slots']) for r in jobs_today)
        if requested + len(slots) > int(os.environ.get('STUDIO_DAILY_IMAGES', '24')):
            raise ValueError('Limite locale de demandes d’images sur 24 h atteinte. Les générations et reprises comptent dans cette limite.')
        job = {'id': uid(), 'pack_id': pack['id'], 'slots': slots, 'correction': correction,
               'created': time.time(), 'message': 'En attente', 'completed_slots': []}
        db.execute('INSERT INTO jobs VALUES (?, ?, ?, ?, ?)', (job['id'], pack['id'], 'queued', job['created'], json.dumps(job)))
        return job

    def create_pack(self, data):
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
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            self.save_pack(db, pack)
            self._queue(db, pack, keys)
        return pack

    def correct(self, pid, data):
        with self.db() as db:
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
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Post introuvable.')
            pack = json.loads(row['data'])
            pack['feedback'].append({'created': time.time(), 'text': text(data.get('text'), 1500), 'kind': 'direction'})
            self.save_pack(db, pack)
        return pack

    def metadata(self, pid, data):
        post = validate_post(data)
        with self.db() as db:
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


class Worker:
    def __init__(self, store, provider=None):
        self.store = store
        self.provider = provider or self.codex
        self.stop = threading.Event()

    def recover(self):
        with self.store.db() as db:
            for row in db.execute("SELECT * FROM jobs WHERE state='running'").fetchall():
                job = json.loads(row['data'])
                job['message'] = 'Génération interrompue au redémarrage. Reprise manuelle disponible.'
                db.execute("UPDATE jobs SET state='failed',data=? WHERE id=?", (json.dumps(job), job['id']))
                pack = json.loads(db.execute('SELECT data FROM packs WHERE id=?', (job['pack_id'],)).fetchone()['data'])
                pack['status'] = 'ready' if all(s['active'] for s in pack['slots']) and pack.get('post') else 'failed'
                self.store.save_pack(db, pack)

    def run(self):
        while not self.stop.is_set():
            if not self.run_one():
                self.stop.wait(2)

    def run_one(self):
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if not row:
                return False
            job = json.loads(row['data'])
            job['message'] = 'Création des images en cours'
            db.execute("UPDATE jobs SET state='running',data=? WHERE id=?", (json.dumps(job), job['id']))
            pack = json.loads(db.execute('SELECT data FROM packs WHERE id=?', (job['pack_id'],)).fetchone()['data'])
            pack['status'] = 'ready' if all(s['active'] for s in pack['slots']) and pack.get('post') else 'running'
            self.store.save_pack(db, pack)
        folder = self.store.runtime / 'jobs' / job['id']
        folder.mkdir(parents=True, exist_ok=True)
        error = None
        try:
            self.prepare(job, pack, folder)
            self.provider(job, folder)
        except Exception as exc:
            error = str(exc)[:700]
        if not job['correction']:
            try:
                post = validate_post(json.loads((folder / 'post.json').read_text()))
                with self.store.db() as db:
                    db.execute('BEGIN IMMEDIATE')
                    current = json.loads(db.execute('SELECT data FROM packs WHERE id=?', (pack['id'],)).fetchone()['data'])
                    current['post'] = post
                    current['title'] = post['title']
                    current['caption'] = post['description'] + '\n\n' + ' '.join(post['hashtags'])
                    self.store.save_pack(db, current)
            except Exception:
                if not pack.get('post'):
                    error = error or 'Fiche du post absente ou invalide. Reprendre la préparation.'
        # Import every valid artifact, even when a later tool call failed. Never discard prior versions.
        for key in job['slots']:
            output = folder / 'images' / f'{key}.png'
            if not output.exists():
                continue
            try:
                if output.is_symlink() or output.stat().st_size > 30 * 1024 * 1024:
                    raise ValueError('Fichier de sortie invalide.')
                with Image.open(output) as im:
                    width, height = im.size
                    im.verify()
                target = {'2:3': 2 / 3, '1:1': 1, '3:2': 3 / 2}[pack['ratio']]
                if min(width, height) < 512 or abs(width / height - target) > .04:
                    raise ValueError(f'Format reçu {width}×{height} incompatible avec {pack["ratio"]}.')
                dest = self.store.runtime / 'media' / pack['id'] / f'{key}-{uid()}.png'
                dest.parent.mkdir(parents=True, exist_ok=True)
                with Image.open(output) as im:
                    im.save(dest, format='PNG')
                filename = dest.relative_to(self.store.runtime / 'media').as_posix()
                version = {'file': filename, 'created': time.time(), 'instruction': job['correction'],
                           'job_id': job['id'], 'width': width, 'height': height,
                           'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}
                with self.store.db() as db:
                    db.execute('BEGIN IMMEDIATE')
                    current = json.loads(db.execute('SELECT data FROM packs WHERE id=?', (pack['id'],)).fetchone()['data'])
                    slot = next(s for s in current['slots'] if s['key'] == key)
                    slot['versions'].append(version)
                    slot['active'] = filename
                    self.store.save_pack(db, current)
                    job['completed_slots'].append(key)
                    db.execute('UPDATE jobs SET data=? WHERE id=?', (json.dumps(job), job['id']))
            except Exception as exc:
                error = str(exc)[:700]
        complete = len(job['completed_slots']) == len(job['slots']) and bool(self.store.pack(pack['id']).get('post'))
        job['message'] = 'Images disponibles' if complete else ('Génération incomplète. ' + (error or 'Codex n’a pas produit tous les fichiers attendus. Vérifier sa connexion et la disponibilité de la génération d’images.'))
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('UPDATE jobs SET state=?,data=? WHERE id=?', ('completed' if complete else 'failed', json.dumps(job), job['id']))
            current = json.loads(db.execute('SELECT data FROM packs WHERE id=?', (pack['id'],)).fetchone()['data'])
            current['status'] = 'ready' if all(s['active'] for s in current['slots']) and current.get('post') else 'failed'
            self.store.save_pack(db, current)
        return True

    def prepare(self, job, pack, folder):
        project = self.store.project(pack['project_id'])
        (folder / 'images').mkdir(exist_ok=True)
        refs = folder / 'references'
        refs.mkdir(exist_ok=True)
        requested = []
        continuity = []
        for slot in pack['slots']:
            if slot['active']:
                continuity_file = f"references/continuity-{slot['key']}.png"
                shutil.copy2(self.store.media_path(slot['active']), folder / continuity_file)
                continuity.append({'key': slot['key'], 'subject': slot['subject'], 'file': continuity_file})
            if slot['key'] not in job['slots']:
                continue
            reference = None
            if slot['active']:
                reference = f"references/{slot['key']}.png"
                shutil.copy2(self.store.media_path(slot['active']), folder / reference)
            requested.append({'key': slot['key'], 'subject': slot['subject'],
                              'destination': f"images/{slot['key']}.png", 'edit_target': reference})
        reference_names = []
        if project['id'] == 'realify':
            shutil.copy2(ROOT / 'docs/CHANNEL.md', folder / 'CHANNEL.md')
            for name in ['doflamingo.jpg', 'kaido.jpg', 'crocodile.jpg', 'bigmom.jpg', 'ace.jpg']:
                shutil.copy2(ROOT / 'web/assets' / name, refs / name)
                reference_names.append('references/' + name)
        else:
            (folder / 'CHANNEL.md').write_text(f"# {project['name']}\nUniverse: {project['universe']}\nArt direction: {project['direction']}\nNo One Piece assumptions apply to this project.\n", encoding='utf-8')
        for item in project.get('reference_files', []):
            name = Path(item).name
            shutil.copy2(self.store.media_path(item), refs / name)
            reference_names.append('references/' + name)
        skilldir = folder / '.agents/skills/studio-producer'
        skilldir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / '.agents/skills/studio-producer/SKILL.md', skilldir / 'SKILL.md')
        brief = {'project': {k: project[k] for k in ['name', 'universe', 'direction']}, 'concept': pack['concept'],
                 'notes': pack['notes'], 'ratio': pack['ratio'], 'requested_slots': requested,
                 'correction': job['correction'], 'style_reference_images': reference_names,
                 'continuity_images': continuity,
                 'recent_posts': [{'title': p['title'], 'feedback': p['feedback'][-5:]} for p in self.store.packs(project['id'])[:8]],
                 'metadata_destination': 'post.json',
                 'constraint': 'Existing Codex subscription only. Native image tool only. No paid API or fallback.'}
        (folder / 'brief.json').write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding='utf-8')

    @staticmethod
    def codex(job, folder):
        executable = shutil.which(os.environ.get('STUDIO_CODEX_BIN', 'codex'))
        if not executable:
            raise RuntimeError('Codex CLI introuvable sur la machine qui génère les images.')
        env = {k: v for k, v in os.environ.items() if k not in ['OPENAI_API_KEY', 'CODEX_API_KEY']}
        auth = subprocess.run([executable, 'login', 'status'], env=env, capture_output=True, text=True, timeout=20)
        if auth.returncode or 'ChatGPT' not in auth.stdout + auth.stderr:
            raise RuntimeError('Connecter Codex avec l’abonnement ChatGPT sur cette machine (codex login). Aucune API payante utilisée.')
        prompt = ('Use $studio-producer to complete brief.json. Read CHANNEL.md and inspect the provided relevant reference images. '
                  'Act as the creative director: choose a coherent fresh angle and scenes, informed by recent posts and feedback. '
                  'Generate each requested image with the native image generation tool and the installed imagegen skill. '
                  'Respect the exact requested aspect ratio. Copy the native output into each requested destination. '
                  'For corrections edit only the requested slot using its edit_target. Preserve all other images. '
                  'Do not use any image API or API key, browser automation, or substitute drawings. '
                  'Do not spawn agents. Do not access unrelated files or services. '
                  'If the native tool is unavailable or quota is exhausted, stop and state the actual blocker. '
                  'Inspect the outputs before your final factual summary. No additional images beyond requested_slots.')
        args = [executable, 'exec', '--sandbox', 'workspace-write', '-c', 'approval_policy="never"',
                '--disable', 'multi_agent', '--enable', 'image_generation', '--skip-git-repo-check',
                '--json', '-C', str(folder), '-o', str(folder / 'result.txt'), '-']
        with (folder / 'events.jsonl').open('w') as out, (folder / 'stderr.log').open('w') as err:
            proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=out, stderr=err, env=env, start_new_session=True)
            try:
                proc.communicate(prompt.encode(), timeout=int(os.environ.get('STUDIO_JOB_TIMEOUT', '1500')))
            except subprocess.TimeoutExpired:
                import signal
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                raise RuntimeError('Délai de génération dépassé. Les images déjà reçues sont conservées.')
            if proc.returncode:
                raise RuntimeError('Codex a arrêté la génération. Consulter le journal local du travail ; aucune API de secours utilisée.')
