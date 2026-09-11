import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from cli import main
from studio import Store, Worker
from test_studio import fake_provider


class AgentContractTests(unittest.TestCase):
    def test_agent_single_batch_correction_export(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(temp)
            def call(*args):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = main(['--runtime', temp, *args])
                return code, json.loads(out.getvalue())
            code, response = call('generate', '--project', 'realify', '--count', '1', '--subject', 'Nami')
            self.assertEqual(code, 0)
            pack = response['result']['pack']
            self.assertEqual(len(pack['slots']), 1)
            self.assertEqual(pack['slots'][0]['subject'], 'Nami')
            self.assertEqual(store.jobs()[0]['state'], 'queued')
            Worker(store, fake_provider).run_one()
            out = Path(temp) / 'export'
            code, response = call('export', pack['id'], '--output', str(out))
            self.assertEqual(code, 0)
            self.assertEqual(len(response['result']['files']), 1)
            self.assertTrue(Path(response['result']['files'][0]).is_file())
            self.assertEqual(call('export', pack['id'], '--output', str(out))[0], 1)
            instruction = Path(temp) / 'edit.txt'
            instruction.write_text('Lumière naturelle latérale.')
            code, response = call('correct', pack['id'], '--slot', 'cover', '--instruction-file', str(instruction))
            self.assertEqual(code, 0)
            Worker(store, fake_provider).run_one()
            brief = json.loads((Path(temp) / 'jobs' / response['result']['id'] / 'brief.json').read_text())
            self.assertEqual(len(brief['continuity_images']), 1)
            self.assertEqual(len(store.pack(pack['id'])['slots'][0]['versions']), 2)
            code, response = call('generate', '--project', 'realify', '--count', '3')
            self.assertEqual(code, 0)
            self.assertEqual(len(response['result']['pack']['slots']), 3)
            jobs = len(store.jobs())
            self.assertEqual(call('generate', '--project', 'realify', '--count', '0')[0], 1)
            self.assertEqual(len(store.jobs()), jobs)
