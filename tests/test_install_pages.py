"""Pages serves exact verified release entry bytes, never branch snapshots."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class InstallPages(unittest.TestCase):
    def builder(self):
        path=ROOT/'scripts/ci/build_install_pages.py'
        self.assertTrue(path.is_file(),'Verified Pages builder is not implemented')
        spec=importlib.util.spec_from_file_location('install_pages',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_pages_preserves_verified_script_bytes_and_refuses_corrupt_assets(self):
        builder=self.builder()
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();assets=root/'release';assets.mkdir()
            scripts={'install.sh':b'#!/bin/sh\n# reviewed\n','install.ps1':b'# reviewed\r\nWrite-Output "ok"\r\n'}
            for name,raw in scripts.items():(assets/name).write_bytes(raw)
            (assets/'SHA256SUMS').write_text(''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,raw in scripts.items()))
            builder.build('7.1.0',assets,root/'site')
            self.assertEqual(scripts['install.sh'],(root/'site/install.sh').read_bytes())
            self.assertEqual(scripts['install.ps1'],(root/'site/install.ps1.txt').read_bytes())
            self.assertTrue((root/'site/provenance.json').is_file())
            (assets/'install.sh').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'integrity|checksum'):builder.build('7.1.0',assets,root/'bad')
            self.assertFalse((root/'bad').exists())

    def test_pages_rejects_legacy_installers_before_reading_assets(self):
        builder=self.builder()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve()
            try:
                with self.assertRaisesRegex(ValueError,'7.1.0|legacy|unified'):
                    builder.build('7.0.1',base/'missing-assets',base/'site')
            except FileNotFoundError:self.fail('Legacy installer was not rejected before asset reads')
            self.assertFalse((base/'site').exists())
