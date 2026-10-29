"""Pinned optional declaration grammars; no dynamic binding or call inference."""
from functools import lru_cache
import importlib
import importlib.metadata as metadata
import importlib.util
import sys
from pathlib import Path
from ..contracts import ParsedFile
from ..policy import content_hash

PINS = {'tree-sitter': '0.25.2', 'tree-sitter-java': '0.23.5',
        'tree-sitter-javascript': '0.25.0', 'tree-sitter-typescript': '0.23.2',
        'tree-sitter-c-sharp': '0.23.1', 'tree-sitter-go': '0.25.0', 'tree-sitter-dart': '0.1.0'}
LANGUAGES = {'.dart': ('dart', 'language'), '.java': ('java', 'language'), '.js': ('javascript', 'language'),
             '.jsx': ('javascript', 'language'), '.mjs': ('javascript', 'language'),
             '.cjs': ('javascript', 'language'), '.ts': ('typescript', 'language_typescript'),
             '.tsx': ('typescript', 'language_tsx'), '.cs': ('c_sharp', 'language'), '.go': ('go', 'language')}
DECLARATIONS = {'class_declaration': 'class', 'interface_declaration': 'interface',
                'enum_declaration': 'enum', 'record_declaration': 'class',
                'struct_declaration': 'class', 'type_spec': 'class',
                'function_declaration': 'function', 'generator_function_declaration': 'function',
                'method_declaration': 'method', 'method_definition': 'method',
                'constructor_declaration': 'method', 'method_signature': 'method',
                'function_signature': 'function', 'arrow_function': 'function',
                'function_expression': 'function'}


@lru_cache(maxsize=8)
def _module(name, distribution):
    installed = metadata.distribution(distribution)
    if installed.version != PINS[distribution]:
        raise ValueError('Optional grammar version differs from the reviewed pin')
    expected = Path(installed.locate_file(name)).resolve()
    if expected.is_relative_to(Path.cwd().resolve()) and not expected.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError('Project-local modules cannot impersonate installed grammars')
    spec = importlib.util.find_spec(name)
    if spec is None or not spec.origin or not Path(spec.origin).resolve().is_relative_to(expected):
        raise ValueError('Untrusted optional parser import location')
    return importlib.import_module(name)


def parser_version(path):
    config = LANGUAGES.get(Path(path).suffix.lower())
    if not config:
        return 'inventory', '1'
    language, factory = config
    distribution = 'tree-sitter-' + language.replace('_', '-')
    try:
        _module('tree_sitter', 'tree-sitter')
        _module('tree_sitter_' + language, distribution)
    except (ImportError, metadata.PackageNotFoundError, ValueError, OSError):
        return 'inventory', '1'
    return 'treesitter-' + language + ('-tsx' if factory.endswith('tsx') else ''), PINS['tree-sitter'] + '/' + PINS[distribution] + '/1'


def parse_file(path, content):
    parser_id, version = parser_version(path)
    result = ParsedFile(path, content_hash(content), 'file_only', parser_id, version)
    if parser_id == 'inventory':
        result.diagnostics.append('optional_grammar_unavailable')
        return result
    language, factory = LANGUAGES[Path(path).suffix.lower()]
    try:
        core = _module('tree_sitter', 'tree-sitter')
        grammar = _module('tree_sitter_' + language, 'tree-sitter-' + language.replace('_', '-'))
        parser = core.Parser(core.Language(getattr(grammar, factory)()))
        tree = parser.parse(content)
        if tree.root_node.has_error:
            result.status = 'parse_error'
            result.diagnostics.append('grammar_parse_error')
            return result
        result.status = 'indexed'
        package = ''
        if language == 'java':
            for node in tree.root_node.named_children:
                if node.type == 'package_declaration':
                    package = content[node.start_byte:node.end_byte].decode().removeprefix('package').strip().rstrip(';')
        stack = [(tree.root_node, package, None)]
        visited = 0
        while stack:
            node, parent, parent_kind = stack.pop()
            visited += 1
            if visited > 200000 or len(result.symbols) >= 50000:
                result.status = 'parse_error'
                result.symbols, result.imports, result.relations = [], [], []
                result.diagnostics.append('grammar_node_limit')
                return result
            child_parent, child_kind = parent, parent_kind
            if node.type in ('namespace_declaration', 'file_scoped_namespace_declaration'):
                name = node.child_by_field_name('name')
                if name:
                    child_parent = '.'.join(p for p in (parent, content[name.start_byte:name.end_byte].decode()) if p)
            kind = DECLARATIONS.get(node.type)
            name = node.child_by_field_name('name') if kind else None
            if kind and not name and node.type in ('arrow_function', 'function_expression') and node.parent and node.parent.type == 'variable_declarator':
                name = node.parent.child_by_field_name('name')
            if kind and name:
                label = content[name.start_byte:name.end_byte].decode('utf8')
                scope = parent
                receiver = node.child_by_field_name('receiver')
                if language == 'go' and receiver:
                    parameters = receiver.named_children
                    value = parameters[0].child_by_field_name('type') if parameters else None
                    if value:
                        scope = content[value.start_byte:value.end_byte].decode().lstrip('*')
                qualified = '.'.join(p for p in (scope, label) if p)
                body = node.child_by_field_name('body')
                signature_end = body.start_byte if body else min(node.end_byte, node.start_byte + 400)
                result.symbols.append(dict(name=label, qualified_name=qualified, kind=kind, path=path,
                    start_byte=node.start_byte, end_byte=node.end_byte, start_line=node.start_point.row + 1,
                    end_line=node.end_point.row + 1, signature=content[node.start_byte:signature_end].decode('utf8')[:400],
                    file_sha256=result.sha256, parser_id=parser_id, parser_version=version))
                if parent_kind:
                    result.relations.append(dict(source=parent, target=qualified, relation='contains', path=path,
                                                 line=node.start_point.row + 1, provenance='syntax'))
                child_parent, child_kind = qualified, kind
            if node.type in ('import_declaration', 'import_statement', 'using_directive', 'import_spec'):
                result.imports.append(dict(name=content[node.start_byte:node.end_byte].decode()[:400], path=path,
                                           line=node.start_point.row + 1, provenance='syntax'))
            stack.extend((child, child_parent, child_kind) for child in reversed(node.named_children))
    except (ImportError, ValueError, TypeError, UnicodeError, OSError):
        result.status, result.symbols, result.imports, result.relations = 'parse_error', [], [], []
        result.diagnostics.append('grammar_unavailable_or_invalid_input')
    return result
