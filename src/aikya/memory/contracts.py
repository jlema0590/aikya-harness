"""Read-only inventory of existing reviewed memory records."""
from dataclasses import dataclass, field


@dataclass
class NoteInspection:
    notes: list = field(default_factory=list)
    omitted_count: int = 0
    diagnostics: list = field(default_factory=list)
