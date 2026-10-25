"""Explicit parser coverage; unsupported languages remain file inventory."""
from pathlib import Path
from ..contracts import ParsedFile
from ..policy import content_hash


def parse_file(path, content):
    if Path(path).suffix.lower() in ('.py', '.pyi'):
        from .python import parse_file as parse_python
        return parse_python(path, content)
    from .treesitter import LANGUAGES, parse_file as parse_optional
    if Path(path).suffix.lower() in LANGUAGES:
        return parse_optional(path, content)
    return ParsedFile(path, content_hash(content), 'file_only')


def parser_version(path):
    if Path(path).suffix.lower() in ('.py', '.pyi'):
        return 'python-ast', '1'
    from .treesitter import parser_version as optional_version
    return optional_version(path)
