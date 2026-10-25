"""Memory approval, private storage and moved-project adoption are explicit."""
import json, os, shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from agent_loop_support import project
from aikya.memory import knowledge as memory


def raw(scope='project'):
    return {'kind':'feedback','text':'Use a stable value lookup.','source':'src/value.py','ttl_days':30,'scope':scope}


class LifecycleTests(unittest.TestCase):
    def test_pending_and_rejected_notes_never_enter_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp)
            self.assertTrue(hasattr(memory,'propose'), 'Missing reviewed candidate lifecycle')
            note=memory.propose(root,raw())
            self.assertEqual('',memory.recall(root,'stable value',4000))
            with self.assertRaises(ValueError):memory.review(root,Path(note).stem,decision='approved')
            memory.review(root,Path(note).stem,decision='rejected',approved=True)
            self.assertEqual('',memory.recall(root,'stable value',4000))
            memory.review(root,Path(note).stem,decision='approved',approved=True)
            self.assertIn('Use a stable value',memory.recall(root,'stable value',4000))
            meta=json.loads((root/note).read_text().split('---')[1])
            self.assertEqual('approved',meta['review_state'])
            self.assertEqual('project',meta['scope'])
            self.assertIsInstance(meta['reviewed_at'],(int,float))
            self.assertEqual(64,len(meta['project_identity']))

    def test_review_rejects_changed_sources_and_custom_note_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp)
            self.assertTrue(hasattr(memory,'propose'), 'Missing reviewed candidate lifecycle')
            note=memory.propose(root,raw());(root/'src/value.py').write_text('VALUE = 2\n')
            with self.assertRaises(ValueError):memory.review(root,Path(note).stem,decision='approved',approved=True)
            original=(root/note).read_text();(root/note).write_text(original.replace('Use a stable value lookup.','Custom edited note.'))
            with self.assertRaises(ValueError):memory.review(root,Path(note).stem,decision='rejected',approved=True)
            self.assertIn('Custom edited note.',(root/note).read_text())

    def test_private_notes_are_opt_in_outside_git_and_permission_restricted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);private=Path(tmp)/'private'
            note=memory.remember(root,raw('private'),approved=True,private_root=private)
            self.assertFalse((root/'aikya/docs/memory').exists())
            self.assertTrue(Path(note).is_relative_to(private.resolve()))
            self.assertEqual('',memory.recall(root,'stable value',4000,private_root=private))
            self.assertIn('stable value',memory.recall(root,'stable value',4000,scopes=['private'],private_root=private))
            self.assertLessEqual(len(memory.recall(root,'stable value',25,scopes=['project','private'],private_root=private)),25)
            if os.name!='nt':
                self.assertEqual(0o600,Path(note).stat().st_mode&0o777)
                self.assertEqual(0o700,Path(note).parent.stat().st_mode&0o777)
            with self.assertRaises(ValueError):memory.remember(root,raw('private'),approved=True,private_root=root/'private')

    def test_moved_project_and_private_notes_require_explicit_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);private=Path(tmp)/'private'
            note=memory.remember(root,raw(),approved=True)
            private_note=memory.remember(root,raw('private'),approved=True,private_root=private)
            prior=json.loads((root/note).read_text().split('---')[1])['project_identity']
            moved=Path(tmp)/'moved';shutil.copytree(root,moved)
            self.assertEqual('',memory.recall(moved,'stable value',4000,scopes=['project','private'],private_root=private))
            with self.assertRaises(ValueError):memory.migrate(moved,prior,scope='project')
            memory.migrate(moved,prior,scope='project',approved=True)
            memory.migrate(moved,prior,scope='private',approved=True,private_root=private)
            self.assertIn('stable value',memory.recall(moved,'stable value',4000,scopes=['private'],private_root=private))
            self.assertIn('stable value',memory.recall(moved,'stable value',4000))
            self.assertTrue(Path(private_note).is_file(), 'Migration preserves the old private store')
            self.assertIn('stable value',memory.recall(root,'stable value',4000))

    def test_legacy_notes_require_review_before_binding_to_a_checkout(self):
        from aikya.core import checkpoints as state
        from aikya.documentation.layout import write_document
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);text='Use a stable value lookup.'
            ident=state.sha({'kind':'feedback','text':text,'source':'src/value.py'})[:24]
            meta={'schema':1,'id':ident,'kind':'feedback','source':'src/value.py','source_hash':state.fingerprint(root/'src/value.py'),'created_at':10,'ttl_days':30}
            write_document(root,'memory/'+ident+'.md','---\n'+json.dumps(meta)+'\n---\n\n'+text)
            self.assertEqual('',memory.recall(root,'value',4000,now=20))
            memory.review(root,ident,decision='approved',approved=True,now=20)
            self.assertIn(text,memory.recall(root,'value',4000,now=20))

    def test_interrupted_migration_is_explicitly_retryable_and_keeps_a_receipt(self):
        from aikya import storage as durable_io
        with tempfile.TemporaryDirectory() as tmp:
            root=project(tmp);note=memory.remember(root,raw(),approved=True)
            memory.remember(root,{**raw(),'text':'A second stable lookup decision.'},approved=True)
            prior=json.loads((root/note).read_text().split('---')[1])['project_identity']
            moved=Path(tmp)/'moved';shutil.copytree(root,moved)
            original=durable_io.atomic_write;counter=[0]
            def fail_second(path,body,**kwargs):
                if Path(path).parent.name=='memory' and Path(path).name!='MEMORY.md':
                    counter[0]+=1
                    if counter[0]==2:raise OSError('simulated second note interruption')
                return original(path,body,**kwargs)
            with patch('aikya.storage.atomic_write',side_effect=fail_second):
                with self.assertRaises(OSError):memory.migrate(moved,prior,approved=True)
            memory.migrate(moved,prior,approved=True)
            self.assertEqual(2,len(list((moved/'aikya/docs/memory').glob('[a-f0-9]'*24+'.md'))))
            self.assertTrue(list((moved/'aikya/docs/memory-migrations').glob('*.md')))


class DurableWriteTests(unittest.TestCase):
    def test_memory_and_documents_use_fsync_and_failed_replace_keeps_original(self):
        from aikya.documentation import layout as docs_layout
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'note.md';target.write_text('original')
            with patch('os.fsync',wraps=os.fsync) as sync:
                docs_layout._write(target,'updated')
                self.assertGreaterEqual(sync.call_count,1)
            with patch('os.replace',side_effect=OSError('simulated interrupted replacement')):
                with self.assertRaises(OSError):docs_layout._write(target,'lost')
            self.assertEqual('updated',target.read_text())
            self.assertEqual(['note.md'],[p.name for p in root.iterdir()])


if __name__=='__main__':unittest.main()
