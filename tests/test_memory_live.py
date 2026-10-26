"""Explicit loopback serving exposes only the current owned memory projection."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch


class MemoryLiveTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('aikya.memory.viewer.live'), 'Local live viewer is missing')
        from aikya.code_index.policy import configure
        from aikya.memory.viewer.export import export_view
        from aikya.memory.viewer.live import serve_live
        self.export = export_view
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve();configure(self.root, approved=True)
        (self.root / 'entity.py').write_text('class Entity: pass\n')
        self.export(self.root, refresh=True)
        self.stop = threading.Event()
        self.server = serve_live(self.root, stop_event=self.stop)
        self.addCleanup(self.server.close)

    def get(self, suffix='', **headers):
        return urlopen(Request(self.server.url + suffix, headers=headers), timeout=5)

    def test_authorized_snapshot_uses_latest_complete_publication(self):
        with self.get() as response:
            html = response.read().decode()
            self.assertIn("connect-src 'self'", html)
            self.assertEqual('no-store', response.headers['Cache-Control'])
        with self.get('snapshot') as response:
            first = json.load(response)
        self.assertIn('Entity', {n['label'] for n in first['snapshot']['nodes']})
        (self.root / 'entity.py').write_text('class Changed: pass\n')
        self.export(self.root, refresh=True)
        with self.get('snapshot') as response:
            second = json.load(response)
        self.assertNotEqual(first['generation'], second['generation'])
        self.assertIn('Changed', {n['label'] for n in second['snapshot']['nodes']})

    def test_loopback_startup_does_not_require_hostname_resolution(self):
        from aikya.memory.viewer.live import serve_live
        # Reverse DNS can block on offline hosts and macOS CI. The explicit
        # numeric loopback endpoint must stay usable when lookup is unavailable.
        with patch('socket.getfqdn', side_effect=AssertionError('Unexpected DNS lookup')):
            server = serve_live(self.root, stop_event=self.stop)
        self.addCleanup(server.close)
        with urlopen(server.url, timeout=5) as response:
            self.assertEqual(200, response.status)

    def test_no_arbitrary_paths_foreign_host_origin_or_missing_capability(self):
        for suffix, headers in [('snapshot', {'Host': 'evil.example'}), ('snapshot', {'Origin': 'https://evil.example'}), ('../outside', {})]:
            with self.subTest(suffix=suffix, headers=headers), self.assertRaises(HTTPError) as raised:
                self.get(suffix, **headers)
            self.assertIn(raised.exception.code, (403, 404))
        from urllib.parse import urlsplit
        origin = urlsplit(self.server.url)
        with self.assertRaises(HTTPError):
            urlopen('http://' + origin.netloc + '/snapshot', timeout=5)

    def test_custom_html_or_torn_report_is_not_served_as_current(self):
        (self.root / 'aikya/docs/memory/view/report.md').write_text('Team report\n')
        with self.assertRaises(HTTPError) as raised:
            self.get('snapshot')
        self.assertEqual(503, raised.exception.code)


if __name__ == '__main__':
    unittest.main()
