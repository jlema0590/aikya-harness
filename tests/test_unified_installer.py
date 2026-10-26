"""Selections and CLI boundaries preserve unrelated user installations."""
import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from aikya.installation.bootstrap import cli, download
from test_mods_distribution import release


class UnifiedInstaller(unittest.TestCase):
    def module(self,name):
        try:return importlib.import_module('aikya.installation.bootstrap.'+name)
        except ModuleNotFoundError:self.fail('Unified installer component missing: '+name)

    def test_dry_run_is_offline_and_does_not_require_claude(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();output=io.StringIO()
            with patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(root/'app')}),patch.object(download,'https_bytes',side_effect=AssertionError('Network forbidden')),contextlib.redirect_stdout(output):
                try:code=cli.main(['install','--dry-run'])
                except SystemExit:self.fail('Default installation requires unnecessary options')
            self.assertEqual(0,code)
            plan=json.loads(output.getvalue())
            self.assertEqual(['aikya-flow','aikya-usage'],plan['mods'])
            self.assertEqual('global',plan['scope'])
            self.assertEqual('latest',plan['version'])
            self.assertFalse((root/'app').exists())

    def test_update_preserves_receipt_ids_and_does_not_add_boxbot(self):
        components=self.module('components')
        cases=[(None,()),({'selected':[]},()),({'selected':['aikya-flow','aikya-usage']},('aikya-flow','aikya-usage')),({'selected':['aikya-boxbot']},('aikya-boxbot',))]
        for previous,want in cases:
            with self.subTest(previous=previous):
                plan=components.plan_components('global',None,None,previous,action='update')
                self.assertEqual(want,plan.selected)
        self.assertEqual(('aikya-flow','aikya-usage'),components.plan_components('global',None,None,None).selected)

    def test_none_never_requires_claude_and_missing_claude_fails_before_writes(self):
        plugins=self.module('claude_plugins')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve()
            with patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(root/'app')}),patch.object(plugins.shutil,'which',return_value=None),contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(2,cli.main(['install','--version','7.1.0']))
            self.assertIn('Claude',errors.getvalue())
            self.assertFalse((root/'app').exists())

    @unittest.skipUnless(shutil.which('claude'),'Claude CLI required for native plugin contract')
    def test_real_cli_installs_updates_and_preserves_externally_added_boxbot(self):
        plugins=self.module('claude_plugins');mods=self.module('mods');components=self.module('components')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();release(root/'assets');bundle=mods.prepare_mods('0.0.10',root/'sources',root/'assets')
            with patch.dict(os.environ,{'CLAUDE_CONFIG_DIR':str(root/'config'),'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1'}):
                adapter=plugins.Claude(root)
                adapter.preflight(bundle.claude_version)
                receipt={}
                plan=components.plan_components('global',None,None,None)
                result=components.install_plugins(bundle,plan,receipt,adapter,lambda:None)
                self.assertEqual('complete',result['status'])
                self.assertEqual({'aikya-flow','aikya-usage'},set(result['plugins']))
                adapter.command('plugin','install','aikya-boxbot@aikya-mods','--scope','user','--json')
                result=components.install_plugins(bundle,plan,receipt,adapter,lambda:None)
                self.assertNotIn('aikya-boxbot',result['plugins'])
                self.assertEqual(3,len(adapter.inventory()))
                adopt=components.plan_components('global',None,['aikya-boxbot'],receipt,action='update')
                components.install_plugins(bundle,adopt,receipt,adapter,lambda:None)
                self.assertFalse(receipt['plugins']['aikya-boxbot']['remove_on_uninstall'])
                components.uninstall_plugins(receipt,adapter,lambda:None)
                self.assertEqual(['aikya-boxbot@aikya-mods'],[p['id'] for p in adapter.inventory()])
                self.assertEqual('aikya-mods',adapter.marketplaces()[0]['name'])

    def test_partial_failure_records_success_and_retry_resumes(self):
        components=self.module('components');mods=self.module('mods')
        class Host:
            def __init__(self):self.installed=[];self.fail=True
            def marketplaces(self):return []
            def inventory(self):return self.installed
            def command(self,*args):
                if args[:2]==('plugin','install'):
                    if 'aikya-usage@aikya-mods' in args and self.fail:raise ValueError('controlled second plugin failure')
                    self.installed.append({'id':args[2],'scope':'user','version':'0.1.0'})
                return {'outcome':'ok'}
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();release(root/'assets');bundle=mods.prepare_mods('0.0.10',root/'sources',root/'assets')
            plan=components.plan_components('global',None,None,None);receipt={};saved=[];host=Host()
            with self.assertRaisesRegex(ValueError,'controlled'):
                components.install_plugins(bundle,plan,receipt,host,lambda:saved.append(json.loads(json.dumps(receipt))))
            self.assertEqual('partial',receipt['status']);self.assertIn('aikya-flow',saved[-1]['plugins'])
            host.fail=False
            components.install_plugins(bundle,plan,receipt,host,lambda:None)
            self.assertEqual('complete',receipt['status'])
            self.assertEqual(2,len(host.installed))

    def test_interrupted_marketplace_move_and_plugin_update_can_resume(self):
        components=self.module('components');mods=self.module('mods')
        class Host:
            def __init__(self,old):
                self.path=str(old.path);self.fail=True
                self.installed=[{'id':'aikya-flow@aikya-mods','scope':'user','version':'0.0.9','readFromFolder':str(old.path/'mods/aikya-flow')}]
            def marketplaces(self):return [{'name':'aikya-mods','path':self.path}]
            def inventory(self):return self.installed
            def command(self,*args):
                if args[:3]==('plugin','marketplace','add'):
                    if self.fail:raise ValueError('marketplace interrupted')
                    self.path=args[3]
                elif args[:2]==('plugin','update'):
                    self.installed[0].update(version='0.1.0',readFromFolder=str(Path(self.path)/'mods/aikya-flow'))
                return {'outcome':'ok'}
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();release(root/'assets','0.0.9');old=mods.prepare_mods('0.0.9',root/'sources',root/'assets')
            release(root/'assets');new=mods.prepare_mods('0.0.10',root/'sources',root/'assets')
            receipt={'selected':['aikya-flow'],'scope':'user','target':None,'marketplace_owned':True,'source':str(old.path),'plugins':{'aikya-flow':{'version':'0.0.9','source':str(old.path/'mods/aikya-flow'),'remove_on_uninstall':True}}}
            plan=components.plan_components('global',None,None,receipt,action='update');host=Host(old)
            with self.assertRaisesRegex(ValueError,'interrupted'):components.install_plugins(new,plan,receipt,host,lambda:None)
            host.fail=False
            components.install_plugins(new,plan,receipt,host,lambda:None)
            self.assertEqual('complete',receipt['status'])
            self.assertEqual('0.1.0',receipt['plugins']['aikya-flow']['version'])

    def test_cross_scope_component_receipt_cannot_remove_user_plugins(self):
        from aikya.installation.bootstrap import state
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();project=root/'project';project.mkdir();app=root/'app'
            file=app/'components'/state.receipt_path(app,'project',project).name
            state.write_json(file,{'schema':1,'scope':'user','target':None,'plugins':{},'selected':[],'status':'complete'})
            with patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(app)}),contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(2,cli.main(['uninstall','--scope','project','--target',str(project)]))
            self.assertIn('scope',errors.getvalue())
            self.assertFalse((app/'owner.json').exists())

    def test_registered_source_can_be_shared_between_owned_scopes_without_replacement(self):
        components=self.module('components');mods=self.module('mods')
        class Host:
            def marketplaces(self):return [{'name':'aikya-mods','path':str(bundle.path)}]
            def inventory(self):return []
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();release(root/'assets');bundle=mods.prepare_mods('0.0.10',root/'sources',root/'assets')
            try:owned=components.check_source(bundle,{},Host(),managed_sources={str(bundle.path)})
            except TypeError:self.fail('Cross-scope shared-source ownership is not supported')
            self.assertTrue(owned)

    def test_uninstall_recovers_plugin_installed_before_receipt_checkpoint(self):
        components=self.module('components')
        class Host:
            def __init__(self):self.installed=[{'id':'aikya-flow@aikya-mods','version':'0.1.0','scope':'user','readFromFolder':'/owned/mods/aikya-flow'}]
            def inventory(self):return self.installed
            def marketplaces(self):return []
            def command(self,*args):
                if args[:2]==('plugin','uninstall'):self.installed=[]
                return {'outcome':'ok'}
        host=Host();receipt={'scope':'user','target':None,'plugins':{'aikya-flow':{'remove_on_uninstall':True,'pending_version':'0.1.0','pending_source':'/owned/mods/aikya-flow'}}}
        try:components.uninstall_plugins(receipt,host,lambda:None)
        except KeyError:self.fail('Partial plugin intent cannot be safely removed')
        self.assertEqual([],host.inventory())
        self.assertEqual('removed',receipt['status'])

    def test_uninstall_recovers_marketplace_registered_before_checkpoint(self):
        components=self.module('components')
        class Host:
            def __init__(self):self.markets=[{'name':'aikya-mods','path':'/owned/source'}]
            def inventory(self):return []
            def marketplaces(self):return self.markets
            def command(self,*args):
                if args[:3]==('plugin','marketplace','remove'):self.markets=[]
                return {'outcome':'ok'}
        host=Host();receipt={'scope':'user','target':None,'plugins':{},'marketplace_owned':True,'pending_source':'/owned/source'}
        try:components.uninstall_plugins(receipt,host,lambda:None)
        except KeyError:self.fail('Partial marketplace intent cannot be safely removed')
        self.assertEqual([],host.marketplaces())

    @unittest.skipUnless(shutil.which('claude'),'Claude CLI required for native plugin contract')
    def test_real_cli_updates_from_new_verified_source_and_project_scope(self):
        plugins=self.module('claude_plugins');mods=self.module('mods');components=self.module('components')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve();project=root/'project';project.mkdir()
            release(root/'assets');old=mods.prepare_mods('0.0.10',root/'sources',root/'assets')
            release(root/'assets','0.0.11',plugin_version='0.1.1');new=mods.prepare_mods('0.0.11',root/'sources',root/'assets')
            with patch.dict(os.environ,{'CLAUDE_CONFIG_DIR':str(root/'config'),'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1'}):
                adapter=plugins.Claude(project);adapter.preflight();receipt={}
                plan=components.plan_components('project',project,['aikya-flow'],None)
                components.install_plugins(old,plan,receipt,adapter,lambda:None)
                updated=components.plan_components('project',project,None,receipt,action='update')
                components.install_plugins(new,updated,receipt,adapter,lambda:None)
                installed=[p for p in adapter.inventory() if p['id']=='aikya-flow@aikya-mods']
                self.assertEqual(1,len(installed));self.assertEqual('0.1.1',installed[0]['version'])
                self.assertEqual('project',installed[0]['scope'])
                components.uninstall_plugins(receipt,adapter,lambda:None)
                self.assertEqual([],adapter.inventory())

    def test_failed_uninstall_remains_partial_and_retains_remaining_ownership(self):
        components=self.module('components')
        class Host:
            def __init__(self):self.ids=['aikya-flow','aikya-usage']
            def inventory(self):return [{'id':n+'@aikya-mods','version':'0.1.0','scope':'user','readFromFolder':'/owned/'+n} for n in self.ids]
            def marketplaces(self):return []
            def command(self,*args):
                if args[2]=='aikya-usage@aikya-mods':raise ValueError('controlled uninstall failure')
                self.ids.remove(args[2].split('@')[0]);return {'outcome':'ok'}
        receipt={'scope':'user','status':'complete','plugins':{n:{'source':'/owned/'+n,'version':'0.1.0','remove_on_uninstall':True} for n in ('aikya-flow','aikya-usage')}}
        with self.assertRaisesRegex(ValueError,'controlled'):
            components.uninstall_plugins(receipt,Host(),lambda:None)
        self.assertEqual('partial',receipt['status'])
        self.assertEqual(['aikya-usage'],list(receipt['plugins']))

    def test_legacy_harness_cannot_activate_unified_mods_management(self):
        from aikya.installation.bootstrap import coordinator
        class Host:
            def preflight(self,*args):pass
        with tempfile.TemporaryDirectory() as t:
            root=Path(t).resolve()
            with patch.dict(os.environ,{'AIKYA_INSTALL_ROOT':str(root/'app')}),patch.object(coordinator,'Claude',return_value=Host()),patch.object(download,'fetch_release',side_effect=AssertionError('Legacy wheel reached provisioning')),contextlib.redirect_stderr(io.StringIO()) as errors:
                try:code=cli.main(['install','--version','7.0.1','--mods','recommended'])
                except AssertionError:self.fail('Legacy Harness is not blocked before unified provisioning')
            self.assertEqual(2,code)
            self.assertIn('7.1.0',errors.getvalue())
            self.assertFalse((root/'app').exists())

    def test_windows_source_case_and_separator_aliases_remain_owned(self):
        from pathlib import PureWindowsPath
        from types import SimpleNamespace
        components=self.module('components')
        source=PureWindowsPath('C:/Users/Team/Aikya/Mods/releases/v0.0.10/aikya-mods')
        class Host:
            def marketplaces(self):return [{'name':'aikya-mods','path':'c:\\users\\team\\aikya\\mods\\releases\\v0.0.10\\aikya-mods'}]
            def inventory(self):return []
        receipt={'marketplace_owned':True,'source':str(source),'plugins':{},'scope':'user'}
        with patch.object(components,'Path',PureWindowsPath):
            try:owned=components.check_source(SimpleNamespace(path=source),receipt,Host())
            except ValueError:self.fail('Windows case/separator aliases incorrectly lose source ownership')
        self.assertTrue(owned)
