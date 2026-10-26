"""Export or observe local project memory without model invocation."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import sys
import threading
import webbrowser
from aikya.memory.viewer.export import export_view
from aikya.memory.viewer.contracts import WatchOptions, ExportResult


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline Aikya memory viewer and local observer')
    parser.add_argument('--target', type=Path, default=Path.cwd())
    parser.add_argument('--open', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--session-managed', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--docs-lang', choices=('en', 'es'))
    parser.add_argument('--session', default=os.environ.get('CLAUDE_SESSION_ID', 'local'))
    args = parser.parse_args(argv)
    if args.dry_run and (args.watch or args.refresh or args.open):
        parser.error('--dry-run cannot refresh, watch or open the viewer')
    if args.session_managed and not args.watch:
        parser.error('Session-managed observation requires --watch')
    endpoint = None
    stop_event = threading.Event()
    previous_signals = {}
    lifecycle = None
    try:
        root = args.target.expanduser().resolve()
        if not args.dry_run and not args.session_managed:
            from aikya.middleware.lifecycle import Lifecycle
            lifecycle = Lifecycle(root, args.session, 'aikya-memory')
            lifecycle.done('explore', 'Project-local memory policy and requested mode inspected')
            lifecycle.event('plan', 'running', 'Resolving local publication and watch scope')
            lifecycle.done('plan', 'Explicit options and project-local destinations selected')
            lifecycle.event('implement', 'running', 'Publishing owned project memory projection')
        if args.watch:
            from aikya.code_index.policy import load_policy
            policy = load_policy(root)
            if not policy.watch:
                raise ValueError('Watch policy is disabled; enable it in the reviewed project policy')
            if args.open and not policy.auto_export:
                raise ValueError('Live refresh requires an already-enabled automatic export policy')
        if args.session_managed:
            result = ExportResult('watching', coverage={'viewer': 'enabled' if policy.auto_export else 'disabled'})
        else:
            result = export_view(root, refresh=args.refresh, open_browser=args.open and not args.watch,
                                 dry_run=args.dry_run, language=None if args.watch else args.docs_lang)
        print(json.dumps(asdict(result), ensure_ascii=False), flush=True)
        if lifecycle:
            lifecycle.done('implement', 'Owned HTML and matching Markdown report exported')
            lifecycle.event('validate', 'running', 'Checking publication generation and artifact hashes')
            from aikya.memory.viewer.publication import read_publication
            read_publication(root)
            lifecycle.done('validate', 'HTML/report hashes and schema match; coverage is ' + result.status, True)
            lifecycle.event('security', 'running', 'Checking local output ownership and contained paths')
            from aikya.memory.viewer.export import preflight
            preflight(root)
            lifecycle.done('security', 'Owned destinations and contained paths validated; no model or external server required', True)
            lifecycle.finish('completed')
        if not args.watch:
            return 0 if result.status in ('complete', 'preview') else 4
        if threading.current_thread() is threading.main_thread():
            for name in (signal.SIGINT, signal.SIGTERM):
                previous_signals[name] = signal.signal(name, lambda *_: stop_event.set())
        if args.session_managed:
            from aikya.memory.viewer.watch import watch_project
            watch_project(root, options=WatchOptions(), stop_event=stop_event, session_managed=True)
        else:
            from aikya.memory.viewer.client import observer_client, wait_for_observer
            with observer_client(root) as heartbeat:
                if args.open:
                    from aikya.memory.viewer.live import serve_live
                    endpoint = serve_live(root, stop_event=stop_event, language=args.docs_lang)
                    webbrowser.open(endpoint.url)
                wait_for_observer(stop_event, heartbeat)
        return 0
    except (OSError, ValueError, TypeError) as error:
        if lifecycle:
            lifecycle.event('implement', 'failed', reason='Local memory operation failed')
            lifecycle.finish('failed', 'Local memory operation requires review')
        print('ERROR: ' + str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        stop_event.set()
        return 0
    finally:
        stop_event.set()
        if endpoint:
            endpoint.close()
        for name, handler in previous_signals.items():
            signal.signal(name, handler)
