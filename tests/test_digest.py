import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('digest', Path(__file__).resolve().parents[1] / 'scripts' / 'digest.py')
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)

class TestDigest(unittest.TestCase):
    def test_render_escapes_untrusted_data(self):
        repo = {'name':'org/test','url':'https://github.com/org/test', 'description':'<script>alert(1)</script>',
                'category':'QA','stars':9,'language':'Python','license':'MIT','last_push':'2026-10-17T00:00:00Z'}
        item = {'name':'org/test','why':'<b>x</b>','use_case':'test','business':'none','risk':'none','difficulty':'easy'}
        report = {'intro':'hello', 'items':[item], 'top_three':[{'name':'org/test','first_step':'begin'}]}
        subj, plain, rich = digest.render(report, {'org/test':repo}, [])
        self.assertIn('&lt;script&gt;', rich)
        self.assertNotIn('<script>', rich)
        self.assertIn('https://github.com/org/test', plain)

if __name__ == '__main__':
    unittest.main()
