"""Content-free measurements. Local bytes, provider tokens and quota are separate."""
from aikya.cli.commands import BOOTSTRAP_COMMANDS
from aikya.middleware.metrics import aggregate_usage
from aikya.middleware.usage import KEYS


def summarize_task(paths, *, session_id=None, start_utc=None, end_utc=None):
    report = aggregate_usage(paths, start_utc, end_utc, session_id)
    calls = report['totals'].get('calls', 0)
    return {'schema': 1, 'attribution': 'time_window' if calls else 'unavailable',
            'session_id': session_id, 'interval': report['interval'],
            'distinct_messages': calls,
            'tokens': {key: report['totals'].get(key, 0) for key in KEYS} if calls else None,
            'models': report['models'], 'coverage': report['coverage'],
            'quota': None,
            'note': 'Recorded selected transcripts; time correlation is not exact command billing or account quota.'}


def command_coverage(measured=None):
    measured = measured or {}
    unknown = set(measured) - set(BOOTSTRAP_COMMANDS)
    if unknown:
        raise ValueError('Unknown public command in efficiency receipt')
    return {name: {'tokens': None, 'model': None, 'effort': None,
                   'attribution': 'unavailable', 'mode': 'not_measured',
                   **measured.get(name, {})} for name in BOOTSTRAP_COMMANDS}
