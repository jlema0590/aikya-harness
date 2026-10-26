"""Bounded records shared by indexing, retrieval and presentation."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IndexOptions:
    enabled: bool = False
    max_files: int = 12000
    max_file_bytes: int = 1048576
    max_sync_bytes: int = 104857600
    watch: bool = False
    auto_export: bool = False
    scope: str = '.'


@dataclass
class ParsedFile:
    path: str
    sha256: str
    status: str
    parser_id: str = 'inventory'
    parser_version: str = '1'
    symbols: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    relations: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)


@dataclass
class SyncResult:
    generation: int = 0
    status: str = 'disabled'
    parsed_files: int = 0
    verified_bytes: int = 0
    skipped_files: int = 0
    diagnostics: list = field(default_factory=list)


@dataclass
class IndexSnapshot:
    generation: int = 0
    status: str = 'missing'
    files: list = field(default_factory=list)
    symbols: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    relations: list = field(default_factory=list)


@dataclass
class QueryResult:
    generation: int = 0
    status: str = 'missing'
    matches: list = field(default_factory=list)
    context: str = ''
    truncated: bool = False
    diagnostics: list = field(default_factory=list)
