"""Explicit source roots and prepared decisions for the installation pipeline."""
from dataclasses import dataclass,field
from pathlib import Path
from aikya.resource_paths import source_root,source_path

@dataclass(frozen=True)
class InstallerContext:
    source_root: Path=field(default_factory=source_root)
    template_root: Path|None=None

    def __post_init__(self):
        if self.template_root is None:
            object.__setattr__(self,'template_root',source_path(self.source_root,'template'))

@dataclass(frozen=True)
class InstallationPlan:
    target: Path
    profile: dict
    detected: dict
    adopt_existing: bool
    documentation_language: str
    context: InstallerContext
    previous_profile: dict
    previous_decisions: dict
    doc_operations: list
    sdd_operations: list
    methodology_operations: list
    claude_contract: str|None
    bundle: list
