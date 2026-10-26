"""Internal bounded code-index operations; cache clearing needs explicit approval."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from .policy import configure, load_policy
from .store import IndexStore
from .sync import sync
from .query import query


def main(argv=None):
    parser = argparse.ArgumentParser(description='Project-local code index')
    parser.add_argument('action', choices=('build', 'sync', 'query', 'status', 'clear'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--query', default='')
    parser.add_argument('--max-chars', type=int, default=6000)
    parser.add_argument('--allowed-file', action='append')
    parser.add_argument('--approved', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = args.root.expanduser().resolve()
        if args.action == 'build':
            configure(root, approved=args.approved)
        if args.action in ('build', 'sync'):
            result = asdict(sync(root, full=True))
        elif args.action == 'query':
            result = asdict(query(root, args.query, allowed_files=args.allowed_file, max_chars=args.max_chars))
        elif args.action == 'status':
            result = IndexStore(root).status() if load_policy(root).enabled else {'status': 'disabled'}
        else:
            if not args.approved:
                raise ValueError('Clearing the derived cache requires --approved')
            store = IndexStore(root)
            if store.path.exists():
                with locked(store.path.parent):
                    store.read_snapshot()  # A path alone does not prove cache ownership.
                    for suffix in ('', '-journal', '-wal', '-shm'):
                        path = safe_file(root, store.path.relative_to(root).as_posix() + suffix)
                        if path.exists():
                            path.unlink()
            result = {'status': 'cleared', 'policy_preserved': True}
        print(json.dumps(result, ensure_ascii=False))
        return 4 if result.get('status') == 'partial' else 0
    except (OSError, ValueError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
