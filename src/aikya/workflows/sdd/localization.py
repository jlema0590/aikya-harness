"""Spanish headings for SDD living docs; machine state and user content remain unchanged."""

def localize_sdd(body: str) -> str:
    """Translate generated SDD headings only; retain user-authored content and IDs."""
    prefixes = {
        '# Design — ': '# Diseño — ',
        '# Execution plan — ': '# Plan de ejecución — ',
        '# Recorded evidence — ': '# Evidencias registradas — ',
        '# Verification invalidated — ': '# Verificación invalidada — ',
        '# Clarifications — ': '# Aclaraciones — ',
        '# Design and plan — ': '# Diseño y plan — ',
        '# Tasks — ': '# Tareas — ',
        '# SDD verification — ': '# Verificación SDD — ',
        '**Status:** ': '**Estado:** ',
        '- Declared result: ': '- Resultado declarado: ',
        '- Command/check: ': '- Comando/comprobación: ',
        '- Evidence file: ': '- Archivo de evidencia: ',
    }
    exact = {
        '## Selected approach': '## Enfoque seleccionado',
        'Task progress changed; previous results are no longer current. Re-run and record the relevant checks before claiming completion.': 'El progreso de las tareas cambió; los resultados anteriores ya no están vigentes. Ejecuta y registra las comprobaciones pertinentes antes de afirmar que el trabajo está terminado.',
        '## Objective': '## Objetivo',
        '## Requirements and acceptance': '## Requisitos y aceptación',
        '## Nonfunctional requirements': '## Requisitos no funcionales',
        '## Proposed design': '## Diseño propuesto',
        '## Technical decisions': '## Decisiones técnicas',
        '## Risks and limitations': '## Riesgos y limitaciones',
        '## Test strategy': '## Estrategia de pruebas',
        'Unanswered questions prevent specification approval.': 'Las preguntas sin respuesta impiden aprobar la especificación.',
        'No outstanding clarifications.': 'No hay aclaraciones pendientes.',
        '**PENDING**': '**PENDIENTE**',
        '- To be agreed': '- Por acordar',
        '- No additional decisions': '- Ninguna decisión adicional',
        '- To be assessed': '- Por evaluar',
        '| Task | Status | Requirements | Dependencies | Evidence |': '| Tarea | Estado | Requisitos | Dependencias | Evidencias |',
        'The engine checks structure and evidence file existence; it does NOT execute or certify checks.': 'El motor comprueba la estructura y la existencia de archivos de evidencia; NO ejecuta ni certifica las comprobaciones.',
        'No accepted evidence has been recorded yet.': 'Todavía no se han registrado evidencias aceptadas.',
    }
    result = []
    for line in body.splitlines():
        translated = exact.get(line, line)
        for old, new in prefixes.items():
            if line.startswith(old):
                translated = new + line[len(old):]
                break
        result.append(translated)
    return '\n'.join(result) + '\n'
