"""Agent-facing commands shared by HTTP and CLI; atomic creation and request replay."""
import hashlib
import json
import time
from domain import uid, text


class StoryService:
    def __init__(self, store):
        self.store = store

    def stories(self, project_id=None):
        with self.store.db() as db:
            rows = db.execute('SELECT data FROM stories WHERE project_id=?', (project_id,)) if project_id else db.execute('SELECT data FROM stories')
            return sorted([json.loads(r['data']) for r in rows], key=lambda s: s['created'], reverse=True)

    def story(self, sid, db=None):
        if db is None:
            with self.store.db() as connection:
                return self.story(sid, connection)
        row = db.execute('SELECT data FROM stories WHERE id=?', (sid,)).fetchone()
        if not row:
            raise ValueError('Série introuvable.')
        return json.loads(row['data'])

    def execute(self, action, data, request_id=None):
        action = text(action, 80)
        if not isinstance(data, dict):
            raise ValueError('Objet JSON requis.')
        fingerprint = hashlib.sha256(json.dumps([action, data], sort_keys=True).encode()).hexdigest()
        if request_id is not None:
            request_id = text(request_id, 120)
        with self.store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if request_id:
                old = db.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
                if old:
                    if old['fingerprint'] != fingerprint:
                        raise ValueError('Cet identifiant de requête correspond à une autre demande.')
                    return json.loads(old['result'])
            operations = {
                'pack.correct': lambda: self.store.correct(data.get('pack_id'), data),
                'pack.restore': lambda: self.store.restore(data.get('pack_id'), data),
                'pack.metadata': lambda: self.store.metadata(data.get('pack_id'), data),
                'pack.feedback': lambda: self.store.feedback(data.get('pack_id'), data),
                'feedback.resolve': lambda: self.store.resolve_feedback(data.get('pack_id'), data),
                'job.retry': lambda: self.store.retry(data.get('job_id')),
            }
            if action in operations:
                result = operations[action]()
            elif action == 'pack.create':
                result = self.store.create_pack(data, db=db)
            elif action == 'story.create':
                result = self._create(db, data)
            elif action == 'story.update':
                result = self._update(db, data)
            elif action == 'story.attach':
                result = self._attach(db, data)
            elif action == 'story.next':
                result = self._next(db, data)
            else:
                raise ValueError('Action inconnue.')
            if request_id:
                db.execute('INSERT INTO requests VALUES (?, ?, ?)', (request_id, fingerprint, json.dumps(result)))
            return result

    def _build(self, data):
        project = self.store.project(data.get('project_id'))
        if not project:
            raise ValueError('Projet introuvable.')
        premise = text(data.get('premise'), 2000)
        outline = data.get('outline') if data.get('outline') is not None else [
            {'title': 'La découverte', 'beat': 'Faire surgir un problème concret et une première piste.', 'ending': 'Une décision engage les personnages dans la suite.'},
            {'title': 'Le prix à payer', 'beat': 'Suivre la décision précédente et affronter une conséquence inattendue.', 'ending': 'Résoudre un obstacle et révéler la dernière question.'},
            {'title': 'La réponse', 'beat': 'Confronter les personnages au choix final établi dans les épisodes précédents.', 'ending': 'Offrir une conclusion visible à la promesse de départ.'},
        ]
        if not isinstance(outline, list) or not 2 <= len(outline) <= 12:
            raise ValueError('Prévoir de 2 à 12 épisodes.')
        clean = []
        for episode in outline:
            if not isinstance(episode, dict):
                raise ValueError('Chaque épisode doit décrire titre, action et fin.')
            clean.append({k: text(episode.get(k), limit) for k, limit in [('title', 120), ('beat', 1500), ('ending', 1000)]})
        cast = data.get('subjects', project['subjects'])
        if not isinstance(cast, list) or not 1 <= len(cast) <= 20:
            raise ValueError('Choisir de 1 à 20 personnages.')
        story = {'id': uid(), 'project_id': project['id'], 'title': text(data.get('title'), 120),
                 'premise': premise, 'continuity': text(data.get('continuity', ''), 3000, False),
                 'subjects': [text(s, 100) for s in cast], 'outline': clean, 'episodes': [], 'created': time.time()}
        return story

    def _create(self, db, data):
        story = self._build(data)
        db.execute('INSERT INTO stories VALUES (?, ?, ?)', (story['id'], story['project_id'], json.dumps(story)))
        return story

    def _next(self, db, data):
        story = self.story(data.get('story_id'), db)
        number = len(story['episodes']) + 1
        if number > len(story['outline']):
            raise ValueError('Cette série est terminée.')
        previous = []
        for pid in story['episodes']:
            row = db.execute('SELECT data FROM packs WHERE id=?', (pid,)).fetchone()
            if not row:
                raise ValueError('Un épisode précédent manque.')
            pack = json.loads(row['data'])
            if pack['status'] != 'ready' or db.execute("SELECT 1 FROM jobs WHERE pack_id=? AND state IN ('queued','running')", (pid,)).fetchone():
                raise ValueError('Terminer ou reprendre l’épisode précédent avant de créer sa suite.')
            previous.append(pack)
        plan = story['outline'][number-1]
        pack = self.store.create_pack({'project_id': story['project_id'], 'subjects': story['subjects'],
                                      'notes': text(data.get('notes', ''), 2000, False)}, db=db)
        pack['title'] = f"{story['title']} · {number:02} — {plan['title']}"
        pack['story_id'] = story['id']
        pack['episode_number'] = number
        pack['concept'] = {'id': 'story', 'title': pack['title'], 'family': 'Série narrative',
                           'subjects': story['subjects'], 'scene': story['premise'], 'episode': plan}
        pack['story_context'] = {'title': story['title'], 'premise': story['premise'],
                                 'continuity': story['continuity'], 'outline': story['outline'],
                                 'number': number, 'total': len(story['outline']),
                                 'previous': [{'pack_id': p['id'], 'title': p['title'], 'post': p['post'], 'feedback': p['feedback'][-5:]} for p in previous]}
        self.store.save_pack(db, pack)
        story['episodes'].append(pack['id'])
        db.execute('UPDATE stories SET data=? WHERE id=?', (json.dumps(story), story['id']))
        return pack

    def _attach(self, db, data):
        story = self.story(data.get('story_id'), db)
        if story['episodes']:
            raise ValueError('Le rattachement concerne uniquement le premier épisode d’une série vide.')
        pack = self.store.pack(data.get('pack_id'))
        if pack['project_id'] != story['project_id'] or pack.get('story_id') or pack['status'] != 'ready':
            raise ValueError('Choisir un post complet du même projet, sans série existante.')
        if db.execute("SELECT 1 FROM jobs WHERE pack_id=? AND state IN ('queued','running')", (pack['id'],)).fetchone():
            raise ValueError('Attendre la fin de la retouche.')
        pack['story_id'] = story['id']
        pack['episode_number'] = 1
        self.store.save_pack(db, pack)
        story['episodes'] = [pack['id']]
        db.execute('UPDATE stories SET data=? WHERE id=?', (json.dumps(story), story['id']))
        return pack

    def _update(self, db, data):
        story = self.story(data.get('story_id'), db)
        fields = ['title', 'premise', 'subjects', 'continuity', 'outline']
        revised = self._build({**story, **{key:data[key] for key in fields if key in data}})
        count = len(story['episodes'])
        if revised['outline'][:count] != story['outline'][:count]:
            raise ValueError('Conserver le plan des épisodes déjà créés ; modifier uniquement la suite.')
        story.update({key:revised[key] for key in fields})
        db.execute('UPDATE stories SET data=? WHERE id=?', (json.dumps(story), story['id']))
        return story
