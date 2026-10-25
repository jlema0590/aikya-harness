"""Aikya 6.0.0 SDD: state-machine, traceability, safety and installation tests."""
import runtime_support
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aikya.workflows.sdd import engine as sdd
from aikya.installation import facade as install
from aikya.installation import registration as aikya_setup
from aikya.documentation import bootstrap as doc_bootstrap

class Sdd60Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def profile(self,kind,methodology="sdd"):
        template={"development":"next-react",
                  "infrastructure":"infra-terraform-only",
                  "devops":"devops-kustomize"}[kind]
        info=json.loads((ROOT/"examples"/template/"answers.json").read_text(encoding="utf8"))
        info["methodology"]=methodology
        return install.validated(info,self.root)

    def configured(self,kind="development",methodology="sdd"):
        profile=self.profile(kind,methodology)
        path=self.root/".harness/project-profile.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({"decisions":profile}),encoding="utf8")
        return profile

    def fixture(self,kind):
        dirname={"development":"order-api",
                 "infrastructure":"aws-network",
                 "devops":"kubernetes-release"}[kind]
        root=ROOT/"examples/sdd"/kind/dirname
        return {part:json.loads((root/(part+".json")).read_text(encoding="utf8"))
                for part in ("spec","clarify","plan","tasks")}

    def test_backward_compatible_standard_methodology(self):
        p=self.profile("development",methodology="standard")
        self.assertEqual("odd",p["methodology"])
        raw=json.loads((ROOT/"examples/next-react/answers.json").read_text())
        self.assertEqual("odd",install.validated(raw,self.root)["methodology"])
        with self.assertRaisesRegex(ValueError,"methodology"):
            install.validated({**raw,"methodology":"invalid"},self.root)

    def test_new_requires_opt_in_and_valid_profile(self):
        self.configured(methodology="standard")
        with self.assertRaisesRegex(sdd.SddError,"methodology=sdd"):
            sdd.initialize(self.root,self.fixture("development")["spec"])
        self.configured(methodology="sdd")
        result=sdd.initialize(self.root,self.fixture("development")["spec"])
        self.assertEqual("SPEC_DRAFT",result["status"])
        self.assertTrue((self.root/"aikya/docs/specs/development/SPEC-001/spec.md").is_file())

    def test_all_three_kinds_can_initialize_and_keep_independent_docs(self):
        for kind in sdd.KINDS:
            with self.subTest(kind=kind):
                self.configured(kind)
                out=sdd.initialize(self.root,self.fixture(kind)["spec"])
                self.assertEqual(out["path"],f"aikya/docs/specs/{kind}/SPEC-001")
                status=sdd.status_data(sdd.load(self.root,"SPEC-001")[1])
                self.assertEqual(kind,status["project_type"])
                # Reinicialización, siempre con root temporal nuevo entre modos.
                self.assertTrue(sdd.validate(self.root)["valid"])
        self.assertEqual(3,sdd.validate(self.root)["specifications"])

    def test_spec_gating_clarifications_and_approval(self):
        self.configured()
        f=self.fixture("development")
        sdd.initialize(self.root,f["spec"])
        with self.assertRaisesRegex(sdd.SddError,"Outstanding clarifications"):
            sdd.approve(self.root,"SPEC-001","spec","reviewer")
        with self.assertRaisesRegex(sdd.SddError,"Approve specification"):
            sdd.create_plan(self.root,"SPEC-001",f["plan"])
        sdd.clarify(self.root,"SPEC-001",f["clarify"])
        status=sdd.approve(self.root,"SPEC-001","spec","reviewer")
        self.assertEqual("SPEC_APPROVED",status["phase"])
        with self.assertRaisesRegex(sdd.SddError,"already approved"):
            sdd.approve(self.root,"SPEC-001","spec","reviewer")
        with self.assertRaisesRegex(sdd.SddError,"approved"):
            sdd.clarify(self.root,"SPEC-001",f["clarify"])

    def test_plan_and_tasks_have_separate_approvals(self):
        self.configured()
        f=self.fixture("development")
        sdd.initialize(self.root,f["spec"])
        sdd.clarify(self.root,"SPEC-001",f["clarify"])
        sdd.approve(self.root,"SPEC-001","spec","architect")
        self.assertEqual("PLAN_DRAFT",sdd.create_plan(self.root,"SPEC-001",f["plan"])["phase"])
        with self.assertRaisesRegex(sdd.SddError,"Approve plan"):
            sdd.create_tasks(self.root,"SPEC-001",f["tasks"])
        sdd.approve(self.root,"SPEC-001","plan","architect")
        self.assertEqual("TASKS_DRAFT",sdd.create_tasks(self.root,"SPEC-001",f["tasks"])["phase"])
        with self.assertRaisesRegex(sdd.SddError,"Approve tasks"):
            sdd.progress(self.root,"SPEC-001","TASK-001","done","missing.txt")
        result=sdd.approve(self.root,"SPEC-001","tasks","reviewer")
        self.assertEqual("IMPLEMENTING",result["phase"])

    def test_reject_missing_requirement_and_dependency_cycle(self):
        self.configured()
        f=self.fixture("development")
        sdd.initialize(self.root,f["spec"])
        sdd.clarify(self.root,"SPEC-001",f["clarify"])
        sdd.approve(self.root,"SPEC-001","spec","reviewer")
        sdd.create_plan(self.root,"SPEC-001",f["plan"])
        sdd.approve(self.root,"SPEC-001","plan","reviewer")
        bad={"tasks":[{"id":"TASK-001","description":"bad","requirements":["REQ-999"],"depends_on":[]}]}
        with self.assertRaisesRegex(sdd.SddError,"existing requirements"):
            sdd.create_tasks(self.root,"SPEC-001",bad)
        cyclic={"tasks":[
            {"id":"TASK-001","description":"one","requirements":["REQ-001"],"depends_on":["TASK-002"]},
            {"id":"TASK-002","description":"two","requirements":["REQ-001"],"depends_on":["TASK-001"]}]}
        with self.assertRaisesRegex(sdd.SddError,"Cyclic"):
            sdd.create_tasks(self.root,"SPEC-001",cyclic)

    def test_verify_records_only_real_files_and_all_requirements(self):
        self.configured()
        f=self.fixture("development")
        sdd.initialize(self.root,f["spec"])
        sdd.clarify(self.root,"SPEC-001",f["clarify"])
        sdd.approve(self.root,"SPEC-001","spec","reviewer")
        sdd.create_plan(self.root,"SPEC-001",f["plan"])
        sdd.approve(self.root,"SPEC-001","plan","reviewer")
        sdd.create_tasks(self.root,"SPEC-001",f["tasks"])
        sdd.approve(self.root,"SPEC-001","tasks","reviewer")
        with self.assertRaisesRegex(sdd.SddError,"Missing evidence file"):
            sdd.progress(self.root,"SPEC-001","TASK-001","done","not-found.txt")
        evidence=self.root/"aikya/docs/quality/test-run.txt"
        evidence.parent.mkdir(parents=True,exist_ok=True)
        evidence.write_text("Test passed in an externally executed job\n")
        sdd.progress(self.root,"SPEC-001","TASK-001","done","aikya/docs/quality/test-run.txt")
        with self.assertRaisesRegex(sdd.SddError,"Missing requirement evidence"):
            sdd.verify(self.root,"SPEC-001",{"requirements":[]})
        result=sdd.verify(self.root,"SPEC-001",{"requirements":[{
            "id":"REQ-001","command":"unittest tests.test_order",
            "result":"passed","evidence":"aikya/docs/quality/test-run.txt"}]})
        self.assertEqual("EVIDENCE_RECORDED",result["phase"])
        self.assertFalse(sdd.load(self.root,"SPEC-001")[1]["verification"]["independently_executed"])
        self.assertIn("NOT execute", (self.root/"aikya/docs/specs/development/SPEC-001/verification.md").read_text())
        self.assertTrue(sdd.validate(self.root)["valid"])

    def test_custom_document_not_overwritten(self):
        self.configured()
        folder=self.root/"aikya/docs/specs/development/SPEC-001"
        folder.mkdir(parents=True)
        (folder/"spec.md").write_text("# texto del equipo")
        with self.assertRaisesRegex(sdd.SddError,"already exists"):
            sdd.initialize(self.root,self.fixture("development")["spec"])
        self.assertEqual("# texto del equipo",(folder/"spec.md").read_text())

    def test_evidence_path_cannot_leave_project(self):
        with self.assertRaisesRegex(sdd.SddError,"Path outside"):
            sdd.rel_file(self.root,"../dangerous.json")
        with self.assertRaisesRegex(sdd.SddError,"Path outside"):
            sdd.rel_file(self.root,"/tmp/example.txt")
        external=Path(self.temp.name)/"elsewhere"
        external.mkdir()
        link=self.root/"aikya-link"
        try:
            link.symlink_to(external,target_is_directory=True)
        except (OSError,NotImplementedError):
            return
        with self.assertRaisesRegex(sdd.SddError,"Symlinked"):
            sdd.rel_file(self.root,"aikya-link/file.txt")

    def test_parser_rejects_duplicate_requirements_and_empty_acceptance(self):
        f=self.fixture("development")["spec"]
        f["requirements"][0]["acceptance"]=[]
        with self.assertRaisesRegex(sdd.SddError,"acceptance criteria"):
            sdd.fields_spec(f)
        f=self.fixture("development")["spec"]
        f["requirements"].append(f["requirements"][0])
        with self.assertRaisesRegex(sdd.SddError,"duplicate"):
            sdd.fields_spec(f)

    def test_lint_reports_corrupted_state_instead_of_crashing(self):
        self.configured()
        sdd.initialize(self.root,self.fixture("development")["spec"])
        state=self.root/"aikya/docs/specs/development/SPEC-001/state.json"
        state.write_text('{"id":"SPEC-001","kind":"development","schema":1}')
        result=sdd.validate(self.root)
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])
        self.assertEqual(1,sdd.main(["lint","--root",str(self.root)]))

    def test_status_list_and_lint_cli(self):
        self.configured()
        self.assertEqual(0,sdd.main(["lint","--root",str(self.root)]))
        data=self.fixture("development")["spec"]
        inp=self.root/"input.json"
        inp.write_text(json.dumps(data))
        self.assertEqual(0,sdd.main(["new","--root",str(self.root),"--input",str(inp)]))
        self.assertEqual(0,sdd.main(["list","--root",str(self.root)]))
        self.assertEqual(0,sdd.main(["status","--root",str(self.root),"--id","SPEC-001"]))
        self.assertEqual(2,sdd.main(["plan","--root",str(self.root),"--id","SPEC-001"]))

    def test_installer_includes_script_and_docs_only_if_opted_in(self):
        for kind in sdd.KINDS:
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as d:
                    root=Path(d)
                    source=json.loads((ROOT/"examples"/{"development":"next-react","infrastructure":"infra-terraform-only","devops":"devops-kustomize"}[kind]/"answers.json").read_text())
                    source["methodology"]="sdd"
                    p=install.validated(source,root)
                    install.install(root,p,{"modules":[],"findings":[]})
                    self.assertTrue((root/"aikya/scripts/harness/sdd_engine.py").is_file())
                    self.assertTrue((root/"aikya/docs/specs/README.md").is_file())
                    manifest=json.loads((root/"harness.json").read_text())
                    self.assertIn("sdd:traceability",[x["name"] for x in manifest["checks"]])
                    self.assertFalse((root/"aikya/docs/specs"/kind/"SPEC-001").exists())
                    self.assertTrue((root/".claude/skills/aikya-specify/SKILL.md").exists())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            p=install.validated(json.loads((ROOT/"examples/next-react/answers.json").read_text()),root)
            install.install(root,p,{"modules":[],"findings":[]})
            self.assertFalse((root/"aikya/scripts/harness/sdd_engine.py").exists())
            self.assertFalse((root/"aikya/docs/specs/README.md").exists())

    def test_sdd_blocks_infrastructure_without_approved_tasks(self):
        import importlib.util
        spec=runtime_support.module_spec("sdd_infra_gate",
             ROOT/'src/aikya/resources/project_template/scripts/harness/infrastructure.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module);module=getattr(module,'_module',module)
        p=self.profile("infrastructure")
        self.assertFalse(module.sdd_approved(self.root,p,"SPEC-001","TASK-001"))
        status,notes=module.generate(self.root,p,approved=True,spec_id="SPEC-001",task_id="TASK-001")
        self.assertEqual(2,status)
        self.assertTrue(any("SDD" in n for n in notes))
        f=self.fixture("infrastructure")
        self.configured("infrastructure")
        sdd.initialize(self.root,f["spec"])
        sdd.clarify(self.root,"SPEC-001",f["clarify"])
        sdd.approve(self.root,"SPEC-001","spec","reviewer")
        sdd.create_plan(self.root,"SPEC-001",f["plan"])
        sdd.approve(self.root,"SPEC-001","plan","reviewer")
        sdd.create_tasks(self.root,"SPEC-001",f["tasks"])
        sdd.approve(self.root,"SPEC-001","tasks","reviewer")
        self.assertTrue(module.sdd_approved(self.root,p,"SPEC-001","TASK-001"))
        result,_=module.generate(self.root,p,approved=True,spec_id="SPEC-001",task_id="TASK-001")
        self.assertEqual(0,result)

    def test_sdd_blocks_scaffold_until_tasks_approved(self):
        import importlib.util
        spec=runtime_support.module_spec("sdd_scaffold_gate",
             ROOT/'src/aikya/resources/project_template/scripts/harness/scaffold.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module);module=getattr(module,'_module',module)
        p=self.profile("development")
        self.assertFalse(module.sdd_approved(self.root,p,"SPEC-001","TASK-001"))
        f=self.fixture("development")
        self.configured()
        sdd.initialize(self.root,f["spec"])
        sdd.clarify(self.root,"SPEC-001",f["clarify"])
        sdd.approve(self.root,"SPEC-001","spec","reviewer")
        sdd.create_plan(self.root,"SPEC-001",f["plan"])
        sdd.approve(self.root,"SPEC-001","plan","reviewer")
        sdd.create_tasks(self.root,"SPEC-001",f["tasks"])
        self.assertFalse(module.sdd_approved(self.root,p,"SPEC-001","TASK-001"))
        sdd.approve(self.root,"SPEC-001","tasks","reviewer")
        self.assertTrue(module.sdd_approved(self.root,p,"SPEC-001","TASK-001"))

    def test_upgrade_standard_project_adds_only_sdd_gate_and_backup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            raw=json.loads((ROOT/"examples/next-react/answers.json").read_text())
            standard=install.validated(raw,root)
            install.install(root,standard,{"modules":[],"findings":[]})
            original=root/"harness.json"
            old=json.loads(original.read_text())
            old["checks"].append({"name":"custom:lint","command":["echo","lint"],"cwd":".","required":False})
            original.write_text(json.dumps(old,indent=2)+"\n")
            sdd_profile=install.validated({**raw,"methodology":"sdd"},root)
            install.install(root,sdd_profile,{"modules":[],"findings":[]})
            new=json.loads(original.read_text())
            names=[item["name"] for item in new["checks"]]
            self.assertEqual(1,names.count("sdd:traceability"))
            self.assertIn("custom:lint",names)
            backup=root/".harness/backup-v611/harness.json"
            self.assertTrue(backup.is_file())
            self.assertNotIn("sdd:traceability",backup.read_text())
            install.install(root,sdd_profile,{"modules":[],"findings":[]})
            final=json.loads(original.read_text())
            self.assertEqual(1,sum(i["name"]=="sdd:traceability" for i in final["checks"]))

    def test_catalog_of_sdd_commands_exists(self):
        for name in ("aikya-specify","aikya-clarify","aikya-plan",
                     "aikya-tasks","aikya-implement","aikya-sdd-status"):
            self.assertIn(name,aikya_setup.BOOTSTRAP_COMMANDS)
            skill=ROOT/'src/aikya/resources/commands'/name/"SKILL.md"
            self.assertTrue(skill.is_file(),name)
            self.assertIn("AIKYA BOOTSTRAP MANAGED",skill.read_text())

if __name__=="__main__":unittest.main()
