"""Scoped maintainability checks stop large candidates and expose exact clones."""
import runtime_support
import importlib.util,json,tempfile,unittest
from pathlib import Path
from agent_loop_support import project,config,runtime


class QualityTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('code_quality'),'Missing shared code quality gate')
        from aikya.quality import source as code_quality
        return code_quality

    def test_line_limit_boundary_and_content_bound_exceptions(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'service.py';p.write_text('VALUE = 1\n'*1000)
            self.assertEqual([],module.inspect_paths(root,['service.py'])['errors'])
            p.write_text('VALUE = 1\n'*1001)
            result=module.inspect_paths(root,['service.py'])
            self.assertEqual('file_too_large',result['errors'][0]['code'])
            import hashlib
            (root/'.aikya').mkdir();exception=root/'.aikya/code-quality-exceptions.json'
            exception.write_text(json.dumps({'schema':1,'exceptions':[{'path':'service.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reason':'Reviewed compatibility fixture; split in a separate change.'}]}))
            self.assertEqual([],module.inspect_paths(root,['service.py'])['errors'])
            p.write_text(p.read_text()+'VALUE = 2\n')
            self.assertEqual('file_too_large',module.inspect_paths(root,['service.py'])['errors'][0]['code'])

    def test_duplicate_bodies_are_reported_and_small_helpers_are_ignored(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            body=''.join('    value += '+str(i)+'\n' for i in range(10))+'    return value\n'
            (root/'first.py').write_text('def first(value):\n'+body)
            (root/'second.py').write_text('def second(value):\n'+body)
            (root/'tiny.py').write_text('def one():\n    return 1\ndef two():\n    return 1\n')
            result=module.inspect_paths(root,['first.py','second.py','tiny.py'])
            self.assertEqual([],result['errors'])
            self.assertEqual(1,len(result['duplicates']))
            self.assertEqual({'first.py','second.py'},{x['path'] for x in result['duplicates'][0]})

    def test_unsafe_paths_and_symlinks_cannot_be_audited(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);outside=root/'outside.py';outside.write_text('VALUE = 1\n')
            (root/'link.py').symlink_to(outside)
            for name in ('../outside.py','.env','link.py'):
                with self.subTest(name=name),self.assertRaises(ValueError):module.inspect_paths(root,[name])

    def test_loop_never_completes_a_task_with_an_oversized_candidate(self):
        self.module()
        from aikya.core import loop as agent_loop; from aikya.workflows import odd as odd_engine
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);(root/'src/value.py').write_text('VALUE = 1\n'*1001)
            result=agent_loop.run(root,config(),runtime('no_write'),approved=True)
            self.assertEqual('blocked',result['status'])
            self.assertEqual('code_quality_failed',result['reason'])
            self.assertNotEqual('done',odd_engine.load(root,'value')['tasks'][0]['status'])

    def test_edit_feedback_reports_non_python_oversized_source(self):
        self.module()
        import importlib.util
        from agent_loop_support import ROOT
        spec=runtime_support.module_spec('quality_edit_hook',ROOT/'src/aikya/resources/project_template/.claude/hooks/check_edit.py')
        hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook);hook=getattr(hook,'_module',hook)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'widget.ts').write_text('const value = 1;\n'*1001)
            feedback=hook.feedback({'tool_input':{'file_path':'widget.ts'}},root)
            self.assertIsInstance(feedback,str)
            self.assertIn('1001',feedback)


if __name__=='__main__':unittest.main()
