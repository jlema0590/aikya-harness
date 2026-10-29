"""Single-generation SQLite snapshots bound to the current project/worktree."""
from contextlib import contextmanager
import json
import sqlite3
from aikya.core.checkpoints import identity, safe_file
from .contracts import IndexSnapshot
from .policy import project_root


class IndexStore:
    def __init__(self, root):
        self.root = project_root(root)
        self.path = safe_file(self.root, '.harness/state/code-index/index.sqlite')

    @contextmanager
    def connect(self, *, write=False):
        safe_file(self.root, self.path.relative_to(self.root).as_posix())
        if not write and not self.path.exists():
            yield None
            return
        if self.path.exists() and self.path.stat().st_size > 268435456:
            raise ValueError('Code index exceeds the local storage limit')
        if write:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = None
        try:
            uri = self.path.as_uri() + ('?mode=rwc' if write else '?mode=ro')
            connection = sqlite3.connect(uri, uri=True, timeout=3)
            connection.execute('PRAGMA trusted_schema=OFF')
            connection.execute('PRAGMA foreign_keys=ON')
            if write:
                connection.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
                for table in ('files', 'symbols', 'imports', 'relations'):
                    connection.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, path TEXT NOT NULL, payload TEXT NOT NULL)')
                    connection.execute(f'CREATE INDEX IF NOT EXISTS {table}_by_path ON {table}(path,id)')
                previous = dict(connection.execute('SELECT key,value FROM meta'))
                if not previous:
                    connection.executemany('INSERT INTO meta VALUES (?,?)', [('schema', '1'), ('identity', identity(self.root)), ('generation', '0'), ('status', 'complete')])
            else:
                connection.execute('PRAGMA query_only=ON')
            connection.execute('BEGIN' if not connection.in_transaction else 'SELECT 1')
            metadata = dict(connection.execute('SELECT key,value FROM meta'))
            if metadata.get('schema') != '1' or metadata.get('identity') != identity(self.root):
                raise ValueError('Code index belongs to another checkout or schema; rebuild explicitly')
            yield connection
            if write:
                connection.commit()
        except sqlite3.Error as exc:
            raise ValueError('Code index unavailable or corrupt; preserve and rebuild explicitly') from exc
        finally:
            if connection:
                connection.close()

    def read_snapshot(self):
        with self.connect() as connection:
            if connection is None:
                return IndexSnapshot()
            meta = dict(connection.execute('SELECT key,value FROM meta'))
            rows = {}
            for table, limit in (('files', 12000), ('symbols', 50000), ('imports', 50000), ('relations', 200000)):
                records = connection.execute(f'SELECT payload FROM {table} ORDER BY path,id LIMIT ?', (limit + 1,)).fetchall()
                if len(records) > limit:
                    meta['status'] = 'partial'
                rows[table] = [json.loads(raw) for raw, in records[:limit]]
            return IndexSnapshot(int(meta['generation']), meta['status'], **rows)

    def status(self):
        from .coverage import summarize
        snapshot = self.read_snapshot()
        return {'generation': snapshot.generation, 'status': snapshot.status,
                'files': len(snapshot.files), 'symbols': len(snapshot.symbols),
                'coverage': {'languages': summarize(snapshot.files, snapshot.symbols)}}
