import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.cli.summary import compact
from aikya.middleware.task_context import for_prompt
from aikya.middleware.compaction import checkpoint
from aikya.middleware.observer import observe

class EfficiencyEdgeCases(unittest.TestCase):
    def test_nested_blockers_remain_visible_in_summary(self):
        result=compact({'status':'NEEDS_REVIEW','modules':[{'errors':['synthetic conflict']} ]},exit_code=4)
        self.assertIn('synthetic conflict',result['blockers'])
    def test_same_prompt_deduplicates_but_post_compact_rehydrates_next_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();(root/'login.py').write_text('class Login: pass')
            event={'hook_event_name':'UserPromptSubmit','session_id':'s','prompt_id':'p','prompt':'/aikya-feature change Login'}
            execution={'command':'aikya-feature','status':'running'}
            self.assertIsNotNone(for_prompt(root,event,execution))
            self.assertIsNone(for_prompt(root,event,execution))
            checkpoint(root,{'hook_event_name':'PostCompact','session_id':'s'},execution)
            followup={**event,'prompt_id':'after','prompt':'continue'}
            resumed=for_prompt(root,followup,execution)
            self.assertIsNotNone(resumed)
            self.assertIn('class Login',json.dumps(resumed))
    def test_plain_model_query_has_no_implementation_phase(self):
        with tempfile.TemporaryDirectory() as folder:
            context={'root':folder,'session_id':'s'}
            event={'hook_event_name':'UserPromptSubmit','prompt_id':'p','prompt':'/aikya-models'}
            result=observe(context,event)
            self.assertEqual(result['phases']['implement']['status'],'skipped')


class LongContextWarningTests(unittest.TestCase):
    def test_verified_window_warning_is_delivered_once_per_context_epoch(self):
        import time
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();(root/'a.py').write_text('class A: pass')
            metrics={'working_window':200000,'current_context_tokens':160000,'observed_at':time.time()}
            with patch('aikya.middleware.metrics.read_metrics',return_value=metrics):
                a=for_prompt(root,{'hook_event_name':'UserPromptSubmit','session_id':'s','prompt_id':'a','prompt':'/aikya-feature A'})
                b=for_prompt(root,{'hook_event_name':'UserPromptSubmit','session_id':'s','prompt_id':'b','prompt':'/aikya-feature A'})
            self.assertIn('75%',json.dumps(a))
            self.assertNotIn('75%',json.dumps(b))


class CompactionTaskBoundary(unittest.TestCase):
    def test_explicit_new_task_does_not_inherit_previous_source_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();(root/'login.py').write_text('class Login: pass');(root/'other.py').write_text('class OtherWidget: pass')
            execution={'command':'aikya-feature','status':'running'}
            base={'hook_event_name':'UserPromptSubmit','session_id':'s','prompt_id':'first','prompt':'/aikya-feature change Login'}
            for_prompt(root,base,execution)
            checkpoint(root,{'hook_event_name':'PostCompact','session_id':'s'},execution)
            value=for_prompt(root,{**base,'prompt_id':'new','prompt':'/aikya-feature change OtherWidget'},execution)
            self.assertIn('OtherWidget',json.dumps(value))

if __name__=='__main__':unittest.main()
