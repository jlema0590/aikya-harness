"""Pinned Dart syntax extraction. Relationships describe containment, never calls."""
from .treesitter import _module, parser_version
from ..contracts import ParsedFile
from ..policy import content_hash

TYPES = {'class_definition': 'class', 'enum_declaration': 'enum',
         'mixin_declaration': 'mixin', 'extension_declaration': 'extension'}
SIGNATURES = {'function_signature', 'constructor_signature', 'factory_constructor_signature',
              'getter_signature', 'setter_signature'}


def parse_file(path, content):
    parser_id, version = parser_version(path)
    result = ParsedFile(path, content_hash(content), 'file_only', parser_id, version)
    if parser_id == 'inventory':
        result.diagnostics.append('optional_grammar_unavailable')
        return result
    try:
        core = _module('tree_sitter', 'tree-sitter')
        grammar = _module('tree_sitter_dart', 'tree-sitter-dart')
        tree = core.Parser(core.Language(grammar.language())).parse(content)
        if tree.root_node.has_error:
            raise ValueError('grammar_parse_error')
        result.status = 'indexed'
        stack = [(tree.root_node, '', None)]
        body_scopes = {}
        visited = 0
        while stack:
            node, parent, parent_kind = stack.pop()
            if node.id in body_scopes:parent,parent_kind=body_scopes[node.id]
            visited += 1
            if visited > 200000 or len(result.symbols) >= 50000:
                raise ValueError('grammar_node_limit')
            scope, scope_kind = parent, parent_kind
            kind = TYPES.get(node.type)
            signature = node.type in SIGNATURES
            if kind or signature:
                identifiers = [c for c in node.named_children if c.type == 'identifier']
                # Anonymous extensions have no declaration name. Keep their members
                # unqualified instead of inventing a class or dynamic binding.
                if identifiers:
                    selected = identifiers[-1] if 'constructor' in node.type else identifiers[0]
                    label = content[selected.start_byte:selected.end_byte].decode('utf8')
                    if 'constructor' in node.type and label == parent.rsplit('.', 1)[-1]:
                        qualified = parent
                    else:
                        qualified = '.'.join(x for x in (parent, label) if x)
                    kind = kind or ('method' if parent_kind in ('class','enum','mixin','extension') else 'function')
                    end = node
                    if signature:
                        holder = node.parent if node.parent and node.parent.type in ('method_signature', 'declaration') else node
                        following = holder.next_named_sibling
                        end = following if following and following.type == 'function_body' else holder
                        if following and following.type == 'function_body':body_scopes[following.id]=(qualified,kind)
                    result.symbols.append(dict(name=label, qualified_name=qualified, kind=kind, path=path,
                        start_byte=node.start_byte, end_byte=end.end_byte, start_line=node.start_point.row+1,
                        end_line=end.end_point.row+1, signature=content[node.start_byte:node.end_byte].decode('utf8')[:400],
                        file_sha256=result.sha256, parser_id=parser_id, parser_version=version))
                    if parent and qualified != parent:
                        result.relations.append(dict(source=parent, target=qualified, relation='contains', path=path,
                                                     line=node.start_point.row+1, provenance='syntax'))
                    if not signature:
                        scope, scope_kind = qualified, kind
            if node.type == 'import_or_export':
                result.imports.append(dict(name=content[node.start_byte:node.end_byte].decode('utf8')[:400],
                                           path=path, line=node.start_point.row+1, provenance='syntax'))
            stack.extend((c, scope, scope_kind) for c in reversed(node.named_children))
    except (ImportError, ValueError, TypeError, UnicodeError, OSError):
        result.status = 'parse_error'
        result.symbols, result.imports, result.relations = [], [], []
        result.diagnostics.append('grammar_unavailable_or_invalid_input')
    return result
