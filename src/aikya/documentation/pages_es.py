"""Deterministic Spanish templates for Aikya living documentation only."""
from __future__ import annotations
from typing import Any
MARK = ""
def flat(value:Any)->str:
    return str(value).replace('\\','/').replace('\n',' ').replace('|','/').replace('`',"'").strip()

def pages(profile:dict, modules:list[dict]) -> dict[str,str]:
    name=flat(profile['name'])
    tech=(f"Backend: {flat(profile['backend'])} ({flat(profile['backend_framework'])}); Frontend: {flat(profile['frontend'])}; Móvil: {flat(profile['mobile'])} ({flat(profile['mobile_framework'])})."
          if profile.get('project_type','development')=='development' else
          "Proyecto "+flat(profile['project_type'])+" independiente; no requiere código de aplicación.")
    installed='\n'.join(f"- `{flat(m['path'])}`: {flat(m['role'])}/{flat(m['technology'])} (detección heurística; verificar)." for m in modules) or '- Aún no se han creado los módulos de aplicación.'
    is_existing=profile['mode']=='existing'
    pages={
    'aikya/docs/README.md': f'''# Documentación — {name}

La documentación de este repositorio es parte del entregable. Una modificación de código, tests, seguridad, infraestructura o arquitectura **debe** actualizar sus documentos relacionados en la misma petición y dejar trazabilidad.

## Índice

- [Visión general](overview.md)
- [Plan y roadmap](plan/roadmap.md)
- [Catálogo de funcionalidades](features/index.md)
- [Incidencias y bugs](bugs/index.md)
- [Seguridad](security/security.md)
- [Arquitectura](architecture/overview.md)
- [Despliegue](operations/deployment.md)
- [Observabilidad](operations/observability.md)
- [Calidad y pruebas](quality/testing.md)
- [Decisiones de arquitectura (ADR)](decisions/README.md)
- [Bitácora por petición](changes/README.md)
- [Bootstrap técnico](harness/bootstrap.md)
- [Skills del proyecto](skills.md)

## Política documental

Cada tarea que cambia artefactos técnicos debe: (1) leer el contexto, (2) actualizar páginas impactadas con datos reales, (3) añadir `aikya/docs/changes/REQ-*.md` y (4) aportar evidencias de verificación. Una consulta sin cambios no requiere modificación documental.

La validación de estructura y diffs **no garantiza** exactitud semántica; revisarla en PR.
''',
    'aikya/docs/overview.md': f'''# Visión general — {name}

## Propósito

Producto **{name}**. Objetivos de negocio y usuarios finales por definir con el equipo propietario. Este documento establece el contexto técnico conocido, no inventa requisitos.

## Stack acordado en entrevista

{tech}

- Arquitectura: **{flat(profile['architecture'])}**.
- Base de datos: **{flat(profile['database'])}**.
- API: **{flat(profile['api_style'])}**.
- Identidad: **{flat(profile['auth'])}**.
- CI: **{flat(profile['ci'])}**; despliegue: **{flat(profile['deployment'])}**.

## Estado de implementación

{'Proyecto existente: confirmar el comportamiento inspeccionando el código antes de describirlo como operativo.' if is_existing else 'Proyecto nuevo: solo harness e infraestructura inicial. El código de negocio se genera o desarrolla posteriormente.'}

{installed}

## Documentos vinculados

[Roadmap](plan/roadmap.md) · [Features](features/index.md) · [Seguridad](security/security.md) · [Arquitectura](architecture/overview.md).
''',
    'aikya/docs/plan/roadmap.md': '''# Plan y roadmap

## Objetivos

- P0: validar el alcance, dependencias, versiones y criterios de aceptación con el equipo.
- P1: generar o revisar los módulos de aplicación y configurar quality gates ejecutables.
- P2: implementar funcionalidades priorizadas con pruebas, seguridad y observabilidad.
- P3: definir estrategia de despliegue, rollbacks y operación.

## Tabla de seguimiento

| ID | Objetivo / hito | Estado | Criterios de aceptación |
|---|---|---|---|
| PLAN-001 | Entrevista técnica y perfil | Registrado | `.harness/project-profile.json` presente |
| PLAN-002 | Scaffold y validación SDK | Pendiente | Módulos generados y comprobados |
| PLAN-003 | Pruebas + pipeline reales | Pendiente | Quality gates obligatorios pasan |

Registra nuevas historias/fechas sólo después de confirmar su alcance; cada feature se relaciona con este roadmap.
''',
    'aikya/docs/features/index.md': '''# Catálogo de funcionalidades

## Estado inicial

Aún no se ha documentado ninguna funcionalidad implementada por este harness. En proyectos existentes, inventariar el código antes de describir prestaciones.

## Convención

Para cada feature mantener identificador `FEAT-NNN`, propósito, historia de usuario, criterios de aceptación, endpoints/pantallas, impacto móvil, contratos, pruebas y estado. Enlazar una ficha `aikya/docs/features/FEAT-NNN.md` cuando sea compleja.

| ID | Feature | Estado | Documentación / pruebas |
|---|---|---|---|
| — | Sin features registradas | Por inventariar | — |
''',
    'aikya/docs/bugs/index.md': '''# Registro de incidencias y bugs

## Estado inicial

No hay incidencias registradas en la instalación. No significa que la aplicación esté libre de fallos.

## Convención

Cada bug debe tener `BUG-NNN`, síntoma, impacto, pasos de reproducción, causa raíz confirmada o hipótesis, corrección, test de regresión y estado. Los cambios de comportamiento deben actualizar también la feature correspondiente cuando aplique.

| ID | Severidad | Estado | Reproducción / regresión |
|---|---|---|---|
| — | — | Sin registros | — |
''',
    'aikya/docs/security/security.md': f'''# Seguridad y privacidad

## Postura inicial

Identidad prevista: **{flat(profile['auth'])}**. La entrevista no constituye auditoría, pentest ni revisión de cumplimiento. Clasificación de datos, amenazas y riesgos concretos por evaluar.

## Requisitos de ingeniería

- No versionar ni mostrar secretos o archivos `.env` privados; usar gestor de secretos.
- Diseñar autenticación/autorización por recurso y mínimos privilegios; revisar CORS/CSRF según contexto.
- Gestionar dependencias con análisis de vulnerabilidades, actualizaciones y SBOM cuando se implemente.
- Registrar errores sin tokens ni PII; validar y limitar entradas; proteger endpoints y credenciales.
- En móvil, usar almacenamiento seguro y requisitos de firma/distribución de tiendas.

## Registro de riesgos

| ID | Riesgo | Control / responsable | Estado |
|---|---|---|---|
| SEC-001 | Modelo de amenazas no evaluado | Revisar flujos y datos | Pendiente |
| SEC-002 | Escaneos SAST/dep. no configurados | Integrar en CI | Pendiente |

Registrar hallazgos confirmados y mitigaciones sin exponer detalles explotables ni credenciales.
''',
    'aikya/docs/architecture/overview.md': f'''# Arquitectura técnica

## Estilo y módulos

Arquitectura elegida: **{flat(profile['architecture'])}**. La decisión debe contrastarse con las restricciones y necesidades del producto; no se asume un diseño definitivo sin ADR.

{tech}

{installed}

## Límites y contratos

- Separar contratos de API, reglas de dominio, infraestructura y clientes.
- Definir responsabilidad de cada módulo y dependencias autorizadas antes del scaffold.
- Para Next.js con React integrado: evitar duplicar un frontend independiente sin motivo.
- Para Android/iOS: diferenciar aplicaciones nativas de runtime compartido.

## Decisiones

Ver [ADR](../decisions/README.md). La documentación de arquitectura se actualiza al modificar contratos, módulos, esquemas o estrategias de integración.
''',
    'aikya/docs/operations/deployment.md': f'''# Despliegue y operación

## Estrategia elegida

Objetivo: **{flat(profile['deployment'])}**; pipeline: **{flat(profile['ci'])}**. El bootstrap puede crear plantillas de Docker y GitHub Actions, pero no prueba una publicación real.

## Plan de implementación

1. Fijar SDKs, dependencias, secretos, redes y entornos.
2. Crear Dockerfiles adecuados al código y etapa real de build (ver `infra/docker/`).
3. Ejecutar pruebas, análisis de dependencias, build y escaneo de imagen.
4. Definir promoción, rollback, migraciones, healthchecks y revisiones de seguridad.
5. Para móvil, tratar signing, provisioning, tracks de prueba y publicación en tiendas por separado.

## Estado

No se afirma disponibilidad, CI verde, ni despliegues activos hasta realizar verificaciones reproducibles.
''',
    'aikya/docs/operations/observability.md': f'''# Observabilidad y operación SRE

## Estrategia

Selección de entrevista: **{flat(profile['observability'])}**.

## Contrato recomendado

- Logs estructurados con correlación `trace_id` y `request_id`, sin PII/secretos.
- Métricas de latencia, tasa de errores, throughput y saturación según tipo de servicio.
- Trazas OpenTelemetry en entrada API, llamadas HTTP/DB/colas y eventos relevantes.
- Para cliente móvil, instrumentación específica y control de privacidad.
- Definir SLIs, SLOs, alertas y runbooks una vez conocidas cargas y criticidad.

La plantilla en `infra/observability/` no instrumenta automáticamente las aplicaciones: requiere dependencias e integración comprobadas.
''',
    'aikya/docs/quality/testing.md': f'''# Estrategia de calidad y testing

Política elegida: **{flat(profile['quality'])}**.

- Unitarias: dominio, validación, estados y casos límite.
- Integración: persistencia/HTTP/servicios externos con dobles o entornos de prueba controlados.
- E2E: journeys web/móvil en browser/dispositivo/simulador real cuando aplique.
- Seguridad: SAST, dependencias y controles de configuración según criticidad.

## Quality gates

`python3 aikya/scripts/harness/run_checks.py` lee `harness.json`: si un check obligatorio carece de comando se marca `NOT_CONFIGURED` y la ejecución falla. Registra evidencias de los resultados en cada bitácora documental.

Los comandos concretos deben corresponder al código generado; no se presume que un proyecto vacío tiene pruebas pasadas.
''',
    'aikya/docs/decisions/README.md': '''# Registro de decisiones de arquitectura (ADR)

Crear `000N-titulo.md` por cada decisión que implique trade-offs, cambios de contrato, tecnología o impacto difícil de revertir.

Formato: contexto, decisión, opciones descartadas, consecuencias, riesgos, estado y fecha. No marcar como aceptada una propuesta pendiente de revisión.
''',
    'aikya/docs/decisions/0001-entrevista-stack.md': f'''# ADR-0001 — Perfil inicial de stack

- Estado: **Propuesto** (pendiente de revisar y aceptar por responsables).
- Contexto: decisiones registradas durante instalación del harness.
- Propuesta: {tech}
- Arquitectura propuesta: {flat(profile['architecture'])}.
- Criterio: mantener módulos independientes y tests reproducibles.
- Alternativas: deben evaluarse cuando haya requisitos funcionales y no funcionales concretos.
- Consecuencias: SDKs, equipos, licencias, seguridad, testing y despliegues aún deben validarse.

Referencia: `.harness/project-profile.json`.
''',
    'aikya/docs/changes/README.md': '''# Bitácora por petición

Cada cambio técnico se rastrea en un `REQ-YYYYMMDD-xxxxxxxx.md` vinculado al estado registrado por el hook `UserPromptSubmit`.

## Plantilla para nuevas entradas

```
# REQ-YYYYMMDD-xxxxxxxx — Título descriptivo

## Cambios
- Archivos de implementación modificados y comportamiento real.

## Evidencias
- Comandos ejecutados, resultados y controles pendientes; no inventar tests.

## Documentos actualizados
- Rutas de los documentos afectados y motivos.
```

El Stop hook bloquea tareas con código modificado pero sin trazabilidad documental actualizada; en CI se comprueban los diffs del PR. Revisar manualmente precisión y suficiencia.
''',
    }
    # Documentación visual sólo cuando el perfil requiere UI web o móvil.
    if profile.get('frontend') != 'none' or profile.get('mobile') != 'none':
        pages['aikya/docs/design/design-system.md'] = f'''# Sistema de diseño y experiencia de usuario

## Stack objetivo

- Frontend: **{flat(profile['frontend'])}**; móvil: **{flat(profile['mobile'])}** / {flat(profile['mobile_framework'])}.
- Skill de referencia: `ui-ux-pro-max` (terceros; requiere instalación autorizada).

## Diseño pendiente de implementar

- Definir tokens de color, tipografía, espaciado, breakpoints, componentes y estados.
- Accesibilidad: foco visible, teclado, contraste, lector de pantalla y reduced motion.
- Responsive: validar tamaños de teléfono/tablet/desktop y dispositivos objetivo.
- Las recomendaciones generadas por skill son propuestas: comprobar accesibilidad y compatibilidad en UI real.

## Registro de cambios UI

Actualizar este documento cuando cambien el sistema visual, tokens, patrones de interacción o navegación; incluir resultados verificables de pruebas visuales y de accesibilidad.
'''
        pages['aikya/docs/README.md'] += '\n- [Sistema de diseño y UI/UX](design/design-system.md)\n'
    pages['aikya/docs/harness/skills-comparison.md'] = '''# Auditoría Agent Skills — Harness v4

Estándar: https://agentskills.io/specification
Repositorio de referencia: https://github.com/agentskills/agentskills

## Evaluación del harness original

Las 8 skills del harness v3 contienen `SKILL.md`, `name` y `description` en YAML, en carpetas con igual nombre, siguiendo los campos requeridos por Agent Skills. `disable-model-invocation: true` es una **extensión de Claude Code**, no requisito de la especificación portable. Las skills se mantienen ligeras y se invocan selectivamente.

## Integraciones

| Herramienta | Uso | Carga contextual | Instalación |
|---|---|---|---|
| Ponytail | Reducir cambios superfluos y priorizar reutilización sin perder seguridad | Sólo cuando aplica desarrollar/revisar | Skill copiada desde checkout oficial; no se instala la interfaz `band` del plugin |
| Graphify | Navegación de dependencias por grafo para repos medianos/grandes | Consultas pequeñas; nunca introducir `graph.json` entero al contexto | CLI local graphifyy, skill de proyecto sin MCP |
| UI UX Pro Max | Design system, UX y accesibilidad web/móvil | Sólo proyectos con frontend o móvil y tareas de interfaz | CLI oficial npm desde usuario autorizado |

## Limitaciones

No hay garantía de reducción porcentual de tokens. El ahorro se comprobará con métricas del mismo conjunto de tareas y Claude Code, registrando tokens/coste, tiempo y calidad, no con afirmaciones de los repos upstream. Todos los paquetes de terceros deben revisarse y actualizarse deliberadamente.
'''
    pages['aikya/docs/harness/token-policy.md'] = '''# Política de contexto y tokens

1. Prioriza `aikya/docs/overview.md`, el perfil técnico y el archivo del módulo relevante; no leas todo `aikya/docs/`.
2. Para repos grandes, genera el índice Graphify **una vez**, al necesitarlo (`graphify . --no-viz`), y actualízalo sólo cuando cambie el código (`graphify update .`, tras verificar soporte CLI). Si no hay índice, no lo supongas.
3. Prefiere `graphify query "pregunta concreta"` o consultas de rutas frente a cargar `graphify-out/GRAPH_REPORT.md` o `graph.json` en el contexto. Comprueba hallazgos críticos leyendo archivos fuente.
4. Aplica ideas de Ponytail: examina código existente antes de escribir, evita dependencias superfluas, **no** reduzcas seguridad, pruebas, accesibilidad o manejo de errores.
5. Activa UI UX Pro Max para nuevas interfaces/diseño y revisión UX, no para API/infraestructura. Guarda design tokens aprobados en `aikya/docs/design/design-system.md`.
6. Mantén la respuesta acotada: archivos modificados, pruebas, riesgos y docs actualizados. Evita duplicar documentación o informes de agentes sin valor.
7. Subagentes sólo si aportan especialización, aislamiento útil o revisión independiente; para cambios triviales, ejecución directa.
8. No indexes, instales, sincronicies ni llames a servicios externos automáticamente por petición. Descargas/updates requieren aprobación y auditoría.
'''
    # Sólo se crean documentos especializados para tecnologías seleccionadas.
    info = profile.get('infrastructure', {})
    if isinstance(info, dict) and (
        info.get('iac') not in (None,'none','existing') or
        info.get('configuration_management') == 'ansible' or
        info.get('containers',{}).get('enabled',False) or
        info.get('orchestration') not in (None,'none')
    ):
        pages['aikya/docs/infrastructure/README.md'] = '''# Infrastructure & DevOps

La infraestructura de aplicación vive bajo infra/ (Terraform, Ansible, Kubernetes)
y los Dockerfiles junto a cada aplicación. Las decisiones, el plan y las verificaciones
se documentan aquí. Una plantilla creada NO está desplegada.
Ejecuta /aikya-infra plan y solicita aprobación antes de generate.
Nunca versionar secretos, estados Terraform ni inventarios con credenciales.
'''
        pages['aikya/docs/infrastructure/architecture.md'] = (
            '# Arquitectura Infrastructure & DevOps\\n\\n'
            '- Plataforma: '+flat(info.get('provider','none'))+'\n'
            '- IaC: '+flat(info.get('iac','none'))+'\n'
            '- Configuración: '+flat(info.get('configuration_management','none'))+'\n'
            '- Orquestación: '+flat(info.get('orchestration','none'))+'\n'
            '- Despliegue Kubernetes: '+flat(info.get('deployment_method','none'))+'\n'
            '- Entornos: '+', '.join(flat(x) for x in info.get('environments',[]))+'\n'
            '\nRevisar backend remoto, secretos, permisos, costes y despliegue antes de ejecutar cambios.\\n')
        pages['aikya/docs/README.md'] += '\\n- [Infraestructura y DevOps](infrastructure/README.md)\\n'
    if profile.get('project_type','development')!='development':
        kind=profile['project_type']
        pages['aikya/docs/overview.md']=f'# Visión general — {name}\n\nProyecto **{kind}** independiente de backend, frontend o móvil.\n'
        pages['aikya/docs/plan/roadmap.md']=(
            '# Roadmap Infrastructure & DevOps\n\n'
            '- P0: confirmar proveedor, entornos, acceso y seguridad.\n'
            '- P1: presentar y aprobar /aikya-infra plan.\n'
            '- P2: generar sólo artefactos autorizados y validar localmente.\n'
            '- P3: desplegar únicamente tras autorización independiente.\n')
        pages['aikya/docs/features/index.md']=(
            '# Capacidades de infraestructura y despliegue\n\n'
            'Inventariar módulos Terraform, roles Ansible, Dockerfiles y manifests reales, '
            'no funcionalidades ficticias de aplicaciones.\n')
        pages['aikya/docs/README.md'] += (
            '\n**Modo '+kind+'**: sin apps/, contracts/ ni packages/; '
            'usar /aikya-infra plan antes de generar infraestructura.\n')
    from aikya.documentation.layout import template_pages
    return template_pages(profile, modules, pages, 'es')
