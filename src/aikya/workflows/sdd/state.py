"""Load and persist SDD dossiers while preserving document ownership and locale."""
import json
from aikya.documentation.layout import generated, stamp, index_paths, update_index
from aikya.workflows.sdd.contracts import KINDS, require, location, rel_file, read_json
from aikya.workflows.sdd.validation import validate_state

def load_profile(root):
    info=read_json(root/".harness/project-profile.json")
    profile=info.get("decisions",info)
    require(isinstance(profile,dict),"Invalid Aikya profile")
    kind=profile.get("project_type","development")
    require(kind in KINDS,"Invalid project type")
    return kind,profile

def load(root,ident):
    kind,profile=load_profile(root)
    folder=location(root,kind,ident)
    rel_file(root, (folder/"state.json").relative_to(root).as_posix(), must_exist=True)
    require(profile.get("methodology", "standard") == "sdd", "SDD must be explicitly enabled")
    data=read_json(folder/"state.json")
    require(data.get("id")==ident and data.get("kind")==kind and data.get("schema")==1,
            "SDD state is incompatible with the project")
    errors = validate_state(data)
    require(not errors, "; ".join(errors))
    return folder,data

def save(root,folder,data,files,*,verification_invalidated=False):
    # Validate all destinations before writing; preserve unowned documents.
    require(not validate_state(data), "; ".join(validate_state(data)))
    if data.get("docs_language") == "es":
        from aikya.workflows.sdd.localization import localize_sdd
        files = {name: localize_sdd(body) for name, body in files.items()}
    index_paths(root)
    from aikya.documentation.language import resolve
    resolve(root)  # Validate the policy before any document changes.
    destinations={folder/name:stamp(body) for name,body in files.items()}
    if verification_invalidated and data.get('verification') is None:
        for name in ('verification.md','evidence.md'):
            target=folder/name
            if target in destinations and not target.exists():destinations.pop(target)
            elif target.exists():
                body='# Verification invalidated — '+data['id']+'\n\nTask progress changed; previous results are no longer current. Re-run and record the relevant checks before claiming completion.'
                if data.get('docs_language')=='es':body=localize_sdd(body)
                destinations[target]=stamp(body)
    destinations[folder/"state.json"]=json.dumps(data,indent=2,ensure_ascii=False)+"\n"
    for target,body in destinations.items():
        rel=target.relative_to(root).as_posix()
        rel_file(root,rel)
        if target.exists():
            current=target.read_text(encoding="utf-8")
            if target.name!="state.json":
                require(generated(current),"Customized document is protected: "+rel)
            else:
                require(json.loads(current).get("id")==data["id"],
                        "Unmanaged existing SDD state: "+rel)
    for target in destinations:
        temporary=target.with_name(target.name+'.aikya-tmp')
        require(not temporary.exists() and not temporary.is_symlink(),'Temporary file already exists: '+str(temporary))
    folder.mkdir(parents=True,exist_ok=True)
    for target,body in destinations.items():
        target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_name(target.name+".aikya-tmp")
        require(not temp.exists() and not temp.is_symlink(),"Temporary file already exists: "+str(temp))
        try:
            temp.write_text(body,encoding="utf-8")
            temp.replace(target)
        finally:
            if temp.exists():temp.unlink()
    update_index(root)
