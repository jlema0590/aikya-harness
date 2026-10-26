"""Versioned, bounded viewer data; independent from model/provider APIs."""
from dataclasses import asdict, dataclass, field, fields
import json


@dataclass(frozen=True)
class ViewerOptions:
    max_notes: int = 5000
    max_documents: int = 5000
    max_document_bytes: int = 1048576
    max_input_bytes: int = 104857600
    max_nodes: int = 50000
    max_edges: int = 200000
    max_serialized_bytes: int = 20971520
    max_excerpt_chars: int = 2000
    max_drawn_nodes: int = 500

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if type(value) is not int or not 1 <= value <= item.default:
                raise ValueError('Viewer limits must be positive and within supported bounds')


@dataclass
class MemorySnapshot:
    schema_version: int = 1
    generated_at: float = 0
    index_generation: int = 0
    coverage: dict = field(default_factory=dict)
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    diagnostics: list = field(default_factory=list)
    project: str = ''


@dataclass
class ExportResult:
    status: str
    html_path: str = 'aikya/docs/memory/view/index.html'
    report_path: str = 'aikya/docs/memory/view/report.md'
    coverage: dict = field(default_factory=dict)
    diagnostics: list = field(default_factory=list)
    published_generation: str = ''


@dataclass(frozen=True)
class WatchOptions:
    poll_interval_ms: int = 2000
    debounce_ms: int = 750
    max_batch_wait_ms: int = 3000
    reconcile_interval_s: int = 60
    live: bool = False

    def __post_init__(self):
        for key, lower, upper in (('poll_interval_ms', 50, 60000), ('debounce_ms', 0, 3000),
                                  ('max_batch_wait_ms', 1, 10000), ('reconcile_interval_s', 1, 3600)):
            if type(getattr(self, key)) is not int or not lower <= getattr(self, key) <= upper:
                raise ValueError('Invalid watch interval')
        if self.debounce_ms > self.max_batch_wait_ms or type(self.live) is not bool:
            raise ValueError('Invalid watch options')


@dataclass
class WatchStatus:
    state: str = 'Starting'
    index_generation: int = 0
    published_generation: str = ''
    pending_count: int = 0
    last_verified_at: float = 0
    coverage: dict = field(default_factory=dict)
    diagnostics: list = field(default_factory=list)


@dataclass
class LiveEndpoint:
    url: str
    close: object


def encoded_snapshot(snapshot):
    """Count and render the same UTF-8 JSON transport, including HTML escaping."""
    return (json.dumps(asdict(snapshot), ensure_ascii=False)
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))
