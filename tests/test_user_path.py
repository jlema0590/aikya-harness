"""User PATH changes have a narrow, reversible ownership boundary."""
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class UserPath(unittest.TestCase):
    def module(self):
        try:return importlib.import_module('aikya.installation.bootstrap.user_path')
        except ModuleNotFoundError:self.fail('Managed user PATH is not implemented')

    @unittest.skipIf(os.name=='nt','POSIX profile ownership')
    def test_profile_surroundings_and_user_edits_are_preserved(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve();home=base/'home';home.mkdir();profile=home/'.zshrc';profile.write_bytes(b'# original\n')
            with patch.dict(os.environ,{'HOME':str(home),'SHELL':'/bin/zsh'}):
                module.ensure_user_path(base/"app's bin",root=base/'app')
                first=profile.read_text();self.assertIn('# original\n',first);self.assertIn("app",first)
                module.ensure_user_path(base/"app's bin",root=base/'app')
                self.assertEqual(first,profile.read_text())
                profile.write_text(first+'# later edit\n')
                module.remove_user_path(base/'app')
                self.assertEqual('# original\n# later edit\n',profile.read_text())

    @unittest.skipIf(os.name=='nt','POSIX profile ownership')
    def test_symlink_and_modified_block_are_never_overwritten(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve();home=base/'home';home.mkdir();outside=base/'owner';outside.write_text('custom')
            with patch.dict(os.environ,{'HOME':str(home),'SHELL':'/bin/bash'}):
                profile=home/'.bashrc';profile.symlink_to(outside)
                with self.assertRaises(ValueError):module.ensure_user_path(base/'bin',root=base/'app')
                self.assertEqual('custom',outside.read_text());profile.unlink()
                module.ensure_user_path(base/'bin',root=base/'app')
                profile.write_text(profile.read_text().replace('export PATH=','export CUSTOM='))
                before=profile.read_text();module.remove_user_path(base/'app')
                self.assertEqual(before,profile.read_text())

    def test_disabled_path_has_no_side_effects(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as t:
            base=Path(t).resolve();module.ensure_user_path(base/'bin',enabled=False,root=base/'app')
            self.assertEqual([],list(base.iterdir()))

    def test_windows_path_preserves_other_entries_and_existing_entry_ownership(self):
        module=self.module()
        class Registry:
            HKEY_CURRENT_USER=1;REG_EXPAND_SZ=2
            def __init__(self):self.value='C:\\owner';self.kind=2
            def CreateKey(self,*args):return self
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def QueryValueEx(self,*args):return self.value,self.kind
            def SetValueEx(self,key,name,reserved,kind,value):self.value=value;self.kind=kind
        registry=Registry()
        with tempfile.TemporaryDirectory() as t,patch.dict('sys.modules',{'winreg':registry}):
            base=Path(t).resolve();marker=base/'path.json'
            self.assertTrue(hasattr(module,'ensure_windows_path'),'Managed Windows PATH helper missing')
            module.ensure_windows_path('C:\\Aikya\\bin',marker)
            self.assertEqual('C:\\owner;C:\\Aikya\\bin',registry.value)
            registry.value+=';C:\\later'
            module.remove_windows_path(__import__('json').loads(marker.read_text()))
            self.assertEqual('C:\\owner;C:\\later',registry.value)
            registry.value='C:\\AIKYA\\BIN';other=base/'unowned.json'
            module.ensure_windows_path('C:\\Aikya\\bin',other)
            self.assertFalse(other.exists())

    def test_windows_broadcast_follows_user_path_changes(self):
        import ctypes
        user_path=self.module()
        class Registry:
            HKEY_CURRENT_USER=1;REG_EXPAND_SZ=2
            value='C:\\owner'
            def CreateKey(self,*args):return self
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def QueryValueEx(self,*args):return self.value,2
            def SetValueEx(self,key,name,reserved,kind,value):self.value=value
        registry=Registry()
        class Send:
            def __init__(self):self.messages=[]
            def __call__(self,window,message,wparam,lparam,flags,timeout,result):
                self.messages.append((window,message,lparam,registry.value))
                return 1
        send=Send()
        class User32:SendMessageTimeoutW=send
        with tempfile.TemporaryDirectory() as t,patch.dict('sys.modules',{'winreg':registry}),patch.object(ctypes,'WinDLL',return_value=User32(),create=True):
            marker=Path(t).resolve()/'path.json'
            user_path.ensure_windows_path('C:\\Aikya\\bin',marker)
            self.assertEqual([(65535,26,'Environment','C:\\owner;C:\\Aikya\\bin')],send.messages)
            user_path.remove_windows_path({'entry':'C:\\Aikya\\bin'})
            self.assertEqual((65535,26,'Environment','C:\\owner'),send.messages[-1])
