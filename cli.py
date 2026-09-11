"""Local agent adapter: JSON in/out, shared Store, no worker or model subprocess."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from studio import ROOT, Store


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', default=os.environ.get('STUDIO_RUNTIME', str(ROOT / 'runtime')))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('projects')
    commands.add_parser('jobs')
    generate = commands.add_parser('generate')
    generate.add_argument('--project', required=True)
    generate.add_argument('--count', type=int, default=5)
    generate.add_argument('--subject', action='append')
    generate.add_argument('--notes-file', type=Path)
    generate.add_argument('--concept', default='auto')
    for name in ['status', 'export']:
        command = commands.add_parser(name)
        command.add_argument('pack_id')
        if name == 'export':
            command.add_argument('--output', type=Path, required=True)
    correct = commands.add_parser('correct')
    correct.add_argument('pack_id')
    correct.add_argument('--slot', required=True)
    correct.add_argument('--instruction-file', type=Path, required=True)
    retry = commands.add_parser('retry')
    retry.add_argument('job_id')
    args = parser.parse_args(argv)
    try:
        store = Store(args.runtime)
        if args.command == 'projects':
            result = store.projects()
        elif args.command == 'jobs':
            result = store.jobs()
        elif args.command == 'generate':
            data = {'project_id': args.project, 'count': args.count, 'concept_id': args.concept,
                    'notes': args.notes_file.read_text() if args.notes_file else ''}
            if args.subject:
                data['subjects'] = args.subject
            pack = store.create_pack(data)
            result = {'pack': pack, 'jobs': [j for j in store.jobs() if j['pack_id'] == pack['id']]}
        elif args.command == 'status':
            result = {'pack': store.pack(args.pack_id), 'jobs': [j for j in store.jobs() if j['pack_id'] == args.pack_id]}
        elif args.command == 'correct':
            result = store.correct(args.pack_id, {'slot': args.slot, 'instruction': args.instruction_file.read_text()})
        elif args.command == 'retry':
            result = store.retry(args.job_id)
        else:
            pack = store.pack(args.pack_id)
            if not pack.get('post') or not all(s['active'] for s in pack['slots']):
                raise ValueError('Pack incomplet : export indisponible.')
            # A fresh directory prevents accidental overwrites of another export.
            args.output.mkdir(parents=True, exist_ok=False)
            files = []
            for i, slot in enumerate(pack['slots'], 1):
                dest = args.output / f'{i:02}-{slot["key"]}.png'
                shutil.copy2(store.media_path(slot['active']), dest)
                files.append(str(dest.resolve()))
            (args.output / 'post.json').write_text(json.dumps(pack['post'], ensure_ascii=False, indent=2))
            result = {'pack_id': pack['id'], 'files': files, 'post': str((args.output / 'post.json').resolve())}
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
