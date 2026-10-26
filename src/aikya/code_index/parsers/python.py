"""Python declaration positions are UTF-8 bytes, matching the AST contract."""
import ast
from ..contracts import ParsedFile
from ..policy import content_hash


def parse_file(path, content):
    parsed = ParsedFile(path, content_hash(content), 'indexed', 'python-ast', '1')
    try:
        text = content.decode('utf8')
        tree = ast.parse(text)
    except (SyntaxError, UnicodeError, ValueError, RecursionError):
        parsed.status = 'parse_error'
        parsed.diagnostics.append('python_parse_error')
        return parsed
    lines = content.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    def walk(node, parents=()):
        declarations = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        child_parents = parents
        if isinstance(node, declarations):
            qualified = '.'.join([p[0] for p in parents] + [node.name])
            kind = 'class' if isinstance(node, ast.ClassDef) else ('method' if parents and parents[-1][1] == 'class' else 'function')
            start = starts[node.lineno - 1] + node.col_offset
            end = starts[node.end_lineno - 1] + node.end_col_offset
            symbol = dict(name=node.name, qualified_name=qualified, kind=kind, path=path,
                          start_byte=start, end_byte=end, start_line=node.lineno,
                          end_line=node.end_lineno, signature=text.splitlines()[node.lineno - 1].strip()[:400],
                          file_sha256=parsed.sha256, parser_id=parsed.parser_id, parser_version=parsed.parser_version)
            parsed.symbols.append(symbol)
            if parents:
                parsed.relations.append(dict(source='.'.join(p[0] for p in parents), target=qualified,
                                             relation='contains', path=path, line=node.lineno, provenance='syntax'))
            child_parents = parents + ((node.name, kind),)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.name if isinstance(node, ast.Import) else '.' * node.level + ((node.module + '.') if node.module else '') + alias.name
                parsed.imports.append(dict(name=name, path=path, line=node.lineno, provenance='syntax'))
        for child in ast.iter_child_nodes(node):
            walk(child, child_parents)
    try:
        walk(tree)
    except RecursionError:
        parsed.status, parsed.symbols, parsed.imports, parsed.relations = 'parse_error', [], [], []
    return parsed
