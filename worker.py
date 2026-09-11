"""Native Codex worker: manifests, process lifecycle and immutable artifact import."""
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from PIL import Image
from domain import ROOT, uid, validate_post

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
            if not db.in_transaction:
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
        return self.finalize(job, pack, folder, error)

    def finalize(self, job, pack, folder, error=None):
        """Validate and import finished native artifacts, including crash recovery."""
        if not job['correction']:
            try:
                post = validate_post(json.loads((folder / 'post.json').read_text()))
                with self.store.db() as db:
                    if not db.in_transaction:
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
            if key in job.get('completed_slots', []):
                continue
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
                    if not db.in_transaction:
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
        complete = len(job['completed_slots']) == len(job['slots']) and (bool(job['correction']) or bool(self.store.pack(pack['id']).get('post')))
        job['message'] = 'Images disponibles' if complete else ('Génération incomplète. ' + (error or 'Codex n’a pas produit tous les fichiers attendus. Vérifier sa connexion et la disponibilité de la génération d’images.'))
        with self.store.db() as db:
            if not db.in_transaction:
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
        if pack.get('story_context', {}).get('previous'):
            previous_pack = self.store.pack(pack['story_context']['previous'][-1]['pack_id'])
            for slot in [previous_pack['slots'][0], previous_pack['slots'][-1]]:
                if slot['active']:
                    filename = f"references/previous-episode-{slot['key']}.png"
                    shutil.copy2(self.store.media_path(slot['active']), folder / filename)
                    continuity.append({'key': slot['key'], 'subject': slot['subject'], 'file': filename, 'role': 'previous episode identity and narrative state'})
        reference_names = []
        if project['id'] == 'realify':
            shutil.copy2(ROOT / 'docs/CHANNEL.md', folder / 'CHANNEL.md')
            cast = ' '.join(pack['concept'].get('subjects', [])).casefold()
            archive_subjects = {'doflamingo.jpg': 'doflamingo', 'kaido.jpg': 'kaido', 'crocodile.jpg': 'crocodile', 'bigmom.jpg': 'big mom', 'ace.jpg': 'portgas'}
            selected = [name for name, subject in archive_subjects.items() if subject in cast]
            # User project references and episode frames take precedence over unrelated archive imagery.
            if not selected and not project.get('reference_files') and not continuity:
                selected = ['doflamingo.jpg']
            for name in selected:
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
                 'story_context': pack.get('story_context'), 'notes': pack['notes'], 'ratio': pack['ratio'], 'requested_slots': requested,
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
