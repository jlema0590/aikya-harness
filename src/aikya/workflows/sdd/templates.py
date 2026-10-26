"""Offline Aikya SDD roles composed exclusively from packaged reference templates.

Aikya owns requirement IDs, approvals and compatibility fields. The reference collection supplies
drafting structure; examples and proposed actions are never project facts.
"""
from __future__ import annotations
from aikya.resource_paths import source_root,source_path
from pathlib import Path
from aikya.documentation.layout import stamp


SOURCE='aikya-template/docs/'


def _entry(filename, reference, fields):
    return {'filename':filename,'source':SOURCE+reference+'.md',
            'reference':reference,'fields':fields}


CATALOG = {
    'feature':_entry('feature.spec.md','general-swe/requirements/product-requirements-document',{
        'owner':('Owner','Responsable'),'context':('Context','Contexto'),
        'non_goals':('Excluded scope','Fuera de alcance'),'edge_cases':('Boundary behavior','Casos límite'),
        'deliverables':('Expected deliverables','Entregables previstos'),
        'rollout':('Delivery sequence','Secuencia de entrega'),'rollback':('Recovery approach','Plan de reversión'),
        'evidence_required':('Evidence to collect','Evidencias necesarias')}),
    'api':_entry('api.spec.md','general-swe/foundations/interface-control-document',{
        'owner':('Owner','Responsable'),'endpoint':('Endpoint contract','Contrato del endpoint'),
        'request':('Request shape','Estructura de petición'),'responses':('Response behavior','Comportamiento de respuestas'),
        'authorization':('Access rules','Reglas de acceso'),'idempotency':('Retry and replay rules','Reintentos e idempotencia'),
        'compatibility':('Consumer compatibility','Compatibilidad con consumidores'),
        'checks':('Contract checks','Comprobaciones del contrato'),'rollback':('Recovery approach','Plan de reversión')}),
    'database':_entry('database.spec.md','general-swe/foundations/data-model',{
        'owner':('Owner','Responsable'),'tables':('Affected data structures','Estructuras de datos afectadas'),
        'columns':('Field definitions','Definiciones de campos'),'constraints':('Data invariants','Invariantes de datos'),
        'indexes':('Query and index impact','Impacto en consultas e índices'),
        'migration':('Migration sequence','Secuencia de migración'),
        'compatibility':('Read/write compatibility','Compatibilidad de lectura y escritura'),
        'checks':('Data verification','Verificación de datos'),'rollback':('Recovery limits','Límites de reversión')}),
    'spec':_entry('spec.md','ai-assisted-development/specification/agent-task-specification',{
        'owner':('Owner','Responsable'),'context':('Problem context','Contexto del problema'),
        'non_goals':('Excluded scope','Fuera de alcance'),'evidence_required':('Evidence to collect','Evidencias necesarias'),
        'rollback':('Recovery approach','Plan de reversión')}),
    'design':_entry('design.md','general-swe/foundations/technical-design-document',{
        'owner':('Owner','Responsable'),'context':('Design context','Contexto del diseño'),
        'alternatives':('Alternatives and rationale','Alternativas y justificación'),
        'interfaces':('Affected interfaces','Interfaces afectadas'),'constraints':('Design constraints','Restricciones de diseño'),
        'rollout':('Delivery sequence','Secuencia de entrega'),'rollback':('Recovery approach','Plan de reversión')}),
    'tasks':_entry('tasks.md','ai-assisted-development/foundations/task-plan',{
        'owner':('Owner','Responsable'),'allowed_files':('Reviewed file scope','Archivos dentro del alcance'),
        'checks':('Checks to execute','Comprobaciones previstas'),'done_when':('Completion conditions','Condiciones de finalización')}),
    'evidence':_entry('evidence.md','general-swe/foundations/test-summary-report',{
        'owner':('Owner','Responsable'),'release':('Release context','Contexto de publicación'),
        'operational':('Observed operational evidence','Evidencias operativas observadas'),
        'manual_checks':('Recorded manual checks','Comprobaciones manuales registradas'),
        'known_gaps':('Unverified areas','Áreas sin verificar'),'stop_signal':('Stop conditions','Condiciones de parada')}),
    'review':_entry('review.md','general-swe/foundations/code-review-guidelines',{
        'reviewer':('Reviewer','Revisor'),'scope':('Observed change scope','Alcance de cambios observado'),
        'spec_alignment':('Requirement coverage','Cobertura de requisitos'),
        'evidence':('Reviewed evidence','Evidencias revisadas'),'decision':('Review conclusion','Conclusión de revisión'),
        'follow_up':('Follow-up work','Trabajo pendiente')}),
    'constitution':_entry('constitution.md','ai-assisted-development/foundations/agent-instructions-file',{
        'owner':('Owner','Responsable'),'applies_to':('Applicable scope','Ámbito de aplicación'),
        'principles':('Engineering principles','Principios de ingeniería'),
        'gates':('Required reviews','Revisiones necesarias'),'ai_rules':('Agent boundaries','Límites de los agentes'),
        'exceptions':('Reviewed exceptions','Excepciones revisadas'),'review_date':('Review date','Fecha de revisión')})
}
FOUNDATIONS = {name:item['reference']+'.md' for name,item in CATALOG.items()}
CATALOG['design']['fields'].update({
    'goals':('Design goals','Objetivos del diseño'),
    'non_goals':('Excluded design scope','Fuera del alcance del diseño'),
    'open_questions':('Unresolved design questions','Preguntas de diseño abiertas')})
