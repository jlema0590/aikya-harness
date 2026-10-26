"""Source-qualified identities and explicit graph edges only."""
def symbol_id(symbol):
    return 'symbol:' + symbol['path'] + ':' + symbol['qualified_name'] + ':' + str(symbol['start_line'])


def edge(source, target, relation, *, path='', line=None, provenance='syntax'):
    return {'id': source + '|' + relation + '|' + target, 'source': source, 'target': target,
            'relation': relation, 'provenance': provenance, 'evidence': {'path': path, 'line': line}}


def add_structure(snapshot):
    folders = set()
    for node in list(snapshot.nodes):
        if node['type'] not in ('file', 'document', 'memory'):
            continue
        parts = node['path'].split('/')[:-1]
        parent = 'project:root'
        for depth in range(len(parts)):
            path = '/'.join(parts[:depth + 1])
            ident = 'folder:' + path
            if ident not in folders:
                snapshot.nodes.append({'id': ident, 'label': parts[depth], 'type': 'folder', 'path': path,
                                       'source_hash': None, 'status': 'derived', 'details': {}})
                snapshot.edges.append(edge(parent, ident, 'contains', path=path, provenance='path'))
                folders.add(ident)
            parent = ident
        snapshot.edges.append(edge(parent, node['id'], 'contains', path=node['path'], provenance='path'))
