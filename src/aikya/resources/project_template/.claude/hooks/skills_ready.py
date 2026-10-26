#!/usr/bin/env python3
"""SessionStart read-only: informa sólo si falta una integración ya seleccionada.
No red, ni ejecución de instaladores, ni indexación, ni carga del grafo.
"""
import json
import os
from pathlib import Path

root=Path(os.environ.get('CLAUDE_PROJECT_DIR') or Path(__file__).resolve().parents[2])
try:
    choices=json.loads((root/'.harness/project-profile.json').read_text(encoding='utf8'))['decisions']
except (OSError,KeyError,ValueError):
    raise SystemExit(0)
requested=['ponytail','graphify']
if choices.get('frontend') not in (None,'none') or choices.get('mobile') not in (None,'none'):
    requested.append('ui-ux-pro-max')
missing=[s for s in requested if not (root/'.claude/skills'/s/'SKILL.md').is_file()]
if missing:
    print('Harness: integraciones pendientes: '+', '.join(missing)+'. Para instalarlas con autorización: '
          'python3 aikya/scripts/harness/external_skills.py install --yes. No se instalan automáticamente durante SessionStart.')
