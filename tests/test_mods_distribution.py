"""A verified release must never escape its source or execute an installer."""
import hashlib
import importlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch


def release(base, version='0.0.10', extra=None, plugin_version='0.1.0'):
    files = {'VERSION': version + '\n'}
    plugins=[]
    for name in ('aikya-boxbot','aikya-flow','aikya-usage'):
        plugins.append({'name':name,'source':'./mods/'+name,'version':plugin_version})
        files['mods/'+name+'/.claude-plugin/plugin.json']=json.dumps({'name':name,'version':plugin_version})
        files['mods/'+name+'/hooks/register.js']='// fixture, never executed\n'
    files['.claude-plugin/marketplace.json']=json.dumps({'name':'aikya-mods','owner':{'name':'Aikya'},'plugins':plugins})
    files.update(extra or {})
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as archive:
        for name,content in files.items():archive.writestr('aikya-mods/'+name,content)
    name='aikya-mods-v'+version+'.zip'
    assets={name:raw.getvalue(),'release.json':json.dumps({'version':'v'+version,'claude_version':'2.1.308','mods':{p['name']:p['version'] for p in plugins}}).encode()}
    assets['SHA256SUMS']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in assets.items()).encode()
    base.mkdir(parents=True,exist_ok=True)
    for name,data in assets.items():(base/name).write_bytes(data)
    return assets


class ModsDistribution(unittest.TestCase):
    def module(self):
        try:return importlib.import_module('aikya.installation.bootstrap.mods')
        except ModuleNotFoundError:self.fail('Verified Mods distribution is not implemented')

    def test_verified_bundle_is_persistent_and_modified_source_is_preserved(self):
        mods=self.module()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve();release(base/'assets')
            bundle=mods.prepare_mods('0.0.10',base/'sources',base/'assets')
            self.assertEqual('0.0.10',bundle.version)
            self.assertEqual({'aikya-boxbot','aikya-flow','aikya-usage'},set(bundle.plugins))
            self.assertTrue((bundle.path/'.claude-plugin/marketplace.json').is_file())
            self.assertEqual(bundle.path,mods.prepare_mods('0.0.10',base/'sources',base/'assets').path)
            source=bundle.path/'mods/aikya-flow/hooks/register.js';source.write_text('custom')
            with self.assertRaisesRegex(ValueError,'modified|Customized'):
                mods.prepare_mods('0.0.10',base/'sources',base/'assets')
            self.assertEqual('custom',source.read_text())

    def test_corrupt_assets_do_not_create_destination(self):
        mods=self.module()
        for filename in ('release.json','aikya-mods-v0.0.10.zip'):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as t:
                base=Path(t).resolve();release(base/'assets');(base/'assets'/filename).write_bytes(b'corrupt')
                with self.assertRaisesRegex(ValueError,'checksum|integrity'):mods.prepare_mods('0.0.10',base/'out',base/'assets')
                self.assertFalse((base/'out').exists())

    def test_unsafe_archives_and_catalogs_do_not_write_any_source(self):
        mods=self.module()
        bad=[{'mods/caf\u00e9':'one','mods/cafe\u0301':'two'}, {'../../escape':'unsafe'},{'mods/CASE':'a','mods/case':'b'},{'NUL.txt':'bad'},
             {'.claude-plugin/marketplace.json':json.dumps({'name':'aikya-mods','plugins':[{'name':'aikya-flow','source':'https://evil.invalid/code.zip','version':'0.1.0'}]})},
             {'mods/aikya-flow/.claude-plugin/plugin.json':'{"name":"wrong","version":"0.1.0"}'}, {'VERSION':'0.9.0'}]
        for extra in bad:
            with self.subTest(extra=extra),tempfile.TemporaryDirectory() as t:
                base=Path(t).resolve();release(base/'assets',extra=extra)
                with self.assertRaises(ValueError):mods.prepare_mods('0.0.10',base/'out',base/'assets')
                self.assertFalse((base/'out').exists())

    def test_missing_marketplace_owner_is_rejected_before_creating_a_source(self):
        mods=self.module()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve();assets=release(base/'assets')
            with zipfile.ZipFile(io.BytesIO(assets['aikya-mods-v0.0.10.zip'])) as archive:
                market=json.loads(archive.read('aikya-mods/.claude-plugin/marketplace.json'))
            market.pop('owner')
            release(base/'assets',extra={'.claude-plugin/marketplace.json':json.dumps(market)})
            with self.assertRaisesRegex(ValueError,'owner|marketplace'):
                mods.prepare_mods('0.0.10',base/'out',base/'assets')
            self.assertFalse((base/'out').exists())

    def test_latest_is_resolved_from_mods_repository_only(self):
        mods=self.module(); requests=[]
        payload=json.dumps({'tag_name':'v0.0.10','draft':False,'prerelease':False,'published_at':'2026-10-26'}).encode()
        def fetch(url,limit):requests.append(url);return payload
        with patch.object(mods.download,'https_bytes',side_effect=fetch):
            self.assertEqual('0.0.10',mods.resolve_version(None))
        self.assertEqual(['https://api.github.com/repos/jlema0590/aikya-mods/releases/latest'],requests)

    def test_prepared_source_cannot_be_replaced_by_forging_its_disk_marker(self):
        mods=self.module()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve();release(base/'assets');bundle=mods.prepare_mods('0.0.10',base/'stage',base/'assets')
            path=bundle.path/'mods/aikya-flow/hooks/register.js';path.write_bytes(b'changed executable content')
            marker=bundle.path.parent/'aikya-source.json';record=json.loads(marker.read_text())
            record['files']['mods/aikya-flow/hooks/register.js']=hashlib.sha256(path.read_bytes()).hexdigest()
            marker.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'modified|integrity'):
                mods.persist_bundle(bundle,base/'persistent')
            self.assertFalse((base/'persistent').exists())

    def test_duplicate_symlink_truncated_and_expanding_zip_are_rejected(self):
        import stat
        import warnings
        mods=self.module()
        for kind in ('duplicate','symlink','truncated','expanding'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as t:
                base=Path(t).resolve();assets=release(base/'assets');name='aikya-mods-v0.0.10.zip'
                raw=io.BytesIO(assets[name])
                if kind=='truncated':data=b'PK invalid truncated ZIP'
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore',UserWarning)
                        with zipfile.ZipFile(raw,'a',compression=zipfile.ZIP_DEFLATED) as archive:
                            if kind=='duplicate':archive.writestr('aikya-mods/VERSION','0.0.10')
                            elif kind=='symlink':
                                info=zipfile.ZipInfo('aikya-mods/link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
                                archive.writestr(info,'../escape')
                            else:archive.writestr('aikya-mods/bomb',b'x'*65537)
                    data=raw.getvalue()
                (base/'assets'/name).write_bytes(data)
                (base/'assets/SHA256SUMS').write_text(hashlib.sha256(data).hexdigest()+'  '+name+'\n'+hashlib.sha256(assets['release.json']).hexdigest()+'  release.json\n')
                with patch.object(mods.download,'LIMIT',65536),self.assertRaises(ValueError):
                    mods.prepare_mods('0.0.10',base/'out',base/'assets')
                self.assertFalse((base/'out').exists())
