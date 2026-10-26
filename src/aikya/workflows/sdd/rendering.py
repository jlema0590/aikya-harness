"""Render SDD lifecycle documents from validated records and supplied facts."""
from aikya.documentation.layout import content, stamp
from aikya.workflows.sdd.contracts import MARK, line
from aikya.workflows.sdd.templates import render_sections, source_note

def render_spec(data):
    out=[MARK,"# "+line(data["id"])+" — "+line(data["title"]),"",
         "## Objective","",data["objective"],"","## Requirements and acceptance",""]
    for req in data["requirements"]:
        out.extend(["### "+req["id"],"",req["description"],""])
        out+=["- AC-"+str(i).zfill(2)+": "+v for i,v in enumerate(req["acceptance"],1)]
        out.append("")
    out.extend(["## Nonfunctional requirements",""])
    out+=["- "+x for x in data["nonfunctional"]] or ["- To be agreed"]
    template=data.get('template','spec')
    out+=['',render_sections(template,data.get('sections'),data.get('docs_language','en')), '',source_note(template,data.get('docs_language','en'))]
    return stamp('\n'.join(out))

def render_clarifications(data):
    out=[MARK,"# Clarifications — "+data["id"],"",
         "Unanswered questions prevent specification approval.",""]
    for question in data["spec"]["questions"]:
        out.extend(["## "+line(question),"",data["clarifications"].get(question,"**PENDING**"),""])
    if not data["spec"]["questions"]:
        out.append("No outstanding clarifications.")
    return stamp("\n".join(out))

def render_plan(data):
    plan=data["plan"]
    out=[MARK,"# Execution plan — "+data["id"],"",
         "## Proposed design","",plan["design"],"",
         "## Technical decisions",""]
    out+=["- "+d for d in plan["decisions"]] or ["- No additional decisions"]
    out+=["","## Risks and limitations",""]
    out+=["- "+d for d in plan["risks"]] or ["- To be assessed"]
    out+=["","## Test strategy","",plan["testing"],""]
    return stamp("\n".join(out))

def render_design(data):
    plan=data['plan']
    return stamp('# Design — '+data['id']+'\n\n## Selected approach\n\n'+plan['design']+
                 '\n\n'+render_sections('design',plan.get('sections'),data.get('docs_language','en'))+
                 '\n\n'+source_note('design',data.get('docs_language','en')))

def render_tasks(data):
    out=[MARK,"# Tasks — "+data["id"],"",
         "| Task | Status | Requirements | Dependencies | Evidence |",
         "| --- | --- | --- | --- | --- |"]
    for task in data["tasks"]:
        out.append("| "+task["id"]+" — "+line(task["description"])+" | "+task["status"]+
                   " | "+", ".join(task["requirements"])+" | "+", ".join(task["depends_on"])+
                   " | "+", ".join(task["evidence"])+" |")
    for task in data['tasks']:
        if task.get('sections'):
            out+=['','### '+task['id'], '',render_sections('tasks',task['sections'],data.get('docs_language','en'))]
    out+=['',source_note('tasks',data.get('docs_language','en'))]
    return stamp('\n'.join(out))

def render_verification(data):
    result=data.get("verification") or {}
    out=[MARK,"# SDD verification — "+data["id"],"",
         "**Status:** "+result.get("status","NOT_VERIFIED"),"",
         "The engine checks structure and evidence file existence; it does NOT execute or certify checks.",""]
    for item in result.get("requirements",[]):
        out.extend(["## "+item["id"],"", "- Declared result: "+item["result"],
                    "- Command/check: "+item["command"],
                    "- Evidence file: "+item["evidence"],""])
    if not result.get("requirements"):
        out+=["No accepted evidence has been recorded yet.",""]
    return stamp("\n".join(out))

def render_evidence(data):
    verification=data['verification']
    return stamp(content(render_verification(data)).replace('# SDD verification','# Recorded evidence',1)+
                 '\n\n'+render_sections('evidence',verification.get('sections'),data.get('docs_language','en'))+
                 '\n\n'+source_note('evidence',data.get('docs_language','en')))
