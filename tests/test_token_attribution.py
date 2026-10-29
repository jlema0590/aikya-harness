import json
from pathlib import Path
import tempfile
import unittest
from aikya.quality.efficiency import summarize_task, command_coverage
from aikya.cli.commands import BOOTSTRAP_COMMANDS

class AttributionTests(unittest.TestCase):
    def test_replayed_messages_and_subagents_are_counted_once(self):
        with tempfile.TemporaryDirectory() as folder:
            paths=[]
            for name, session in [('main','s'),('child','child')]:
                p=Path(folder)/(name+'.jsonl')
                event={'sessionId':session,'timestamp':'2026-10-29T10:00:00Z','message':{'id':'same','role':'assistant','model':'synthetic','usage':{'input_tokens':10,'output_tokens':5}}}
                p.write_text((json.dumps(event)+'\n')*2);paths.append(p)
            value=summarize_task(paths,session_id=None,start_utc=None,end_utc=None)
            self.assertEqual(value['distinct_messages'],2)
            self.assertEqual(value['tokens']['input_tokens'],20)
            self.assertNotIn('message',value)
    def test_time_window_is_not_exact_command_attribution(self):
        value=summarize_task([],session_id='s',start_utc='2026-10-29T10:00:00Z',end_utc='2026-10-29T11:00:00Z')
        self.assertEqual(value['attribution'],'unavailable')
        self.assertIsNone(value['tokens'])
    def test_every_public_command_has_usage_coverage_row(self):
        self.assertEqual(set(command_coverage()),set(BOOTSTRAP_COMMANDS))
    def test_unmeasured_command_usage_is_unknown_not_zero(self):
        for value in command_coverage().values():
            self.assertIsNone(value['tokens']);self.assertIsNone(value['model'])


class DirectRoutingTests(unittest.TestCase):
    def test_contained_work_is_direct_and_explicit_model_is_preserved(self):
        from aikya.routing.router import route
        facts={'understood':True,'contained_risk':True,'resumable_from_request_diff':True}
        value=route('fix python label',{'routine_model':'sonnet'},odd_facts=facts)
        self.assertEqual(value['execution_mode'],'direct')
        self.assertEqual(value['recommended_model'],'sonnet')
        dangerous=route('fix authentication',odd_facts=facts)
        self.assertTrue(dangerous['independent_review_required'])

if __name__=='__main__':unittest.main()
