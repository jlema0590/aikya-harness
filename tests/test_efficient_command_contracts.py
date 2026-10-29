import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from aikya.cli.main import main

class EfficientCommandTests(unittest.TestCase):
    def test_analyze_summary_is_bounded_and_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'pom.xml').write_text('<project/>')
            out=io.StringIO()
            with contextlib.redirect_stdout(out):code=main(['analyze','--target',str(root),'--dry-run','--summary','--methodology','odd'])
            result=json.loads(out.getvalue())
            self.assertIn(code,(0,4));self.assertLessEqual(len(out.getvalue()),2000)
            self.assertIn('status',result);self.assertIn('omitted_count',result)
            self.assertEqual([p.name for p in root.iterdir()],['pom.xml'])

if __name__=='__main__':unittest.main()
