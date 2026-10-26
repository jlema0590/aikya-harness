#!/usr/bin/env python3
"""UserPromptSubmit: inicia una petición sin guardar su contenido."""
import json
import os
from pathlib import Path
import sys

root=Path(os.environ.get('CLAUDE_PROJECT_DIR') or '.').resolve()
sys.path.insert(0,str(root/'scripts/harness'))
try:
    from docs_guard import start_request
    event=json.load(sys.stdin)
    data=start_request(event.get('session_id','default'),event.get('prompt',''))
    message=(f'Petición {data["request_id"]} ({data["kind"]}). '
             'Si modificas código, infraestructura o tests, actualiza los documentos afectados en docs/, '
             f'y crea docs/changes/{data["request_id"]}.md con Cambios, Evidencias y Documentos actualizados. '
             'Comprueba el estado documental antes de finalizar.')
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'UserPromptSubmit','additionalContext':message}},ensure_ascii=False))
except Exception as exc:
    print(f'Harness docs: error al registrar petición: {exc}',file=sys.stderr)
    sys.exit(2)
