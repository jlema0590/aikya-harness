"""Scoped maintainability checks; these diagnostics are not a security scanner."""
from __future__ import annotations
import argparse,ast,hashlib,json,os,subprocess
from pathlib import Path
from aikya.core.checkpoints import safe_file

SOURCE_SUFFIXES={'.py','.js','.jsx','.ts','.tsx','.c','.h','.cpp','.cc','.hpp','.go','.rs','.java','.kt','.kts','.swift','.cs','.rb','.php','.sh','.ps1','.vue','.svelte','.tf','.hcl','.sql','.yaml','.yml'}
EXCLUDED={'.git','.venv','venv','node_modules','vendor','dist','build','__pycache__','aikya-template'}


def _exceptions(root):
    path=safe_file(root,'.aikya/code-quality-exceptions.json')
    if not path.exists():return {}
    if path.stat().st_size>100000:raise ValueError('Oversized code quality exception file')
    data=json.loads(path.read_text())
    if not isinstance(data,dict) or set(data)!={'schema','exceptions'} or type(data['schema']) is not int or data['schema']!=1 or not isinstance(data['exceptions'],list):raise ValueError('Invalid code quality exception schema')
    result={}
    for item in data['exceptions']:
        if not isinstance(item,dict) or set(item)!={'path','sha256','reason'}:raise ValueError('Invalid code quality exception')
        safe_file(root,item['path'])
        if not isinstance(item['reason'],str) or len(item['reason'].strip())<20 or len(item['reason'])>1000:raise ValueError('Exception needs a review rationale (20–1,000 characters)')
        if not isinstance(item['sha256'],str) or len(item['sha256'])!=64 or any(c not in '0123456789abcdef' for c in item['sha256']) or item['path'] in result:raise ValueError('Invalid or duplicate exception fingerprint')
        result[item['path']]=item
    return result


def inspect_paths(root,paths):
    root=Path(root).absolute();exceptions=_exceptions(root);errors=[];warnings=[];bodies={};count=0
    for name in sorted(set(paths)):
        path=safe_file(root,name)
        if not path.exists() or path.suffix.lower() not in SOURCE_SUFFIXES:continue
        count+=1
        if path.stat().st_size>10_000_000:raise ValueError('Source exceeds 10 MB inspection limit')
        raw=path.read_bytes();text=raw.decode('utf8');lines=text.splitlines()
        if len(lines)>1000:
            item={'path':name,'line':1,'code':'file_too_large','message':str(len(lines))+' lines: split by responsibility; maximum is 1,000 physical lines.'}
            exception=exceptions.get(name)
            if exception and exception['sha256']==hashlib.sha256(raw).hexdigest():warnings.append({**item,'code':'reviewed_size_exception','reason':exception['reason']})
            else:errors.append(item)
        if path.suffix.lower()!='.py':continue
        try:tree=ast.parse(text,filename=name)
        except SyntaxError as exc:
            errors.append({'path':name,'line':exc.lineno,'code':'python_syntax','message':exc.msg});continue
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
            length=node.end_lineno-node.lineno+1
            location={'path':name,'line':node.lineno,'function':node.name}
            if length>100:warnings.append({**location,'code':'long_function','message':str(length)+' lines: review cohesion and extract focused helpers where justified.'})
            significant=sum(bool(s.strip()) and not s.lstrip().startswith('#') for s in lines[node.lineno:node.end_lineno])
            if significant<10:continue
            # Exact AST bodies only: no claim about semantic equivalence or other languages.
            key=ast.dump(ast.Module(body=node.body,type_ignores=[]),include_attributes=False)
            bodies.setdefault(key,[]).append(location)
    duplicates=[items for items in bodies.values() if len(items)>1]
    for group in duplicates:warnings.append({'code':'duplicate_python_body','message':'Repeated nontrivial Python function body; review a shared implementation.','locations':group})
    return {'files':count,'errors':errors,'warnings':warnings,'duplicates':duplicates}


def source_paths(root):
    root=Path(root).absolute();result=[]
    for base,dirs,files in os.walk(root,followlinks=False):
        relative=Path(base).relative_to(root)
        dirs[:]=[d for d in dirs if d not in EXCLUDED and not (Path(base)/d).is_symlink()]
        if relative.parts[:2] in (('aikya','docs'),('examples','documentation')):dirs[:]=[];continue
        for name in files:
            path=Path(base)/name
            if path.suffix.lower() in SOURCE_SUFFIXES and not path.is_symlink():result.append(path.relative_to(root).as_posix())
    return sorted(result)


def changed_paths(root,base='HEAD'):
    def git(*args):
        return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,text=True,timeout=20).stdout.split('\x00')
    return sorted(set(p for p in git('diff','--name-only','-z',base,'--')+git('ls-files','--others','--exclude-standard','-z') if p))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--all',action='store_true');p.add_argument('--changed',action='store_true');p.add_argument('--base',default='HEAD');p.add_argument('paths',nargs='*');a=p.parse_args(argv)
    try:
        if sum((a.all,a.changed,bool(a.paths)))!=1:raise ValueError('Choose explicit paths, --all or --changed')
        paths=source_paths(a.root) if a.all else changed_paths(a.root,a.base) if a.changed else a.paths
        result=inspect_paths(a.root,paths);print(json.dumps(result,ensure_ascii=False,indent=2));return 1 if result['errors'] else 0
    except (ValueError,OSError,subprocess.SubprocessError) as exc:print(json.dumps({'error':str(exc)}));return 2
if __name__=='__main__':raise SystemExit(main())
