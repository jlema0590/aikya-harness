"""Git checkout conversion must not change shipped resource bytes or signatures."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('git'), 'Git is required for checkout acceptance')
class AssetLineEndingTests(unittest.TestCase):
    def test_windows_style_checkout_preserves_pinned_resource_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)

            def git(*arguments):
                result = subprocess.run(['git', *arguments], cwd=root, capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)

            git('init', '-q')
            git('config', 'core.autocrlf', 'false')
            attributes = ROOT / '.gitattributes'
            if attributes.is_file():
                shutil.copyfile(attributes, root / '.gitattributes')
            payload = b'Pinned asset\nUTF-8: caf\xc3\xa9\n'
            paths = [root / 'src/aikya/resources' / name for name in (
                'aikya-template/docs/foundation.md', 'migrations/documentation-hashes.json',
                'memory-viewer/viewer.js')]
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            git('add', '.')
            for path in paths:
                path.unlink()
            git('config', 'core.autocrlf', 'true')
            git('config', 'core.eol', 'crlf')
            git('checkout-index', '--all', '--force')
            for path in paths:
                self.assertEqual(payload, path.read_bytes(), path.relative_to(root).as_posix())


if __name__ == '__main__':
    unittest.main()
