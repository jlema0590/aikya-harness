import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aikya.tools.check_evidence import binding, reusable

class CheckReuseTests(unittest.TestCase):
    def test_candidate_definition_and_environment_invalidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();source=root/'a.py';source.write_text('x=1')
            check={'name':'test','command':[sys.executable,'-c','pass'],'required':True,'reusable':True}
            value=binding(root,check)
            evidence={'kind':'process','check':'test','exit_code':0,'binding':value}
            self.assertTrue(reusable(evidence,value))
            source.write_text('x=2');self.assertNotEqual(binding(root,check),value)
            source.write_text('x=1')
            self.assertNotEqual(binding(root,{**check,'command':[sys.executable,'-c','assert False']}),value)
            with patch.dict(os.environ,{'AIKYA_SYNTHETIC_CHECK_INPUT':'changed'}):self.assertNotEqual(binding(root,check),value)
            self.assertFalse(reusable({**evidence,'exit_code':1},value))
            self.assertIsNone(binding(root,{k:v for k,v in check.items() if k!='reusable'}))

if __name__=='__main__':unittest.main()
