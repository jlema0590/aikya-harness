"""Bounded deterministic lookup with current-source checks before retrieval."""
import json
from aikya.core.checkpoints import safe_file
from .contracts import QueryResult
from .policy import content_hash, excluded, load_policy, read_source
from .scan import ignored
from .store import IndexStore
from .sync import sync


def query(root, text, *, allowed_files=None, max_chars=6000):
    if not isinstance(text, str) or len(text) > 10000 or type(max_chars) is not int or not 1 <= max_chars <= 16000:
        raise ValueError('Invalid bounded code query')
    if allowed_files is not None:
        if not isinstance(allowed_files, list) or len(allowed_files) > 12000:
            raise ValueError('Invalid code query scope')
        for path in allowed_files:
            safe_file(root, path)
    options = load_policy(root)
    if not options.enabled:
        return QueryResult(status='disabled')
    sync(root)
    snapshot = IndexStore(root).read_snapshot()
    result = QueryResult(snapshot.generation, snapshot.status)
    entries = list(snapshot.symbols)
    entries.extend(dict(path=f['path'], name=f['path'], kind='file', file_sha256=f['sha256'],
                        start_line=1, end_line=20) for f in snapshot.files if f['status'] == 'file_only')
    candidates = [s for s in entries if (allowed_files is None or s['path'] in allowed_files)
                  and text.casefold() in (s['name'] + ' ' + s['path']).casefold() and not excluded(s['path'])]
    hidden = ignored(IndexStore(root).root, list({s['path'] for s in candidates}))
    for symbol in sorted(candidates, key=lambda s: (s['path'], s['start_line'], s['name'])):
        if len(result.matches) >= 20:
            result.truncated = True
            break
        if symbol['path'] in hidden:
            continue
        try:
            raw = read_source(root, symbol['path'], options.max_file_bytes)
            if content_hash(raw) != symbol['file_sha256']:
                result.status = 'partial'
                continue
            lines = raw.decode('utf8').splitlines()
        except (OSError, ValueError, UnicodeError):
            result.status = 'partial'
            continue
        snippet = '\n'.join(lines[symbol['start_line'] - 1:min(symbol['end_line'], symbol['start_line'] + 19)])[:2000]
        entry = {**symbol, 'snippet': snippet}
        chunk = json.dumps(entry, ensure_ascii=False) + '\n'
        remaining = max_chars - len(result.context)
        if remaining <= 0:
            result.truncated = True
            break
        result.matches.append(entry)
        result.context += chunk[:remaining]
        result.truncated |= len(chunk) > remaining
    return result
