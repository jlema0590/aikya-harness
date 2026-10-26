"""Hash-driven replacement of file declarations in one writer transaction."""
from dataclasses import asdict
from bisect import bisect_left
import json
from aikya.core.state import locked
from .contracts import ParsedFile, SyncResult
from .policy import content_hash, load_policy, read_source
from .scan import inventory
from .store import IndexStore
from .parsers.registry import parse_file, parser_version


def sync(root, *, full=False):
    options = load_policy(root)
    if not options.enabled:
        return SyncResult()
    store = IndexStore(root)
    store.path.parent.mkdir(parents=True, exist_ok=True)
    with locked(store.path.parent):
        previous = store.read_snapshot()
        old = {f['path']: f for f in previous.files}
        paths, diagnostics = inventory(store.root, options)
        with store.connect() as connection:
            metadata = dict(connection.execute('SELECT key,value FROM meta')) if connection else {}
        offset = bisect_left(paths, metadata.get('next_path', '')) % max(1, len(paths))
        ordered = paths[offset:] + paths[:offset]
        result = SyncResult(previous.generation, 'complete', diagnostics=diagnostics)
        records = []
        seen = set()
        next_path = ''
        for path in ordered:
            seen.add(path)
            try:
                size = (store.root / path).stat().st_size
                if size > min(options.max_file_bytes, options.max_sync_bytes):
                    record = ParsedFile(path, '', 'oversized')
                    result.skipped_files += 1
                elif result.verified_bytes + size > options.max_sync_bytes:
                    if not next_path:
                        next_path = path
                    result.skipped_files += 1
                    # Previously verified declarations retain their hash, never a
                    # freshness claim. Consumers still check selected source bytes.
                    if path in old:
                        continue
                    record = ParsedFile(path, '', 'not_revalidated')
                else:
                    raw = read_source(store.root, path, options.max_file_bytes)
                    result.verified_bytes += len(raw)
                    digest = content_hash(raw)
                    before = old.get(path)
                    if before and before['sha256'] == digest and (before['parser_id'], before['parser_version']) == parser_version(path):
                        continue
                    record = parse_file(path, raw)
                    result.parsed_files += int(record.parser_id != 'inventory')
            except (OSError, ValueError):
                record = ParsedFile(path, '', 'not_revalidated')
                result.skipped_files += 1
            metadata_only = asdict(record)
            for table in ('symbols', 'imports', 'relations'):
                metadata_only.pop(table)
            if metadata_only != old.get(path):
                records.append(record)
        removed = set(old) - seen
        # Incomplete inventories cannot prove absence, so invalidate remaining paths.
        if diagnostics:
            records.extend(ParsedFile(p, '', 'not_revalidated') for p in removed)
            removed = set()
        statuses = {p: f['status'] for p, f in old.items() if p in seen}
        statuses.update({r.path: r.status for r in records})
        if diagnostics or result.skipped_files or any(s not in ('indexed', 'file_only') for s in statuses.values()):
            result.status = 'partial'
        changed = bool(records or removed or result.status != previous.status)
        if not changed:
            if metadata.get('next_path', '') != next_path:
                with store.connect(write=True) as connection:
                    connection.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', ('next_path', next_path))
            return result
        with store.connect(write=True) as connection:
            for path in removed | {r.path for r in records}:
                for table in ('symbols', 'imports', 'relations', 'files'):
                    connection.execute(f'DELETE FROM {table} WHERE path=?', (path,))
            for record in records:
                value = asdict(record)
                for table in ('symbols', 'imports', 'relations'):
                    for number, item in enumerate(value.pop(table)):
                        connection.execute(f'INSERT INTO {table} VALUES (?,?,?)',
                                           (record.path + ':' + str(number), record.path, json.dumps(item)))
                connection.execute('INSERT INTO files VALUES (?,?,?)', (record.path, record.path, json.dumps(value)))
            result.generation += 1
            connection.execute('UPDATE meta SET value=? WHERE key=?', (str(result.generation), 'generation'))
            connection.execute('UPDATE meta SET value=? WHERE key=?', (result.status, 'status'))
            connection.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', ('next_path', next_path))
        return result
