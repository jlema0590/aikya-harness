"""Pure rendering with embedded resources, escaped JSON and hashed CSP."""
import base64
import hashlib
from pathlib import Path
from .contracts import encoded_snapshot

RESOURCES = Path(__file__).resolve().parents[2] / 'resources/memory-viewer'
SCRIPTS = ('layout.js', 'labels.js', 'camera.js', 'graph.js', 'viewer.js')


def asset_fingerprint():
    digest = hashlib.sha256()
    for name in ('index.html.tmpl', 'viewer.css', *SCRIPTS):
        digest.update((RESOURCES / name).read_bytes())
    return digest.hexdigest()


def render_html(snapshot, *, language='en', live=False):
    if language not in ('en', 'es'):
        raise ValueError('Unsupported viewer language')
    template = (RESOURCES / 'index.html.tmpl').read_text(encoding='utf8')
    css = (RESOURCES / 'viewer.css').read_text(encoding='utf8')
    script = '\n'.join((RESOURCES / name).read_text(encoding='utf8') for name in SCRIPTS)
    payload = encoded_snapshot(snapshot)
    digest = lambda text: "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"
    csp = ("default-src 'none'; script-src " + digest(script) + '; style-src ' + digest(css)
           + "; img-src data:; object-src 'none'; base-uri 'none'; form-action 'none'; connect-src " + ("'self'" if live else "'none'"))
    return (template.replace('@@LANG@@', language).replace('@@MODE@@', 'live' if live else 'snapshot')
            .replace('@@CSP@@', csp).replace('@@CSS@@', css).replace('@@SCRIPT@@', script).replace('@@DATA@@', payload))
