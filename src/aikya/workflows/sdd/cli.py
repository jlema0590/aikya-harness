"""Command-line dispatch for the portable SDD lifecycle; no model execution."""
import argparse
import json
import sys
from pathlib import Path
from aikya.workflows.sdd.contracts import SddError, STAGES, ID_RE, require, read_json, approvals_done
from aikya.workflows.sdd.state import load, load_profile
from aikya.workflows.sdd.templates import catalog, starter
from aikya.workflows.sdd.engine import (
    initialize, clarify, approve, create_plan, create_tasks, progress, verify,
    status_data, require_approved_task, validate_completion, validate, create_document,
)

def main(argv=None):
    parser=argparse.ArgumentParser(description="Aikya Spec-Driven Engineering")
    parser.add_argument("action",choices=("new","clarify","approve","plan","tasks","worklist","progress","verify","status","list","lint","completion","authorize","templates","document"))
    parser.add_argument("--root",type=Path,default=Path.cwd())
    parser.add_argument("--template",choices=tuple(catalog()))
    parser.add_argument("--approved",action="store_true")
    parser.add_argument("--id")
    parser.add_argument("--input",type=Path,help="JSON explicitly reviewed by the user")
    parser.add_argument("--stage",choices=STAGES)
    parser.add_argument("--actor")
    parser.add_argument("--task")
    parser.add_argument("--result",choices=("in_progress","done"))
    parser.add_argument("--evidence",help="Relative path of an existing evidence file")
    args=parser.parse_args(argv)
    root=args.root.expanduser().resolve()
    try:
        require(root.is_dir(),"Project does not exist")
        if args.action=='templates':
            if args.template:
                print(starter(args.template),end='')
            else:print(json.dumps(catalog(),ensure_ascii=False,indent=2))
            return 0
        if args.action=='document':
            require(args.template and args.input,'Document writing requires --template and --input')
            result=create_document(root,args.template,read_json(args.input.resolve()),ident=args.id,approved=args.approved)
        elif args.action=="lint":
            result=validate(root)
        elif args.action=="completion":
            require(args.id, "Completion requires --id")
            errors = validate_completion(root, args.id)
            print(json.dumps({"ready": not errors, "errors": errors, "independently_executed": False}))
            return 1 if errors else 0
        elif args.action=="authorize":
            result = require_approved_task(root, args.id, args.task)
        elif args.action=="list":
            kind,_=load_profile(root)
            base=root/"aikya/docs/specs"/kind
            result={"specifications":sorted(p.name for p in base.iterdir()
                        if p.is_dir() and ID_RE.fullmatch(p.name)) if base.exists() else []}
        else:
            if args.action in ("new","clarify","plan","tasks","verify"):
                require(args.input is not None,"Action requires --input JSON")
                input_data=read_json(args.input.resolve())
            if args.action=="new":
                result=initialize(root,input_data)
            else:
                require(args.id is not None,"Action requires --id SPEC-NNN")
                if args.action=="clarify":result=clarify(root,args.id,input_data)
                elif args.action=="approve":
                    require(args.stage and args.actor,"Approval requires --stage and --actor")
                    result=approve(root,args.id,args.stage,args.actor)
                elif args.action=="plan":result=create_plan(root,args.id,input_data)
                elif args.action=="tasks":result=create_tasks(root,args.id,input_data)
                elif args.action=="progress":
                    require(args.task and args.result,"Progress requires --task and --result")
                    result=progress(root,args.id,args.task,args.result,args.evidence)
                elif args.action=="verify":result=verify(root,args.id,input_data)
                elif args.action=="worklist":
                    folder,data=load(root,args.id)
                    require(approvals_done(data,"tasks"),"Tasks have not been approved")
                    result={"id":args.id,"tasks":data["tasks"],"note":"Implementation requires an authorized agent; this engine does not edit code."}
                else:
                    folder,data=load(root,args.id)
                    result=status_data(data)
        from aikya.middleware.observer import emit_engine_event
        emit_engine_event(root,'sdd',args.action,result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if not (args.action=="lint" and not result["valid"]) else 1
    except (SddError,OSError,UnicodeError,TypeError,ValueError,KeyError) as exc:
        print("ERROR SDD: "+str(exc),file=sys.stderr)
        return 2
