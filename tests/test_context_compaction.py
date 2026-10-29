import tempfile
from pathlib import Path
import unittest
from aikya.middleware.compaction import checkpoint, configure_native, warning

class CompactionTests(unittest.TestCase):
    def test_compaction_preserves_pending_checks_and_never_creates_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();execution={'run_id':'abc','command':'aikya-feature','methodology':'odd','candidate_generation':3,'phases':{'security':{'status':'pending'}},'prompt':'SECRET'}
            before=repr(execution)
            value=checkpoint(root,{'session_id':'s','hook_event_name':'PreCompact','compact_summary':'SECRET'},execution)
            self.assertEqual(value['pending_checks'],['security'])
            self.assertNotIn('SECRET',repr(value));self.assertNotIn('approval',value)
            self.assertEqual(repr(execution),before)
    def test_post_compact_increments_epoch_without_resetting_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            a=checkpoint(root,{'session_id':'s','hook_event_name':'PreCompact'},None)
            b=checkpoint(root,{'session_id':'s','hook_event_name':'PostCompact'},None)
            self.assertEqual(b['context_epoch'],a['context_epoch']+1)
    def test_effective_window_is_not_assumed_from_model_context_percentage(self):
        self.assertIsNone(warning({'context_pct':90,'context_size':1000000,'observed_at':100},now=101))
        self.assertIsNotNone(warning({'working_window':200000,'current_context_tokens':160000,'observed_at':100},now=101))
        self.assertIsNone(warning({'working_window':200000,'current_context_tokens':160000,'observed_at':100},now=200))
    def test_native_auto_preserves_custom_settings_and_unsupported_host(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();p=root/'.claude/settings.json';p.parent.mkdir();p.write_text('{"autoCompactWindow":500000,"model":"opus"}')
            self.assertEqual(configure_native(root,approved=True,supported=True)['status'],'needs_review')
            self.assertIn('500000',p.read_text())
            self.assertEqual(configure_native(root,approved=True,supported=False)['status'],'manual_only')
            with self.assertRaises(ValueError):configure_native(root,approved=False,supported=True)


class NativeConfigurationTests(unittest.TestCase):
    def test_auto_mode_requires_observer_and_registers_supported_events(self):
        from aikya.middleware.compaction import configure_native
        import json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            self.assertEqual(configure_native(root,approved=True,supported=True)['status'],'manual_only')
            path=root/'.claude/settings.json';path.parent.mkdir(exist_ok=True)
            observer={'type':'command','command':'python execution_observer.py hook'}
            path.write_text(json.dumps({'model':'opus','hooks':{'UserPromptSubmit':[{'hooks':[observer]}]}}))
            value=configure_native(root,approved=True,supported=True)
            data=json.loads(path.read_text())
            self.assertEqual(data['model'],'opus');self.assertEqual(data['autoCompactWindow'],200000)
            self.assertIn('PreCompact',data['hooks']);self.assertIn('PostCompact',data['hooks'])
            self.assertTrue(value['hooks_registered'])

if __name__=='__main__':unittest.main()
