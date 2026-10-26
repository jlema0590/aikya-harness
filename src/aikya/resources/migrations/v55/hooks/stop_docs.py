#!/usr/bin/env python3
"""Stop: impide finalizar cambios de código sin documentación modificada."""
import json
import os
from pathlib import Path
import sys

root=Path(os.environ.get('CLAUDE_PROJECT_DIR') or '.').resolve()
sys.path.insert(0,str(root/'scripts/harness'))
try:
    from docs_guard import load_state,validate_request
    event=json.load(sys.stdin)
    # Evita ciclos sin fin si otro hook ya causó una continuación.
    if event.get('stop_hook_active'):
        sys.exit(0)
    state=load_state(event.get('session_id','default'))
    if state is None:
        sys.exit(0)
    ok,details=validate_request(state)
    if not ok:
        print(json.dumps({'decision':'block','reason':
            'Gate de documentación pendiente para '+state['request_id']+': '+
            '; '.join(details[-8:])+'. Actualiza los documentos con contenido real (no placeholders) '
            'y comprueba de nuevo. Si es trabajo sólo informativo, no edites código.'},ensure_ascii=False))
except Exception as exc:
    # Fallo visible, sin bloquear infinitamente: CI seguirá validando la documentación.
    print('Harness docs: no se pudo validar Stop: '+str(exc),file=sys.stderr)
    sys.exit(2)
