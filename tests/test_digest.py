import importlib.util
from pathlib import Path
from unittest.mock import patch, Mock
import unittest

spec = importlib.util.spec_from_file_location('digest', Path(__file__).resolve().parents[1] / 'scripts' / 'digest.py')
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)


def sample_repos(count=16):
    cats = list(digest.CATEGORIES)
    return [{'name': f'org/repo-{i}', 'url': f'https://github.com/org/repo-{i}',
             'description': '<script>alert(1)</script>' if i == 0 else 'demo',
             'category': cats[i % 4], 'stars': i, 'language': 'Python',
             'license': 'MIT', 'last_push': '2026-10-22T00:00:00Z'} for i in range(count)]


class TestDigest(unittest.TestCase):
    def test_fallback_is_balanced_and_valid(self):
        repos = sample_repos()
        report = digest.fallback_report(repos)
        digest.validate_report(report, repos)
        self.assertEqual(len(report['items']), 12)
        self.assertEqual({r['category'] for r in repos if r['name'] in
                          {i['name'] for i in report['items']}}, set(digest.CATEGORIES))

    def test_render_escapes_untrusted_data(self):
        repos = sample_repos()
        report = digest.fallback_report(repos)
        _, plain, rich = digest.render(report, {r['name']: r for r in repos}, [], 'python')
        self.assertIn('&lt;script&gt;', rich)
        self.assertNotIn('<script>', rich)
        self.assertIn('https://github.com/org/repo-0', plain)

    def test_gemini_error_triggers_fallback(self):
        repos = sample_repos()
        with patch.object(digest, 'choose_gemini', side_effect=RuntimeError('429')):
            report, engine = digest.generate_report(repos, 'fake-key')
        self.assertEqual(engine, 'python')
        self.assertEqual(len(report['items']), 12)

    def test_valid_gemini_response_is_used(self):
        repos = sample_repos()
        report = digest.fallback_report(repos)
        with patch.object(digest, 'choose_gemini', return_value=report):
            actual, engine = digest.generate_report(repos, 'fake-key')
        self.assertEqual(engine, 'gemini')
        self.assertEqual(actual, report)

    def test_invalid_repositories_are_rejected(self):
        repos = sample_repos()
        report = digest.fallback_report(repos)
        report['items'][0]['name'] = 'unknown/repo'
        with self.assertRaises(ValueError):
            digest.validate_report(report, repos)

    def test_missing_key_uses_fallback(self):
        report, engine = digest.generate_report(sample_repos(), '')
        self.assertEqual(engine, 'python')
        self.assertEqual(len(report['top_three']), 3)


    def test_gmail_send_confirms_message_id(self):
        env = {'GMAIL_CLIENT_ID': 'id', 'GMAIL_CLIENT_SECRET': 'secret',
               'GMAIL_REFRESH_TOKEN': 'refresh', 'EMAIL_FROM': 'from@example.com',
               'EMAIL_TO': 'to@example.com'}
        token = Mock(ok=True)
        token.json.return_value = {'access_token': 'access'}
        with patch.dict(digest.os.environ, env), \
             patch.object(digest.requests, 'post', return_value=token), \
             patch.object(digest, 'request_json', return_value={'id': 'msg-1'}) as send:
            result = digest.send_gmail('Subject', 'Plain', '<b>HTML</b>')
        self.assertEqual(result, 'msg-1')
        self.assertIn('raw', send.call_args.kwargs['data'])

    def test_gmail_missing_configuration_fails_closed(self):
        with patch.dict(digest.os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'Missing Gmail environment variable'):
                digest.send_gmail('Subject', 'Plain', '<b>HTML</b>')

    def test_gmail_unconfirmed_send_is_error(self):
        env = {'GMAIL_CLIENT_ID': 'id', 'GMAIL_CLIENT_SECRET': 'secret',
               'GMAIL_REFRESH_TOKEN': 'refresh', 'EMAIL_FROM': 'from@example.com',
               'EMAIL_TO': 'to@example.com'}
        token = Mock(ok=True)
        token.json.return_value = {'access_token': 'access'}
        with patch.dict(digest.os.environ, env), \
             patch.object(digest.requests, 'post', return_value=token), \
             patch.object(digest, 'request_json', return_value={}):
            with self.assertRaisesRegex(RuntimeError, 'unconfirmed'):
                digest.send_gmail('Subject', 'Plain', '<b>HTML</b>')


if __name__ == '__main__':
    unittest.main()
