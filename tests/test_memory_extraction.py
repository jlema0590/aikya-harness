"""Optional extraction produces review candidates, never trusted memories."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from agent_loop_support import project,runtime
from aikya.memory import knowledge as agent_memory
from unittest.mock import patch


def config():
    return {'schema':1,'files':['src/value.py'],'scope':'project','max_turns':3,'timeout_seconds':5,'max_cost_usd':0.02}


class ExtractionTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('agent_memory_extract'),'Missing opt-in memory extraction')
        from aikya.memory import extraction as agent_memory_extract
        return agent_memory_extract

    def test_extraction_requires_approval_and_only_creates_pending_candidates(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp)
            with self.assertRaises(ValueError):module.extract(root,config(),runtime('extract'))
            self.assertFalse((root/'aikya/docs/memory-extractions').exists())
            report=module.extract(root,config(),runtime('extract'),approved=True)
            self.assertEqual('completed',report['status'])
            self.assertEqual(0.001,report['ledger']['cost_usd'])
            self.assertEqual(1,len(report['notes']))
            self.assertEqual('',agent_memory.recall(root,'value lookup',4000))
            path=root/report['notes'][0];meta=json.loads(path.read_text().split('---')[1])
            self.assertEqual('pending',meta['review_state']);self.assertEqual('model',meta['origin'])
            agent_memory.review(root,path.stem,decision='approved',approved=True)
            self.assertIn('value lookup',agent_memory.recall(root,'value lookup',4000))

    def test_invalid_candidates_and_changed_sources_cannot_be_published(self):
        module=self.module()
        for mode in ('extract_many','extract_escape','extract_stale'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=project(tmp);report=module.extract(root,config(),runtime(mode),approved=True)
                self.assertEqual('blocked',report['status'])
                self.assertEqual([],report['notes'])
                self.assertFalse((root/'aikya/docs/memory').exists())

    def test_crash_and_unknown_usage_leave_receipts_without_automatic_retries(self):
        module=self.module()
        for mode in ('crash','unknown_usage'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=project(tmp);report=module.extract(root,config(),runtime(mode),approved=True)
                self.assertEqual('blocked',report['status']);self.assertEqual([],report['notes'])
                self.assertFalse(report['ledger']['cost_known'])
                receipts=list((root/'aikya/docs/memory-extractions').glob('*/state.json'))
                self.assertEqual(1,len(receipts));saved=json.loads(receipts[0].read_text())
                self.assertEqual('blocked',saved['status'])
                self.assertNotIn('prompt',saved)

    def test_source_change_between_reading_and_runtime_start_is_not_accepted(self):
        module=self.module();original=module._sources
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp)
            def change_after_read(root,config):
                result=original(root,config)
                (root/'src/value.py').write_text('VALUE = 8\n')
                return result
            with patch.object(module,'_sources',side_effect=change_after_read):
                result=module.extract(root,config(),runtime('extract'),approved=True)
            self.assertEqual('blocked',result['status'])
            self.assertEqual([],result['notes'])

    def test_runtime_timeout_keeps_unknown_cost_and_no_candidates(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);result=module.extract(root,{**config(),'timeout_seconds':1},runtime('hang'),approved=True)
            self.assertEqual('blocked',result['status']);self.assertFalse(result['ledger']['cost_known'])
            self.assertTrue(result['pending']);self.assertEqual([],result['notes'])

    def test_private_extraction_keeps_proposals_and_receipts_outside_project_docs(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);private=Path(tmp)/'private';settings={**config(),'scope':'private'}
            report=module.extract(root,settings,runtime('extract'),approved=True,private_root=private)
            self.assertEqual('completed',report['status'])
            self.assertTrue(Path(report['notes'][0]).is_relative_to(private.resolve()))
            self.assertFalse((root/'aikya/docs/memory-extractions').exists())
            self.assertFalse((root/'aikya/docs/memory').exists())

    def test_private_receipt_symlink_is_rejected_before_running_a_query(self):
        module=self.module()
        from aikya.memory import store as memory_store
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);private=Path(tmp)/'private';outside=Path(tmp)/'outside';outside.mkdir()
            folder=memory_store.store_root(root,'private',private,create=True)
            (folder/'extractions').symlink_to(outside,target_is_directory=True)
            with self.assertRaises(ValueError):module.extract(root,{**config(),'scope':'private'},runtime('extract'),approved=True,private_root=private)
            self.assertEqual([],list(outside.iterdir()))


if __name__=='__main__':unittest.main()
