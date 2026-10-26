"""Pure rendering with embedded resources, escaped JSON and hashed CSP."""
import base64
import hashlib
from pathlib import Path
from .contracts import encoded_snapshot


def asset_fingerprint():
    resources = Path(__file__).resolve().parents[2] / 'resources/memory-viewer'
    digest = hashlib.sha256()
    for name in ('index.html.tmpl', 'viewer.css', 'viewer.js'):
        digest.update((resources / name).read_bytes())
    return digest.hexdigest()


def render_html(snapshot, *, language='en', live=False):
    if language not in ('en', 'es'):
        raise ValueError('Unsupported viewer language')
    resources = Path(__file__).resolve().parents[2] / 'resources/memory-viewer'
    template = (resources / 'index.html.tmpl').read_text(encoding='utf8')
    css = (resources / 'viewer.css').read_text(encoding='utf8')
    script = (resources / 'viewer.js').read_text(encoding='utf8')
    payload = encoded_snapshot(snapshot)
    digest = lambda text: "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"
    csp = ("default-src 'none'; script-src " + digest(script) + '; style-src ' + digest(css)
           + "; img-src data:; object-src 'none'; base-uri 'none'; form-action 'none'; connect-src " + ("'self'" if live else "'none'"))
    return (template.replace('@@LANG@@', language).replace('@@MODE@@', 'live' if live else 'snapshot')
            .replace('@@CSP@@', csp).replace('@@CSS@@', css).replace('@@SCRIPT@@', script).replace('@@DATA@@', payload))
