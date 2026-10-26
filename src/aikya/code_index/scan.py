"""Bounded candidate inventory; no project imports, tools or symlink traversal."""
import os
import shutil
import subprocess
from pathlib import Path
from .policy import CODE_SUFFIXES, excluded, project_root


def ignored(root, names):
    if not names or not (root / '.git').exists():
        return set()
    if not shutil.which('git'):
        raise ValueError('Git unavailable; cannot safely apply repository ignore rules')
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', 'check-ignore',
                             '--no-index', '-z', '--stdin'], cwd=root,
                            input=b'\0'.join(n.encode('utf8') for n in names) + b'\0',
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
    if result.returncode not in (0, 1):
        raise ValueError('Repository ignore rules could not be verified')
    return set(result.stdout.decode('utf8').strip('\0').split('\0'))


def inventory(root, options, *, documents=False):
    root = project_root(root)
    focus = root / options.scope
    stack = [focus]
    docs = root / 'aikya/docs'
    if documents and focus != root and docs.is_dir() and not docs.is_relative_to(focus):
        stack.append(docs)
    paths, diagnostics = [], []
    examined = 0
    while stack:
        folder = stack.pop()
        if folder != root and (folder / '.git').exists():
            continue
        try:
            with os.scandir(folder) as listing:
                entries = []
                for entry in listing:
                    examined += 1
                    if examined > options.max_files * 10:
                        return sorted(paths), diagnostics + ['inventory_limit']
                    if not entry.is_symlink():
                        entries.append(Path(entry.path))
            entries.sort()
            candidates = [p for p in entries if not excluded(p.relative_to(root).as_posix())]
            hidden = ignored(root, [p.relative_to(root).as_posix() for p in candidates])
        except (OSError, ValueError, subprocess.SubprocessError, UnicodeError):
            diagnostics.append('inventory_unavailable:' + folder.relative_to(root).as_posix())
            continue
        for path in reversed(candidates):
            relative = path.relative_to(root).as_posix()
            if relative in hidden:
                continue
            if path.is_dir():
                stack.append(path)
            elif path.is_file() and (path.suffix.lower() in CODE_SUFFIXES or
                    (documents and path.suffix.lower() == '.md' and relative.startswith('aikya/docs/')
                     and relative != 'aikya/docs/indice.md')):
                paths.append(relative)
                if len(paths) >= options.max_files:
                    return sorted(paths), diagnostics + ['file_limit']
    return sorted(paths), diagnostics
