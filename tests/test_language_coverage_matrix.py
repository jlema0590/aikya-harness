import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from aikya.code_index.policy import CODE_SUFFIXES,configure
from aikya.code_index.parsers.registry import parse_file
from aikya.code_index.sync import sync
from aikya.code_index.store import IndexStore
from aikya.context.prepare import prepare_context

FIXTURES=Path(__file__).parent/'fixtures/language-coverage'

class LanguageCoverageTests(unittest.TestCase):
    def test_every_code_suffix_has_fixture_and_expected_capability(self):
        manifest=json.loads((FIXTURES/'manifest.json').read_text())
        self.assertEqual(set(manifest),set(CODE_SUFFIXES))
        for suffix,row in manifest.items():
            with self.subTest(suffix=suffix):
                raw=(FIXTURES/row['file']).read_bytes();value=parse_file(row['file'],raw)
                expected='indexed' if row['parser']=='python' or row['parser']!='inventory' and importlib.util.find_spec('tree_sitter_'+row['parser']) else 'file_only'
                self.assertEqual(value.status,expected,value.diagnostics)
                if expected=='indexed':self.assertTrue(value.symbols)
                else:self.assertFalse(value.symbols)
    def test_edit_rename_delete_and_scoped_query_for_every_extension(self):
        manifest=json.loads((FIXTURES/'manifest.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();configure(root,approved=True)
            for suffix,row in manifest.items():(root/row['file']).write_bytes((FIXTURES/row['file']).read_bytes())
            sync(root,full=True)
            self.assertEqual(len(IndexStore(root).read_snapshot().files),len(CODE_SUFFIXES))
            for suffix,row in manifest.items():
                with self.subTest(suffix=suffix):
                    path=root/row['file'];path.write_bytes(path.read_bytes()+b'\n')
                    packet=prepare_context(root,'',paths=[row['file']])
                    self.assertTrue(packet['context'])
                    self.assertTrue(all(x['path']==row['file'] for x in packet['context']))
                    renamed=path.with_name('renamed'+suffix);path.rename(renamed);sync(root,full=True)
                    self.assertFalse(any(x['path']==row['file'] for x in IndexStore(root).read_snapshot().files))
                    renamed.unlink();sync(root,full=True)
                    self.assertFalse(any(x['path']==renamed.name for x in IndexStore(root).read_snapshot().files))
    def test_polyglot_worktrees_are_isolated(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            for folder,name in ((a,'First'),(b,'Second')):
                root=Path(folder).resolve();configure(root,approved=True);(root/'x.py').write_text('class '+name+': pass')
            self.assertNotIn('First',json.dumps(prepare_context(Path(b),'Second',paths=['x.py'])))


class WorkflowCoverageTests(unittest.TestCase):
    def test_all_declared_optional_parsers_have_dependency_free_fallback(self):
        from unittest.mock import patch
        manifest=json.loads((FIXTURES/'manifest.json').read_text())
        with patch('aikya.code_index.parsers.treesitter._module',side_effect=ImportError('unavailable')):
            for row in manifest.values():
                if row['parser'] not in ('python','inventory'):
                    value=parse_file(row['file'],(FIXTURES/row['file']).read_bytes())
                    self.assertEqual(value.status,'file_only');self.assertFalse(value.symbols)
    def test_supported_stacks_have_valid_workflow_cases(self):
        from aikya.installation.profile import validated
        from aikya.installation.defaults import BACKENDS,FRONTENDS,CIS
        from aikya.catalogs.engineering import discover
        cases=json.loads((FIXTURES/'workflows.json').read_text())
        self.assertTrue(set(BACKENDS)-{'none'}<=set(c['input'].get('backend') for c in cases))
        self.assertTrue(set(FRONTENDS)-{'none'}<=set(c['input'].get('frontend') for c in cases))
        self.assertTrue(set(CIS)<=set(c['input'].get('ci') for c in cases))
        with tempfile.TemporaryDirectory() as folder:
            for case in cases:
                with self.subTest(case=case['name']):
                    profile=validated(case['input'],Path(folder))
                    selected=discover(Path(folder),profile,case.get('modules',[]))
                    self.assertTrue(set(case['agents'])<=set(selected['agents']))
                    self.assertIn(profile['methodology'],('odd','sdd'))

if __name__=='__main__':unittest.main()
