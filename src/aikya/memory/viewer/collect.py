"""Read existing notes, documents and a single index generation without mutation."""
from pathlib import Path
import re
import time
from urllib.parse import unquote
from aikya.core.checkpoints import safe_file
from aikya.memory.knowledge import inspect_notes
from aikya.code_index.policy import content_hash, load_policy, read_source, project_root
from aikya.code_index.scan import inventory
from aikya.code_index.store import IndexStore
from .contracts import MemorySnapshot, ViewerOptions, encoded_snapshot
from .graph import add_structure, edge, symbol_id


def collect_snapshot(root, *, options=None, now=None):
    root = project_root(root)
    options = options or ViewerOptions()
    when = time.time() if now is None else now
    snapshot = MemorySnapshot(generated_at=when, project=root.name)
    policy = load_policy(root)
    paths, diagnostics = inventory(root, policy, documents=True)
    eligible = set(paths)
    snapshot.diagnostics.extend(diagnostics)
    snapshot.coverage = {'code_index': 'missing', 'documents': 'available', 'notes': 'available'}
    snapshot.nodes.append({'id': 'project:root', 'type': 'project', 'label': root.name,
                           'path': '.', 'source_hash': None, 'status': 'derived', 'details': {}})
    total_bytes, cache = 0, {}

    def read(path, limit):
        nonlocal total_bytes
        if path not in cache:
            size = safe_file(root, path).stat().st_size
            if size > limit or total_bytes + size > options.max_input_bytes:
                raise ValueError('Viewer input limit')
            raw = read_source(root, path, limit)
            total_bytes += len(raw)
            cache[path] = raw
        return cache[path]

    if policy.enabled:
        try:
            index = IndexStore(root).read_snapshot()
            snapshot.index_generation = index.generation
            snapshot.coverage['code_index'] = 'available' if index.status == 'complete' else index.status
            verified = {}
            for file in index.files:
                path = file['path']
                if path not in eligible:
                    continue
                try:
                    current = content_hash(read(path, policy.max_file_bytes))
                    verified[path] = current == file['sha256'] and file['status'] in ('indexed', 'file_only')
                except (OSError, ValueError):
                    verified[path] = False
                status = file['status'] if verified[path] else 'not_revalidated'
                if not verified[path]:
                    snapshot.coverage['code_index'] = 'partial'
                snapshot.nodes.append({'id': 'file:' + path, 'type': 'file', 'label': Path(path).name,
                                       'path': path, 'source_hash': file['sha256'], 'status': status,
                                       'details': {'parser': file['parser_id'], 'coverage': file['status']}})
            for symbol in index.symbols:
                path = symbol['path']
                if not verified.get(path):
                    continue
                snapshot.nodes.append({'id': symbol_id(symbol), 'type': symbol['kind'], 'label': symbol['qualified_name'],
                                       'path': path, 'source_hash': symbol['file_sha256'], 'status': 'current', 'details': symbol})
                snapshot.edges.append(edge('file:' + path, symbol_id(symbol), 'contains', path=path, line=symbol['start_line']))
            by_name = {(s['path'], s['qualified_name']): symbol_id(s) for s in index.symbols if verified.get(s['path'])}
            for relation in index.relations:
                source = by_name.get((relation['path'], relation['source']))
                target = by_name.get((relation['path'], relation['target']))
                if source and target:
                    snapshot.edges.append(edge(source, target, relation['relation'], path=relation['path'], line=relation['line']))
        except (OSError, ValueError):
            snapshot.coverage['code_index'] = 'invalid'
            snapshot.diagnostics.append('code_index_unavailable')
    notes = inspect_notes(root, now=when, limit=options.max_notes, max_input_bytes=options.max_input_bytes)
    if notes.omitted_count or notes.diagnostics:
        snapshot.coverage['notes'] = 'partial'
    note_paths = set()
    for note in notes.notes:
        if note['path'] not in eligible:
            continue
        note_paths.add(note['path'])
        snapshot.nodes.append({'id': 'memory:' + note['id'], 'type': 'memory', 'label': note['kind'] + ' · ' + note['id'][:8],
                               'path': note['path'], 'source_hash': note['source_hash'], 'status': note['source_status'], 'details': note})
    documents = [p for p in paths if p.startswith('aikya/docs/') and p.endswith('.md')
                 and not p.startswith('aikya/docs/memory/') and p not in note_paths]
    if len(documents) > options.max_documents or diagnostics:
        snapshot.coverage['documents'] = 'partial'
    pending_links = []
    for path in documents[:options.max_documents]:
        try:
            raw = read(path, options.max_document_bytes)
            text = raw.decode('utf8')
        except (OSError, UnicodeError, ValueError):
            snapshot.coverage['documents'] = 'partial'
            continue
        heading = re.search(r'^#\s+(.+)$', text, re.M)
        snapshot.nodes.append({'id': 'document:' + path, 'type': 'document', 'label': heading[1][:160] if heading else Path(path).name,
                               'path': path, 'source_hash': content_hash(raw), 'status': 'current',
                               'details': {'excerpt': text[:options.max_excerpt_chars]}})
        for target in re.findall(r'\]\(([^)]+)\)', text)[:200]:
            value = unquote(target.split('#')[0])
            if not value or ':' in value or '\\' in value or value.startswith('/'):
                continue
            candidate = (root / path).parent / value
            try:
                relative = candidate.resolve().relative_to(root).as_posix()
                safe_file(root, relative)
                pending_links.append(('document:' + path, relative))
            except ValueError:
                continue
    by_path = {n['path']: n['id'] for n in snapshot.nodes if n['type'] in ('file', 'document', 'memory')}
    for source, target in pending_links:
        if target in by_path:
            snapshot.edges.append(edge(source, by_path[target], 'references', path=target, provenance='markdown'))
    for note in notes.notes:
        if note['path'] in note_paths and note['source'] in by_path:
            snapshot.edges.append(edge('memory:' + note['id'], by_path[note['source']], 'references', path=note['source'], provenance='note_source'))
    add_structure(snapshot)
    snapshot.counts = {'eligible_nodes': len(snapshot.nodes), 'eligible_edges': len(snapshot.edges),
                       'omitted_notes': notes.omitted_count, 'verified_bytes': total_bytes}
    snapshot.diagnostics.extend(notes.diagnostics)
    if len(snapshot.nodes) > options.max_nodes or len(snapshot.edges) > options.max_edges:
        snapshot.diagnostics.append('graph_limit')
    snapshot.nodes = snapshot.nodes[:options.max_nodes]
    ids = {n['id'] for n in snapshot.nodes}
    snapshot.edges = list({e['id']: e for e in snapshot.edges if e['source'] in ids and e['target'] in ids}.values())[:options.max_edges]
    # Size limits count UTF-8 bytes, and retain an explicitly partial useful view.
    while len(encoded_snapshot(snapshot).encode('utf8')) > options.max_serialized_bytes and snapshot.nodes:
        snapshot.nodes = snapshot.nodes[:len(snapshot.nodes) // 2]
        ids = {n['id'] for n in snapshot.nodes}
        snapshot.edges = [e for e in snapshot.edges if e['source'] in ids and e['target'] in ids]
        if 'serialized_limit' not in snapshot.diagnostics:
            snapshot.diagnostics.append('serialized_limit')
    if snapshot.diagnostics:
        snapshot.coverage['projection'] = 'partial'
    if len(encoded_snapshot(snapshot).encode('utf8')) > options.max_serialized_bytes:
        raise ValueError('Viewer byte budget cannot contain snapshot metadata')
    return snapshot
