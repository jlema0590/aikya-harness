"""Known pre-package source hashes captured from reviewed repository baselines."""
import json
from pathlib import Path
from aikya.resource_paths import source_path


def predecessor_hashes(source, relative):
    path = source_path(source, 'migrations/structure-predecessors.json')
    data = json.loads(path.read_text(encoding='utf8'))
    name = Path(relative).name
    values = data.get(name, [])
    if not isinstance(values, list) or any(not isinstance(v, str) or len(v) != 64 for v in values):
        raise ValueError('Invalid structural migration signatures')
    return set(values)
