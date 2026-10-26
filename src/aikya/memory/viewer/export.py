"""Recoverable owned HTML/report publication; never overwrites team artifacts."""
from dataclasses import asdict
import hashlib
import json
import re
import time
import webbrowser
from aikya.core.checkpoints import identity, safe_file
from aikya.core.state import locked
from aikya.documentation.language import resolve
from aikya.documentation.layout import generated, index_paths, write_document, stamp
from aikya.storage import atomic_write
from aikya.code_index.policy import load_policy, project_root
from aikya.code_index.sync import sync
from .collect import collect_snapshot
from .contracts import ExportResult
from .render import render_html, asset_fingerprint

OWNER = '<!-- AIKYA MEMORY VIEWER schema=1 -->'
PUBLICATION = '.harness/state/memory-view/publication.json'


def preflight(root):
    """Validate all publication destinations before installation or export writes."""
    result = ExportResult('preview')
    html_path = safe_file(root, result.html_path)
    report_path = safe_file(root, result.report_path)
    index_paths(root)
    if html_path.exists() and (html_path.stat().st_size > 30000000 or not html_path.read_text(encoding='utf8').startswith(OWNER)):
        raise ValueError('Custom viewer HTML is preserved')
    if report_path.exists() and not generated(report_path.read_text(encoding='utf8')):
        raise ValueError('Custom viewer report is preserved')
    state_path = safe_file(root, PUBLICATION)
    if state_path.exists():
        if state_path.stat().st_size > 4000:
            raise ValueError('Invalid memory publication ownership state')
        state = json.loads(state_path.read_text())
        if (not isinstance(state, dict) or state.get('schema') != 1 or state.get('identity') != identity(root)
                or any(not isinstance(state.get(key), list) or not 1 <= len(state[key]) <= 2
                       or any(not isinstance(v, str) or not re.fullmatch('[a-f0-9]{64}', v) for v in state[key])
                       for key in ('html_hashes', 'report_hashes'))):
            raise ValueError('Custom or moved memory publication state is preserved')
        for path, key in ((html_path, 'html_hashes'), (report_path, 'report_hashes')):
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() not in state[key]:
                raise ValueError('Edited memory artifact is preserved; review before regeneration')
    elif html_path.exists():
        if not report_path.exists() or '- html_sha256: ' + hashlib.sha256(html_path.read_bytes()).hexdigest() not in report_path.read_text():
            raise ValueError('Unverified existing memory HTML is preserved')
    return html_path, report_path


def projection_hash(snapshot, language):
    value = asdict(snapshot)
    value.pop('generated_at')
    return hashlib.sha256(json.dumps({'snapshot': value, 'language': language, 'renderer': asset_fingerprint()}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def export_view(root, *, refresh=False, open_browser=False, dry_run=False, language=None):
    root = project_root(root)
    if dry_run and (refresh or open_browser):
        raise ValueError('Dry-run cannot refresh or open the viewer')
    locale = resolve(root, language)
    result = ExportResult('preview')
    html_path, report_path = preflight(root)
    if dry_run:
        result.coverage = {'code_index': 'enabled' if load_policy(root).enabled else 'disabled'}
        return result
    if refresh:
        if not load_policy(root).enabled:
            raise ValueError('Code index policy must already be enabled; export cannot enable it')
        sync(root)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    with locked(html_path.parent):
        preflight(root)
        snapshot = collect_snapshot(root)
        generation = projection_hash(snapshot, locale)
        result.coverage, result.diagnostics = snapshot.coverage, snapshot.diagnostics
        result.published_generation = generation
        result.status = 'partial' if snapshot.diagnostics or any(v in ('partial', 'invalid', 'missing') for v in snapshot.coverage.values()) else 'complete'
        if html_path.exists() and report_path.exists():
            report = report_path.read_text(encoding='utf8')
            actual = hashlib.sha256(html_path.read_bytes()).hexdigest()
            if 'projection: ' + generation in report and 'html_sha256: ' + actual in report:
                if open_browser:
                    webbrowser.open(html_path.as_uri())
                return result
        html = render_html(snapshot, language=locale)
        digest = hashlib.sha256(html.encode()).hexdigest()
        title = 'Informe de memoria local' if locale == 'es' else 'Local memory report'
        report = ('# ' + title + '\n\n- projection: ' + generation + '\n- html_sha256: ' + digest
                  + '\n- index_generation: ' + str(snapshot.index_generation) + '\n- generated_at: ' + str(snapshot.generated_at)
                  + '\n- status: ' + result.status + '\n- nodes: ' + str(len(snapshot.nodes))
                  + '\n- edges: ' + str(len(snapshot.edges)) + '\n- coverage: ' + json.dumps(snapshot.coverage)
                  + '\n- diagnostics: ' + json.dumps(snapshot.diagnostics) + '\n')
        state_path = safe_file(root, PUBLICATION)
        report_digest = hashlib.sha256(stamp(report).encode()).hexdigest()
        intent = {'schema': 1, 'identity': identity(root), 'html_hashes': [digest], 'report_hashes': [report_digest]}
        for path, key in ((html_path, 'html_hashes'), (report_path, 'report_hashes')):
            if path.exists():
                before = hashlib.sha256(path.read_bytes()).hexdigest()
                if before not in intent[key]:
                    intent[key].append(before)
        atomic_write(state_path, json.dumps(intent, sort_keys=True) + '\n')
        atomic_write(html_path, html)
        write_document(root, 'memory/view/report.md', report, replace_generated=True)
        intent['html_hashes'], intent['report_hashes'] = [digest], [report_digest]
        atomic_write(state_path, json.dumps(intent, sort_keys=True) + '\n')
    if open_browser:
        webbrowser.open(html_path.as_uri())
    return result
