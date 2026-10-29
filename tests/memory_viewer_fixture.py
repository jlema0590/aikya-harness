"""Synthetic source graphs for repeatable browser acceptance, without private data."""
import argparse
from pathlib import Path

from aikya.memory.viewer.contracts import MemorySnapshot
from aikya.memory.viewer.graph import edge
from aikya.memory.viewer.render import render_html


def fixture_snapshot(shape='mixed'):
    snapshot = MemorySnapshot(project='synthetic-project', generated_at=1793145600,
                              index_generation=1, coverage={'code_index': 'available'})

    def add(ident, kind, path, parent=None):
        snapshot.nodes.append({'id': ident, 'type': kind, 'path': path,
                               'label': path.split('/')[-1] or 'synthetic-project',
                               'status': 'current', 'details': {}, 'source_hash': None})
        if parent:
            snapshot.edges.append(edge(parent, ident, 'contains', path=path))

    add('project:root', 'project', '')
    if shape == 'mixed':
        for number in range(10):
            add('folder:' + str(number), 'folder', 'module-' + str(number), 'project:root')
        for number in range(88):
            path = 'module-' + str(number % 10) + '/Source-' + str(number) + '.java'
            add('file:' + str(number), 'file', path, 'folder:' + str(number % 10))
            for suffix in ('Class', 'Method'):
                add('symbol:' + str(number) + suffix, 'class' if suffix == 'Class' else 'method',
                    path + '/' + suffix + '-with-a-long-verifiable-name', 'file:' + str(number))
        snapshot.edges.append(edge('folder:0', 'folder:1', 'related'))
    elif shape in ('wide', 'flow80', 'flow81', 'flow-overflow'):
        for number in range(1000 if shape == 'wide' else 81 if shape == 'flow-overflow' else int(shape[4:])):
            add('file:' + str(number), 'file', 'File-' + str(number) + '.py', 'project:root')
        if shape == 'flow-overflow':
            for source in range(80):
                for target in range(source + 1, 80):
                    snapshot.edges.append(edge('file:' + str(source), 'file:' + str(target), 'related'))
            for target in range(80):
                snapshot.edges.append(edge('file:80', 'file:' + str(target), 'related'))
    elif shape == 'deep':
        for number in range(180):
            add('folder:' + str(number), 'folder', '/'.join(['nested'] * (number + 1)),
                'project:root' if number == 0 else 'folder:' + str(number - 1))
    else:
        raise ValueError('Unknown fixture shape')
    return snapshot


def write_fixture(output: Path, language: str, shape='mixed', live=False):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(fixture_snapshot(shape), language=language, live=live), encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--language', choices=('en', 'es'), default='en')
    parser.add_argument('--shape', choices=('mixed', 'wide', 'deep', 'flow80', 'flow81', 'flow-overflow'), default='mixed')
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    write_fixture(args.output, args.language, args.shape, args.live)
