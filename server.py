"""Single-user HTTP API and built React assets. Run behind HTTPS for remote access."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import mimetypes
import os
import secrets
import threading
import time
import zipfile
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from PIL import Image
from studio import ROOT, CONCEPTS, Store, Worker, uid


def make_server(store, host='127.0.0.1', port=8787):
    attempts = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # no query strings, tokens, private captions in access logs

        def send(self, status, body, mime='application/json; charset=utf-8', extra=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; font-src 'self'; frame-ancestors 'none'")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def session(self):
            try:
                cookie = SimpleCookie(self.headers.get('Cookie', ''))
                token = cookie.get('studio_session')
                return token is not None and store.authorized(token.value)
            except Exception:
                return False

        def read_body(self):
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 12 * 1024 * 1024:
                raise ValueError('Requête vide ou trop volumineuse.')
            if 'application/json' not in self.headers.get('Content-Type', ''):
                raise ValueError('Format JSON requis.')
            result = json.loads(self.rfile.read(length))
            if not isinstance(result, dict):
                raise ValueError('Objet JSON requis.')
            return result

        def do_GET(self):
            try:
                self.get()
            except ValueError as exc:
                self.send(400, {'error': str(exc)})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self.send(500, {'error': 'Erreur interne. Consulter le terminal du serveur.'})

        def get(self):
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            if path == '/api/session':
                return self.send(200, {'authenticated': self.session()})
            if (path.startswith('/api/') or path.startswith('/media/')) and not self.session():
                return self.send(401, {'error': 'Connexion requise.'})
            if path == '/api/state':
                jobs = store.jobs()
                # Host process details and raw agent logs are deliberately not served.
                return self.send(200, {'projects': store.projects(), 'packs': store.packs(), 'jobs': jobs,
                                       'concepts': CONCEPTS,
                                       'limits': {'daily_images': int(os.environ.get('STUDIO_DAILY_IMAGES', '24'))}})
            if path == '/api/analytics':
                return self.send(200, (ROOT / 'data/analytics.json').read_bytes())
            if path.startswith('/media/'):
                image = store.media_path(path[len('/media/'):])
                extra = {'Content-Disposition': f'attachment; filename="{image.name}"'} if 'download' in parse_qs(parsed.query) else {}
                return self.send(200, image.read_bytes(), mimetypes.guess_type(image.name)[0] or 'application/octet-stream', extra)
            parts = path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api', 'packs'] and parts[3] == 'download':
                pack = store.pack(parts[2])
                selected = pack['slots']
                if any(not s['active'] for s in selected) or not pack.get('post'):
                    raise ValueError('Ce post n’est pas encore complet.')
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
                    for i, slot in enumerate(selected, 1):
                        z.write(store.media_path(slot['active']), f'{i:02}_{slot["key"]}.png')
                    z.writestr('caption.txt', pack['caption'])
                    z.writestr('post.json', json.dumps(pack['post'], ensure_ascii=False, indent=2))
                    z.writestr('manifest.json', json.dumps({'pack_id': pack['id'], 'title': pack['title'], 'exported_at': time.time(),
                                'images': [{'slot': s['key'], 'file': s['active'], 'subject': s['subject']} for s in selected]}, ensure_ascii=False, indent=2))
                return self.send(200, buffer.getvalue(), 'application/zip', {'Content-Disposition': f'attachment; filename="studio-{pack["id"][:8]}.zip"'})
            if path.startswith('/api/'):
                return self.send(404, {'error': 'Route introuvable.'})
            # Public shell has no analytics or private reference imagery baked into it.
            static = ROOT / 'dist'
            target = (static / path.lstrip('/')).resolve()
            if not target.is_relative_to(static.resolve()):
                return self.send(404, 'Not found', 'text/plain')
            if not target.is_file():
                if Path(path).suffix:
                    return self.send(404, 'Not found', 'text/plain')
                target = static / 'index.html'
            if not target.exists():
                return self.send(503, 'Construire l’interface avec npm run build.', 'text/plain; charset=utf-8')
            return self.send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')

        def do_POST(self):
            try:
                self.post()
            except (ValueError, KeyError, TypeError) as exc:
                self.send(400, {'error': str(exc)})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                self.send(500, {'error': 'Erreur interne. Vérifier le serveur.'})

        def post(self):
            origin = self.headers.get('Origin')
            if origin and urlparse(origin).netloc != self.headers.get('Host'):
                return self.send(403, {'error': 'Origine refusée.'})
            path = urlparse(self.path).path
            data = self.read_body()
            if path == '/api/login':
                address = self.client_address[0]
                now = time.time()
                attempts[address] = [t for t in attempts.get(address, []) if t > now - 60]
                if len(attempts[address]) >= 10:
                    return self.send(429, {'error': 'Trop de tentatives. Réessayer dans une minute.'})
                token = store.authenticate(data.get('code'))
                if not token:
                    attempts[address].append(now)
                    return self.send(401, {'error': 'Code d’accès incorrect.'})
                secure = '; Secure' if os.environ.get('STUDIO_SECURE_COOKIE') == '1' else ''
                return self.send(200, {'ok': True}, extra={'Set-Cookie': f'studio_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000{secure}'})
            if not self.session():
                return self.send(401, {'error': 'Connexion requise.'})
            if path == '/api/logout':
                cookie = SimpleCookie(self.headers.get('Cookie', ''))
                token = cookie['studio_session'].value
                with store.db() as db:
                    db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
                return self.send(200, {'ok': True}, extra={'Set-Cookie': 'studio_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
            if path == '/api/projects':
                return self.send(201, store.create_project(data))
            if path == '/api/packs':
                return self.send(201, store.create_pack(data))
            parts = path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api', 'packs']:
                operations = {'correct': store.correct, 'restore': store.restore, 'feedback': store.feedback,
                              'metadata': store.metadata, 'publish': store.publish}
                if parts[3] in operations:
                    return self.send(200, operations[parts[3]](parts[2], data))
            if len(parts) == 4 and parts[:2] == ['api', 'jobs'] and parts[3] == 'retry':
                return self.send(201, store.retry(parts[2]))
            if len(parts) == 4 and parts[:2] == ['api', 'projects'] and parts[3] == 'update':
                return self.send(200, store.update_project(parts[2], data))
            if len(parts) == 4 and parts[:2] == ['api', 'projects'] and parts[3] == 'reference':
                project = store.project(parts[2])
                if not project or len(project['reference_files']) >= 8:
                    raise ValueError('Projet introuvable ou maximum de 8 références atteint.')
                raw = base64.b64decode(data['image'], validate=True)
                with Image.open(io.BytesIO(raw)) as im:
                    im.verify()
                filename = f"references/{project['id']}-{uid()}.png"
                dest = store.runtime / 'media' / filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                with Image.open(io.BytesIO(raw)) as im:
                    im.thumbnail((1600, 1600))
                    im.convert('RGB').save(dest, format='PNG')
                project['reference_files'].append(filename)
                store.put_project(project)
                return self.send(201, project)
            if path == '/api/reference':
                allowed = ['doflamingo.jpg', 'kaido.jpg', 'crocodile.jpg', 'bigmom.jpg', 'ace.jpg']
                name = data.get('name')
                if name not in allowed:
                    raise ValueError('Référence introuvable.')
                return self.send(200, {'image': base64.b64encode((ROOT / 'web/assets' / name).read_bytes()).decode()})
            return self.send(404, {'error': 'Route introuvable.'})

    return ThreadingHTTPServer((host, port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--no-worker', action='store_true')
    args = parser.parse_args()
    store = Store(os.environ.get('STUDIO_RUNTIME', str(ROOT / 'runtime')))
    # One worker-owning process per SQLite volume; refuse a second launcher.
    import fcntl
    lock = (store.runtime / 'server.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    worker = Worker(store)
    worker.recover()
    if not args.no_worker:
        threading.Thread(target=worker.run, daemon=True).start()
    server = make_server(store, args.host, args.port)
    print(f'Studio: http://{args.host}:{args.port}\nCode d’accès local : {store.runtime / "access-code"}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        worker.stop.set()
        server.server_close()


if __name__ == '__main__':
    main()
