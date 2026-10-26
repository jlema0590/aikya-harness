"""Read only a verified matching HTML/report pair, never arbitrary source files."""
import hashlib
import json
import re
from aikya.code_index.policy import read_source
from aikya.documentation.layout import generated
from .contracts import MemorySnapshot
from .export import OWNER


def read_publication(root):
    html = read_source(root, 'aikya/docs/memory/view/index.html', 30000000).decode('utf8')
    report = read_source(root, 'aikya/docs/memory/view/report.md', 1000000).decode('utf8')
    if not html.startswith(OWNER) or not generated(report):
        raise ValueError('Owned memory publication required')
    digest = hashlib.sha256(html.encode()).hexdigest()
    match = re.search(r'^- projection: ([a-f0-9]{64})$', report, re.M)
    data = re.search(r'<script type="application/json" id="snapshot">(.*?)</script>', html, re.S)
    if not match or not data or '- html_sha256: ' + digest not in report:
        raise ValueError('Memory report and HTML do not match; retry publication')
    snapshot = MemorySnapshot(**json.loads(data[1]))
    if snapshot.schema_version != 1:
        raise ValueError('Unsupported memory snapshot')
    return snapshot, match[1]