CATALOG['tasks']['fields'].update({
    'out_of_scope':('Excluded task scope','Fuera del alcance de la tarea'),
    'constraints':('Task constraints','Restricciones de la tarea')})
CATALOG['evidence']['fields'].update({
    'assessment':('Result assessment','Evaluación de resultados'),
    'residual_risk':('Residual risk','Riesgo residual')})

SPEC_TEMPLATES = frozenset(('spec','feature','api','database'))


def catalog() -> dict:
    return {name:{'filename':item['filename'],'source':item['source'],
                  'section_keys':list(item['fields']),
                  'foundations':FOUNDATIONS.get(name)} for name,item in CATALOG.items()}


def normalize_sections(name: str, value=None) -> dict[str,str]:
    if name not in CATALOG:raise ValueError('Unknown SDD template: '+str(name))
    if value is None:return {}
    if not isinstance(value,dict) or not set(value).issubset(CATALOG[name]['fields']):
        raise ValueError('Unknown or invalid sections for SDD template '+name)
    result={}
    for key,text in value.items():
        if not isinstance(text,str) or not text.strip() or len(text)>4000 or '\x00' in text:
            raise ValueError('Template sections require nonempty text of at most 4000 characters: '+str(key))
        result[key]=text.strip()
    if sum(map(len,result.values()))>20000:raise ValueError('Template sections exceed the document limit')
    return result


def render_sections(name: str, sections=None, language='en') -> str:
    values=normalize_sections(name,sections)
    return '\n\n'.join('## '+labels[language=='es']+'\n\n'+values[key]
                        for key,labels in CATALOG[name]['fields'].items() if key in values)


def source_note(name: str, language='en') -> str:
    es=language=='es'
    return ('Referencia de plantilla: ' if es else 'Template reference: ')+'`'+CATALOG[name]['source']+'`. '+('Composición de Aikya; los identificadores, campos de compatibilidad y aprobaciones pertenecen a Aikya.' if es else 'Aikya composition; identifiers, compatibility fields and approvals belong to Aikya.')



def starter(name: str) -> str:
    if name not in CATALOG:raise ValueError('Unknown SDD template: '+str(name))
    base=source_path(source_root(), 'sdd-templates')
    target=base/CATALOG[name]['filename']
    if base.is_symlink() or target.is_symlink():raise ValueError('Symlinked template assets are not supported')
    return stamp(target.read_text(encoding='utf8'))
