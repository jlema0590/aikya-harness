import unittest
from aikya.catalogs.external import enabled_names, planned_commands

class OptionalSkillDefaults(unittest.TestCase):
    def test_no_vendor_is_selected_without_user_choice(self):
        for profile in ({},{'frontend':'react','mobile':'flutter'}):
            self.assertEqual(enabled_names(profile),[])
            self.assertEqual(planned_commands(profile),[])

if __name__=='__main__':unittest.main()

class MissingSkillSelection(unittest.TestCase):
    def test_approved_install_still_requires_a_selected_source(self):
        import tempfile
        from pathlib import Path
        from aikya.catalogs.external import install_all
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(ValueError):install_all(root,{},permission=True)
            self.assertFalse((root/'.harness/external-skills-lock.json').exists())
