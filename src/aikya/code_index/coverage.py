"""Semantic coverage is separate from snapshot completeness."""
from pathlib import Path


def summarize(files, symbols):
    result = {}
    for row in files:
        suffix = Path(row['path']).suffix.lower()
        item = result.setdefault(suffix, {'indexed': 0, 'file_only': 0, 'error': 0, 'symbols': 0})
        status = row.get('status')
        item[status if status in ('indexed', 'file_only') else 'error'] += 1
    for symbol in symbols:
        suffix = Path(symbol['path']).suffix.lower()
        if suffix in result:
            result[suffix]['symbols'] += 1
    return dict(sorted(result.items()))
