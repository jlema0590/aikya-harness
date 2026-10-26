#!/usr/bin/env python3
"""Portable SDD transitions and public compatibility facade.

Storage, validation, rendering and CLI dispatch have focused modules. This engine
records authorized workflow; it never generates application code or deploys.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from aikya.documentation.layout import content, generated, stamp, safe, index_paths, update_index, write_document
from aikya.workflows.sdd.templates import SPEC_TEMPLATES, catalog, normalize_sections, render_sections, source_note, starter
from aikya.workflows.sdd.contracts import (
    KINDS, ID_RE, REQ_RE, TASK_RE, STAGES, MARK, SddError,
    require, clean, line, items, rel_file, location, read_json, fields_spec, approvals_done,
)
from aikya.workflows.sdd.state import load_profile, load, save
from aikya.workflows.sdd.validation import validate_state
from aikya.workflows.sdd.rendering import (
    render_spec, render_clarifications, render_plan, render_design, render_tasks,
    render_verification, render_evidence,
)

def initialize(root,input_data):
    kind,profile=load_profile(root)
    require(profile.get("methodology","standard")=="sdd",
            "Enable methodology=sdd explicitly through onboarding or a reviewed profile")
    spec=fields_spec(input_data)
    folder=location(root,kind,spec["id"])
    require(not folder.exists(),"Specification already exists: "+spec["id"])
    from aikya.documentation.language import read as read_docs_language
    language = read_docs_language(root) or "en"
    data={"schema":1,"docs_language":language,"id":spec["id"],"kind":kind,"spec":spec,
          "clarifications":{},"approvals":{},"plan":None,"tasks":[],
          "verification":None}
    files={'spec.md':render_spec({**spec,'docs_language':language})}
    if spec['questions']:files['clarifications.md']=render_clarifications(data)
    save(root,folder,data,files)
    return {"id":spec["id"],"status":"SPEC_DRAFT","path":str(folder.relative_to(root))}

def clarify(root,ident,answers):
    folder,data=load(root,ident)
    require("spec" not in data["approvals"],"Specification approved: create a new specification to change it")
    require(isinstance(answers.get("answers"),dict),"answers must map questions to answers")
    requested=set(data["spec"]["questions"])
    for question,answer in answers["answers"].items():
        require(question in requested,"Unknown question: "+question)
        data["clarifications"][question]=clean(answer,"answer",2000)
    save(root,folder,data,{'clarifications.md':render_clarifications(data)} if data['spec']['questions'] else {})
    return status_data(data)

def approve(root,ident,stage,actor):
    require(stage in STAGES,"Unknown stage")
    folder,data=load(root,ident)
    actor=clean(actor,"actor",120)
    require(not approvals_done(data,stage),"Stage already approved")
    if stage=="spec":
        outstanding=[q for q in data["spec"]["questions"] if q not in data["clarifications"]]
        require(not outstanding,"Outstanding clarifications: "+str(len(outstanding)))
    elif stage=="plan":
        require(approvals_done(data,"spec") and data["plan"] is not None,
                "Approved specification and complete plan are required")
    elif stage=="tasks":
        require(approvals_done(data,"plan") and data["tasks"],
                "Approved plan and defined tasks are required")
    data["approvals"][stage]={"actor":actor,"approved":True}
    save(root,folder,data,{})
    return status_data(data)

def create_plan(root,ident,raw):
    folder,data=load(root,ident)
    require(approvals_done(data,"spec"),"Approve specification before planning")
    require(not approvals_done(data,"plan"),"Approved plan cannot be modified")
    plan={"design":clean(raw.get("design"),"design"),
          "decisions":[clean(s,"decision") for s in items(raw.get("decisions",[]),"decisions")],
          "risks":[clean(s,"risk") for s in items(raw.get("risks",[]),"risks")],
          "testing":clean(raw.get("testing"),"testing")}
    if "sections" in raw:plan["sections"]=normalize_sections("design",raw["sections"])
    data["plan"]=plan
    save(root,folder,data,{"design.md":render_design(data),"plan.md":render_plan(data)})
    return status_data(data)

def create_tasks(root,ident,raw):
    folder,data=load(root,ident)
    require(approvals_done(data,"plan"),"Approve plan before defining tasks")
    require(not approvals_done(data,"tasks"),"Approved tasks cannot be modified")
    rawtasks=items(raw.get("tasks"),"tasks")
    require(0<len(rawtasks)<=120,"Between 1 and 120 tasks are required")
    tasks=[]
    seen=set()
    valid_req={r["id"] for r in data["spec"]["requirements"]}
    for entry in rawtasks:
        require(isinstance(entry,dict),"Task must be an object")
        key=clean(entry.get("id"),"task.id",25)
        require(bool(TASK_RE.fullmatch(key)) and key not in seen,"Invalid or duplicate task ID")
        seen.add(key)
        refs=items(entry.get("requirements"),"task.requirements")
        require(bool(refs) and set(refs).issubset(valid_req),"Task must reference existing requirements")
        deps=items(entry.get("depends_on",[]),"depends_on")
        require(all(isinstance(dep,str) and bool(TASK_RE.fullmatch(dep)) for dep in deps),
                "Invalid dependencies")
        tasks.append({"id":key,"description":clean(entry.get("description"),"description",1500),
                      "requirements":refs,"depends_on":deps,"status":"todo","evidence":[],
                      **({"sections":normalize_sections("tasks",entry["sections"])} if "sections" in entry else {})})
    byid={t["id"]:t for t in tasks}
    require(all(set(t["depends_on"]).issubset(byid) and t["id"] not in t["depends_on"]
                for t in tasks),"Circular or missing dependency")
    def visit(key,stack,visited):
        require(key not in stack,"Cyclic dependencies")
        if key in visited:return
        for dep in byid[key]["depends_on"]:visit(dep,stack|{key},visited)
        visited.add(key)
    seen_walk=set()
    for key in byid:visit(key,set(),seen_walk)
    covered={x for t in tasks for x in t["requirements"]}
    require(covered==valid_req,"Every requirement needs at least one task; missing: "+", ".join(sorted(valid_req-covered)))
    data["tasks"]=tasks
    save(root,folder,data,{"tasks.md":render_tasks(data)})
    return status_data(data)

def progress(root,ident,task_id,result,evidence):
    folder,data=load(root,ident)
    require(approvals_done(data,"tasks"),"Approve tasks before implementation")
    task=next((t for t in data["tasks"] if t["id"]==task_id),None)
    require(task is not None,"Task not found")
    require(result in ("in_progress","done"),"Allowed status is in_progress or done")
    byid={t["id"]:t for t in data["tasks"]}
    require(all(byid[d]["status"]=="done" for d in task["depends_on"]),
            "Complete task dependencies first")
    if result=="done":
        require(evidence,"Completing a task requires an existing evidence file")
        rel_file(root,evidence,must_exist=True)
        task["evidence"]=sorted(set(task["evidence"]+[evidence]))
    task["status"]=result
    # A task change invalidates the previous verification record.
    data["verification"]=None
    save(root,folder,data,{"tasks.md":render_tasks(data)},verification_invalidated=True)
    return status_data(data)

def verify(root,ident,raw):
    folder,data=load(root,ident)
    require(approvals_done(data,"tasks"),"Tasks are not approved")
    require(all(t["status"]=="done" for t in data["tasks"]),
            "Tasks are incomplete")
    entries=items(raw.get("requirements"),"verification.requirements")
    expected={r["id"] for r in data["spec"]["requirements"]}
    seen=set()
    verified=[]
    for entry in entries:
        require(isinstance(entry,dict),"Result must be an object")
        key=clean(entry.get("id"),"verification.id",25)
        require(key in expected and key not in seen,"Invalid or duplicate evidence ID")
        seen.add(key)
        command=clean(entry.get("command"),"verification.command",800)
        result=entry.get("result")
        require(result in ("passed","failed"),"Declared result must be passed/failed")
        evidence=clean(entry.get("evidence"),"verification.evidence",240)
        rel_file(root,evidence,must_exist=True)
        verified.append({"id":key,"command":command,"result":result,"evidence":evidence})
    require(seen==expected,"Missing requirement evidence: "+", ".join(sorted(expected-seen)))
    complete=all(e["result"]=="passed" for e in verified)
    data["verification"]={"status":"EVIDENCE_RECORDED" if complete else "FAILED",
                          "requirements":verified,"independently_executed":False}
    if 'sections' in raw:data['verification']['sections']=normalize_sections('evidence',raw['sections'])
    save(root,folder,data,{'verification.md':render_verification(data),'evidence.md':render_evidence(data)})
    return status_data(data)

def status_data(data):
    approvals=data["approvals"]
    if data.get("verification"):
        step=data["verification"]["status"]
    elif "tasks" in approvals:
        step="IMPLEMENTING"
    elif data["tasks"]:
        step="TASKS_DRAFT"
    elif "plan" in approvals:
        step="PLAN_APPROVED"
    elif data["plan"] is not None:
        step="PLAN_DRAFT"
    elif "spec" in approvals:
        step="SPEC_APPROVED"
    else:step="SPEC_DRAFT"
    return {"id":data["id"],"project_type":data["kind"],
            "phase":step,"approved":sorted(approvals),
            "outstanding_questions":len([q for q in data["spec"]["questions"]
                                         if q not in data["clarifications"]]),
            "total_tasks":len(data["tasks"]),
            "completed_tasks":len([t for t in data["tasks"] if t["status"]=="done"]),
            "requirements":len(data["spec"]["requirements"])}

def require_approved_task(root, spec_id, task_id):
    """Authorize a specific ready task, never any historical project approval."""
    require(spec_id and task_id, "SDD requires --spec-id and --task-id")
    folder, data = load(root, spec_id)
    require(all(approvals_done(data, stage) for stage in STAGES), "Specification, plan and tasks must be approved")
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    require(task is not None, "Task not found in active specification")
    byid = {t["id"]: t for t in data["tasks"]}
    require(all(byid[d]["status"] == "done" for d in task["depends_on"]), "Complete task dependencies first")
    return task

def validate_completion(root, spec_id):
    """Check recorded completion; this never executes or certifies external tests."""
    try:
        folder, data = load(root, spec_id)
        require(all(approvals_done(data, stage) for stage in STAGES), "All stages require approval")
        require(bool(data["tasks"]) and all(t["status"] == "done" for t in data["tasks"]), "Incomplete tasks")
        require(data.get("verification") and data["verification"]["status"] == "EVIDENCE_RECORDED", "Passing requirement evidence is missing")
        for task in data["tasks"]:
            for path in task["evidence"]: rel_file(root, path, must_exist=True)
        for entry in data["verification"]["requirements"]: rel_file(root, entry["evidence"], must_exist=True)
        return []
    except (ValueError, OSError, TypeError, KeyError) as exc:
        return [str(exc)]

def validate(root):
    base=root/"aikya/docs/specs"
    try:
        rel_file(root, "aikya/docs/specs")
    except ValueError as exc:
        return {"valid":False,"specifications":0,"errors":[str(exc)]}
    if not base.exists(): return {"valid":True,"specifications":0,"errors":[]}
    errors=[];count=0
    for directory in base.glob("*/*"):
        if not directory.is_dir() and not directory.is_symlink(): continue
        file = directory/"state.json"
        count+=1
        try:
            ident=file.parent.name;kind=file.parent.parent.name
            folder=location(root,kind,ident)
            rel_file(root, file.relative_to(root).as_posix(), must_exist=True)
            data=read_json(file)
            require(data.get("id")==ident and data.get("kind")==kind, "Specification location mismatch")
            require(not validate_state(data), "; ".join(validate_state(data)))
            documents=['spec.md']
            if data['spec']['questions']:documents.append('clarifications.md')
            if data.get('verification'):documents.append('verification.md')
            for name in documents:
                rel_file(root, (folder/name).relative_to(root).as_posix(), must_exist=True)
            if data["plan"] is not None:
                for name in ("plan.md", "design.md"): rel_file(root, (folder/name).relative_to(root).as_posix(), must_exist=True)
            if data["tasks"]: rel_file(root, (folder/"tasks.md").relative_to(root).as_posix(), must_exist=True)
            for task in data["tasks"]:
                for path in task["evidence"]:rel_file(root,path,must_exist=True)
            if data.get("verification"):
                for item in data["verification"]["requirements"]:rel_file(root,item["evidence"],must_exist=True)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            errors.append(str(file)+": "+str(exc))
    return {"valid":not errors,"specifications":count,"errors":errors}

def create_document(root, template, raw, *, ident=None, approved=False):
    require(approved,'Writing a template document requires explicit approval')
    require(template in ('review','constitution'),'Only review and constitution are auxiliary documents')
    kind,profile=load_profile(root)
    require(profile.get('methodology')=='sdd','SDD must be explicitly enabled')
    sections=normalize_sections(template,raw.get('sections'))
    require(bool(sections),'No document is created without reviewed content')
    if template=='review':
        require(ident,'A review requires the specification ID')
        folder,data=load(root,ident)
        relative=(folder/'review.md').relative_to(root/'aikya/docs').as_posix()
    else:
        require(not ident,'The constitution applies to the project, not one specification')
        relative='specs/constitution.md'
    from aikya.documentation.language import resolve
    locale=resolve(root)
    title={'review':('Specification review','Revisión de especificación'),
           'constitution':('Engineering constitution','Constitución de ingeniería')}[template][locale=='es']
    note='This document records reviewed content; it does not approve an SDD stage.' if locale=='en' else 'Este documento registra contenido revisado; no aprueba etapas SDD.'
    body='# '+title+(' — '+ident if ident else '')+'\n\n'+note+'\n\n'+render_sections(template,sections,locale)+'\n\n'+source_note(template,locale)
    return {'path':write_document(root,relative,body,replace_generated=True),'approval_recorded':False}


def main(argv=None):
    from aikya.workflows.sdd.cli import main as dispatch
    return dispatch(argv)


if __name__ == '__main__':
    sys.exit(main())
