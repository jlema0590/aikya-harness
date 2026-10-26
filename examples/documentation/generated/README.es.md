# Ejemplos de documentos generados por Aikya

Este catálogo es una instantánea previa al cambio de standard a ODD. Para la
continuidad nueva, consulta [examples/odd](../../odd/) y [ODD](../../../docs/ODD.md).

Todos estos ejemplos son **simulados** y se han obtenido con los generadores reales.
La documentación de ejemplo está en inglés; esta guía explica su uso en español.
Milkeles es la única fuente externa de plantillas. Aikya conserva sus propias reglas,
identificadores, trazabilidad, política de idioma y aprobaciones.

No se crean todos estos documentos al iniciar un proyecto. Cada comando crea o
actualiza únicamente lo que corresponde a su perfil y a los datos disponibles.
Las 120 plantillas del catálogo son opciones explícitas; no son 120 informes de onboarding.

Los resultados SDD usan evidencia de una simulación etiquetada. El estado conserva
`independently_executed: false`. No se ejecutó una aplicación, no se desplegó y no
se aprobó una publicación. Algunas rutas internas en las muestras apuntan a su
proyecto original simulado; son snapshots documentales, no proyectos ejecutables.

## Estado histórico y compatibilidad

Esta galería conserva los nombres y resultados previos a ODD. El comando público
actual es `/aikya-arc-review`; `/aikya-architecture-review` se conserva debajo como
referencia histórica. Los 253 documentos con hash no se han regenerado ni validan
la ejecución de una aplicación. La ruta `fixture-evidence.log` que aparece en
`standard/summary.md` pertenecía al proyecto sintético original y no se distribuye;
el enlace se conserva como procedencia histórica, no como evidencia disponible.
La galería permanece en el repositorio y se omite del runtime registrado.

## Cuándo se generan

| Uso | Documentos y condiciones |
|---|---|
| /aikya-init | Índice, overview, arquitectura, herramientas, skills y documentos respaldados por el perfil; los apartados de seguridad, pruebas, operaciones e infraestructura son condicionales. |
| /aikya-init en modo SDD | Lo anterior más specs/README.md; una especificación no se crea hasta recibir requisitos reales. |
| /aikya-analyze | Documentos respaldados por lo observado; la vista previa no escribe. El informe técnico de análisis está en .aikya/analysis/report.md. |
| /aikya-architecture-review | Revisión de solo lectura; actualizar arquitectura, ADR o diseño requiere una edición autorizada. |
| /aikya-feature | En estándar: features/<nombre>/spec.md con objetivo y aceptación; diseño o ADR solo cuando hagan falta. En SDD usa tareas aprobadas. |
| /aikya-mobile-feature | Igual, con las plataformas realmente seleccionadas. |
| /aikya-bugfix | bugs/bugs.md solo con un BUG-NNN único y reproducción; en SDD la implementación sigue su tarea aprobada. |
| /aikya-specify | spec.md; clarifications.md solo si hay preguntas. |
| /aikya-plan | design.md y plan.md dentro de la especificación. |
| /aikya-tasks | tasks.md con requisitos, dependencias y condiciones de finalización. |
| /aikya-implement | Utiliza la tarea autorizada y actualiza su progreso; no duplica la especificación. |
| /aikya-tests | Estrategia, casos o informe según la necesidad; los informes necesitan evidencias existentes. |
| /aikya-verify | verification.md y evidence.md al registrar resultados aportados; no prueba por sí solo que se ejecutara un comando. |
| /aikya-sdd-status | Lee el estado sin generar otro informe. Hay un ejemplo JSON junto a la especificación SDD. |
| /aikya-install-skill | tools/skill-comparison.md únicamente al registrar una instalación solicitada; la muestra no instala nada. |
| Cambios de ingeniería | changes/REQ-*.md con cambios, evidencias y documentos afectados. |
| Catálogo Milkeles | Documentos opcionales con contenido revisado y destino seguro; no modifica aprobaciones SDD. |

CLAUDE.md y las reglas de perfil son instrucciones de la raíz del proyecto; las
skills y agentes instalados son activos del harness, no informes vivos adicionales.
La galería muestra las instrucciones de perfil y CLAUDE.md, y el inventario generado
identifica los agentes/skills disponibles. El código y los archivos JSON mantienen
su formato y no llevan el pie Markdown.

## Qué plantilla se utiliza

| Documento | Referencia de Milkeles y adaptación de Aikya |
|---|---|
| overview.md | onboarding-guide, junto con las decisiones y la guía de inicio de Aikya |
| architecture/architecture-overview.md | architecture-overview |
| features/<nombre>/spec.md | technical-design-document, junto con objetivo y criterios AC de Aikya |
| architecture/designs/<nombre>.md | technical-design-document |
| decisions/<nombre>.md | architecture-decision-record |
| bugs/bugs.md | bug-report adaptado al registro acumulativo BUG-NNN |
| plan/testing.md | test-strategy |
| plan/test-cases/<nombre>.md | test-case-specification |
| quality/test-reports/<nombre>.md | test-summary-report con rutas reales de evidencia |
| SDD spec.md | agent-task-specification; product-requirements-document para feature; interface-control-document para API; data-model para base de datos |
| SDD design.md / tasks.md / evidence.md | technical-design-document / task-plan / test-summary-report |
| SDD review.md / constitution.md | code-review-guidelines / agent-instructions-file |
| CLAUDE.md | agent-instructions-file junto con reglas y perfil propios de Aikya |
| Índices, políticas, inventarios, registros REQ, estado SDD, clarifications.md, plan.md y verification.md | Formatos propios de Aikya que conservan la trazabilidad y las aprobaciones; no se atribuyen a otra biblioteca |

Los identificadores completos y enlaces de origen están en cada ejemplo del catálogo
y en la [guía SDD](../../../docs/SDD_TEMPLATES.md). La referencia de Milkeles aporta
estructura; los campos de compatibilidad, las comprobaciones y las aprobaciones
siguen perteneciendo a Aikya.

## Ejemplos por familia


### Inicialización por tipo de proyecto

| Ejemplo | Uso | Ruta de salida en el proyecto |
|---|---|---|
| [development/aikya/docs/README.md](init/development/aikya/docs/README.md) | /aikya-init | `aikya/docs/README.md` |
| [development/aikya/docs/architecture/architecture-overview.md](init/development/aikya/docs/architecture/architecture-overview.md) | /aikya-init | `aikya/docs/architecture/architecture-overview.md` |
| [development/aikya/docs/architecture/infrastructure.md](init/development/aikya/docs/architecture/infrastructure.md) | /aikya-init | `aikya/docs/architecture/infrastructure.md` |
| [development/aikya/docs/changes/README.md](init/development/aikya/docs/changes/README.md) | /aikya-init | `aikya/docs/changes/README.md` |
| [development/aikya/docs/decisions/0001-entrevista-stack.md](init/development/aikya/docs/decisions/0001-entrevista-stack.md) | /aikya-init | `aikya/docs/decisions/0001-entrevista-stack.md` |
| [development/aikya/docs/decisions/README.md](init/development/aikya/docs/decisions/README.md) | /aikya-init | `aikya/docs/decisions/README.md` |
| [development/aikya/docs/indice.md](init/development/aikya/docs/indice.md) | /aikya-init | `aikya/docs/indice.md` |
| [development/aikya/docs/infrastructure/README.md](init/development/aikya/docs/infrastructure/README.md) | /aikya-init | `aikya/docs/infrastructure/README.md` |
| [development/aikya/docs/infrastructure/plan.md](init/development/aikya/docs/infrastructure/plan.md) | /aikya-init | `aikya/docs/infrastructure/plan.md` |
| [development/aikya/docs/operations/deployment.md](init/development/aikya/docs/operations/deployment.md) | /aikya-init | `aikya/docs/operations/deployment.md` |
| [development/aikya/docs/overview.md](init/development/aikya/docs/overview.md) | /aikya-init | `aikya/docs/overview.md` |
| [development/aikya/docs/plan/roadmap.md](init/development/aikya/docs/plan/roadmap.md) | /aikya-init | `aikya/docs/plan/roadmap.md` |
| [development/aikya/docs/plan/testing.md](init/development/aikya/docs/plan/testing.md) | /aikya-init | `aikya/docs/plan/testing.md` |
| [development/aikya/docs/skills.md](init/development/aikya/docs/skills.md) | /aikya-init | `aikya/docs/skills.md` |
| [development/aikya/docs/tools/agents.md](init/development/aikya/docs/tools/agents.md) | /aikya-init | `aikya/docs/tools/agents.md` |
| [development/aikya/docs/tools/token-policy.md](init/development/aikya/docs/tools/token-policy.md) | /aikya-init | `aikya/docs/tools/token-policy.md` |
| [development/CLAUDE.md](init/development/CLAUDE.md) | /aikya-init | `CLAUDE.md` |
| [development/claude/rules/00-project-profile.md](init/development/claude/rules/00-project-profile.md) | /aikya-init | `.claude/rules/00-project-profile.md` |
| [mobile/aikya/docs/README.md](init/mobile/aikya/docs/README.md) | /aikya-init | `aikya/docs/README.md` |
| [mobile/aikya/docs/architecture/architecture-overview.md](init/mobile/aikya/docs/architecture/architecture-overview.md) | /aikya-init | `aikya/docs/architecture/architecture-overview.md` |
| [mobile/aikya/docs/changes/README.md](init/mobile/aikya/docs/changes/README.md) | /aikya-init | `aikya/docs/changes/README.md` |
| [mobile/aikya/docs/decisions/0001-entrevista-stack.md](init/mobile/aikya/docs/decisions/0001-entrevista-stack.md) | /aikya-init | `aikya/docs/decisions/0001-entrevista-stack.md` |
| [mobile/aikya/docs/decisions/README.md](init/mobile/aikya/docs/decisions/README.md) | /aikya-init | `aikya/docs/decisions/README.md` |
| [mobile/aikya/docs/indice.md](init/mobile/aikya/docs/indice.md) | /aikya-init | `aikya/docs/indice.md` |
| [mobile/aikya/docs/operations/deployment.md](init/mobile/aikya/docs/operations/deployment.md) | /aikya-init | `aikya/docs/operations/deployment.md` |
| [mobile/aikya/docs/overview.md](init/mobile/aikya/docs/overview.md) | /aikya-init | `aikya/docs/overview.md` |
| [mobile/aikya/docs/plan/roadmap.md](init/mobile/aikya/docs/plan/roadmap.md) | /aikya-init | `aikya/docs/plan/roadmap.md` |
| [mobile/aikya/docs/plan/testing.md](init/mobile/aikya/docs/plan/testing.md) | /aikya-init | `aikya/docs/plan/testing.md` |
| [mobile/aikya/docs/skills.md](init/mobile/aikya/docs/skills.md) | /aikya-init | `aikya/docs/skills.md` |
| [mobile/aikya/docs/tools/agents.md](init/mobile/aikya/docs/tools/agents.md) | /aikya-init | `aikya/docs/tools/agents.md` |
| [mobile/aikya/docs/tools/token-policy.md](init/mobile/aikya/docs/tools/token-policy.md) | /aikya-init | `aikya/docs/tools/token-policy.md` |
| [mobile/CLAUDE.md](init/mobile/CLAUDE.md) | /aikya-init | `CLAUDE.md` |
| [mobile/claude/rules/00-project-profile.md](init/mobile/claude/rules/00-project-profile.md) | /aikya-init | `.claude/rules/00-project-profile.md` |
| [infrastructure/aikya/docs/README.md](init/infrastructure/aikya/docs/README.md) | /aikya-init | `aikya/docs/README.md` |
| [infrastructure/aikya/docs/architecture/architecture-overview.md](init/infrastructure/aikya/docs/architecture/architecture-overview.md) | /aikya-init | `aikya/docs/architecture/architecture-overview.md` |
| [infrastructure/aikya/docs/architecture/infrastructure.md](init/infrastructure/aikya/docs/architecture/infrastructure.md) | /aikya-init | `aikya/docs/architecture/infrastructure.md` |
| [infrastructure/aikya/docs/changes/README.md](init/infrastructure/aikya/docs/changes/README.md) | /aikya-init | `aikya/docs/changes/README.md` |
| [infrastructure/aikya/docs/decisions/0001-entrevista-stack.md](init/infrastructure/aikya/docs/decisions/0001-entrevista-stack.md) | /aikya-init | `aikya/docs/decisions/0001-entrevista-stack.md` |
| [infrastructure/aikya/docs/decisions/README.md](init/infrastructure/aikya/docs/decisions/README.md) | /aikya-init | `aikya/docs/decisions/README.md` |
| [infrastructure/aikya/docs/indice.md](init/infrastructure/aikya/docs/indice.md) | /aikya-init | `aikya/docs/indice.md` |
| [infrastructure/aikya/docs/infrastructure/README.md](init/infrastructure/aikya/docs/infrastructure/README.md) | /aikya-init | `aikya/docs/infrastructure/README.md` |
| [infrastructure/aikya/docs/infrastructure/plan.md](init/infrastructure/aikya/docs/infrastructure/plan.md) | /aikya-init | `aikya/docs/infrastructure/plan.md` |
| [infrastructure/aikya/docs/overview.md](init/infrastructure/aikya/docs/overview.md) | /aikya-init | `aikya/docs/overview.md` |
| [infrastructure/aikya/docs/plan/roadmap.md](init/infrastructure/aikya/docs/plan/roadmap.md) | /aikya-init | `aikya/docs/plan/roadmap.md` |
| [infrastructure/aikya/docs/plan/testing.md](init/infrastructure/aikya/docs/plan/testing.md) | /aikya-init | `aikya/docs/plan/testing.md` |
| [infrastructure/aikya/docs/skills.md](init/infrastructure/aikya/docs/skills.md) | /aikya-init | `aikya/docs/skills.md` |
| [infrastructure/aikya/docs/tools/agents.md](init/infrastructure/aikya/docs/tools/agents.md) | /aikya-init | `aikya/docs/tools/agents.md` |
| [infrastructure/aikya/docs/tools/token-policy.md](init/infrastructure/aikya/docs/tools/token-policy.md) | /aikya-init | `aikya/docs/tools/token-policy.md` |
| [infrastructure/CLAUDE.md](init/infrastructure/CLAUDE.md) | /aikya-init | `CLAUDE.md` |
| [infrastructure/claude/rules/00-project-profile.md](init/infrastructure/claude/rules/00-project-profile.md) | /aikya-init | `.claude/rules/00-project-profile.md` |
| [devops/aikya/docs/README.md](init/devops/aikya/docs/README.md) | /aikya-init | `aikya/docs/README.md` |
| [devops/aikya/docs/architecture/architecture-overview.md](init/devops/aikya/docs/architecture/architecture-overview.md) | /aikya-init | `aikya/docs/architecture/architecture-overview.md` |
| [devops/aikya/docs/architecture/infrastructure.md](init/devops/aikya/docs/architecture/infrastructure.md) | /aikya-init | `aikya/docs/architecture/infrastructure.md` |
| [devops/aikya/docs/changes/README.md](init/devops/aikya/docs/changes/README.md) | /aikya-init | `aikya/docs/changes/README.md` |
| [devops/aikya/docs/decisions/0001-entrevista-stack.md](init/devops/aikya/docs/decisions/0001-entrevista-stack.md) | /aikya-init | `aikya/docs/decisions/0001-entrevista-stack.md` |
| [devops/aikya/docs/decisions/README.md](init/devops/aikya/docs/decisions/README.md) | /aikya-init | `aikya/docs/decisions/README.md` |
| [devops/aikya/docs/indice.md](init/devops/aikya/docs/indice.md) | /aikya-init | `aikya/docs/indice.md` |
| [devops/aikya/docs/infrastructure/README.md](init/devops/aikya/docs/infrastructure/README.md) | /aikya-init | `aikya/docs/infrastructure/README.md` |
| [devops/aikya/docs/infrastructure/plan.md](init/devops/aikya/docs/infrastructure/plan.md) | /aikya-init | `aikya/docs/infrastructure/plan.md` |
| [devops/aikya/docs/overview.md](init/devops/aikya/docs/overview.md) | /aikya-init | `aikya/docs/overview.md` |
| [devops/aikya/docs/plan/roadmap.md](init/devops/aikya/docs/plan/roadmap.md) | /aikya-init | `aikya/docs/plan/roadmap.md` |
| [devops/aikya/docs/plan/testing.md](init/devops/aikya/docs/plan/testing.md) | /aikya-init | `aikya/docs/plan/testing.md` |
| [devops/aikya/docs/skills.md](init/devops/aikya/docs/skills.md) | /aikya-init | `aikya/docs/skills.md` |
| [devops/aikya/docs/tools/agents.md](init/devops/aikya/docs/tools/agents.md) | /aikya-init | `aikya/docs/tools/agents.md` |
| [devops/aikya/docs/tools/token-policy.md](init/devops/aikya/docs/tools/token-policy.md) | /aikya-init | `aikya/docs/tools/token-policy.md` |
| [devops/CLAUDE.md](init/devops/CLAUDE.md) | /aikya-init | `CLAUDE.md` |
| [devops/claude/rules/00-project-profile.md](init/devops/claude/rules/00-project-profile.md) | /aikya-init | `.claude/rules/00-project-profile.md` |

### Análisis de proyectos existentes

| Ejemplo | Uso | Ruta de salida en el proyecto |
|---|---|---|
| [development/aikya/docs/README.md](analyze/development/aikya/docs/README.md) | /aikya-analyze | `aikya/docs/README.md` |
| [development/aikya/docs/architecture/architecture-overview.md](analyze/development/aikya/docs/architecture/architecture-overview.md) | /aikya-analyze | `aikya/docs/architecture/architecture-overview.md` |
| [development/aikya/docs/changes/README.md](analyze/development/aikya/docs/changes/README.md) | /aikya-analyze | `aikya/docs/changes/README.md` |
| [development/aikya/docs/indice.md](analyze/development/aikya/docs/indice.md) | /aikya-analyze | `aikya/docs/indice.md` |
| [development/aikya/docs/overview.md](analyze/development/aikya/docs/overview.md) | /aikya-analyze | `aikya/docs/overview.md` |
| [development/aikya/docs/plan/testing.md](analyze/development/aikya/docs/plan/testing.md) | /aikya-analyze | `aikya/docs/plan/testing.md` |
| [development/aikya/docs/skills.md](analyze/development/aikya/docs/skills.md) | /aikya-analyze | `aikya/docs/skills.md` |
| [development/aikya/docs/tools/agents.md](analyze/development/aikya/docs/tools/agents.md) | /aikya-analyze | `aikya/docs/tools/agents.md` |
| [development/aikya/docs/tools/token-policy.md](analyze/development/aikya/docs/tools/token-policy.md) | /aikya-analyze | `aikya/docs/tools/token-policy.md` |
| [development/CLAUDE.md](analyze/development/CLAUDE.md) | /aikya-analyze | `CLAUDE.md` |
| [development/aikya/analysis/report.md](analyze/development/aikya/analysis/report.md) | /aikya-analyze | `.aikya/analysis/report.md` |
| [development/claude/rules/00-project-profile.md](analyze/development/claude/rules/00-project-profile.md) | /aikya-analyze | `.claude/rules/00-project-profile.md` |
| [infrastructure/aikya/docs/README.md](analyze/infrastructure/aikya/docs/README.md) | /aikya-analyze | `aikya/docs/README.md` |
| [infrastructure/aikya/docs/architecture/architecture-overview.md](analyze/infrastructure/aikya/docs/architecture/architecture-overview.md) | /aikya-analyze | `aikya/docs/architecture/architecture-overview.md` |
| [infrastructure/aikya/docs/architecture/infrastructure.md](analyze/infrastructure/aikya/docs/architecture/infrastructure.md) | /aikya-analyze | `aikya/docs/architecture/infrastructure.md` |
| [infrastructure/aikya/docs/changes/README.md](analyze/infrastructure/aikya/docs/changes/README.md) | /aikya-analyze | `aikya/docs/changes/README.md` |
| [infrastructure/aikya/docs/indice.md](analyze/infrastructure/aikya/docs/indice.md) | /aikya-analyze | `aikya/docs/indice.md` |
| [infrastructure/aikya/docs/infrastructure/README.md](analyze/infrastructure/aikya/docs/infrastructure/README.md) | /aikya-analyze | `aikya/docs/infrastructure/README.md` |
| [infrastructure/aikya/docs/overview.md](analyze/infrastructure/aikya/docs/overview.md) | /aikya-analyze | `aikya/docs/overview.md` |
| [infrastructure/aikya/docs/plan/testing.md](analyze/infrastructure/aikya/docs/plan/testing.md) | /aikya-analyze | `aikya/docs/plan/testing.md` |
| [infrastructure/aikya/docs/skills.md](analyze/infrastructure/aikya/docs/skills.md) | /aikya-analyze | `aikya/docs/skills.md` |
| [infrastructure/aikya/docs/tools/agents.md](analyze/infrastructure/aikya/docs/tools/agents.md) | /aikya-analyze | `aikya/docs/tools/agents.md` |
| [infrastructure/aikya/docs/tools/token-policy.md](analyze/infrastructure/aikya/docs/tools/token-policy.md) | /aikya-analyze | `aikya/docs/tools/token-policy.md` |
| [infrastructure/CLAUDE.md](analyze/infrastructure/CLAUDE.md) | /aikya-analyze | `CLAUDE.md` |
| [infrastructure/aikya/analysis/report.md](analyze/infrastructure/aikya/analysis/report.md) | /aikya-analyze | `.aikya/analysis/report.md` |
| [infrastructure/claude/rules/00-project-profile.md](analyze/infrastructure/claude/rules/00-project-profile.md) | /aikya-analyze | `.claude/rules/00-project-profile.md` |
| [devops/aikya/docs/README.md](analyze/devops/aikya/docs/README.md) | /aikya-analyze | `aikya/docs/README.md` |
| [devops/aikya/docs/architecture/architecture-overview.md](analyze/devops/aikya/docs/architecture/architecture-overview.md) | /aikya-analyze | `aikya/docs/architecture/architecture-overview.md` |
| [devops/aikya/docs/architecture/infrastructure.md](analyze/devops/aikya/docs/architecture/infrastructure.md) | /aikya-analyze | `aikya/docs/architecture/infrastructure.md` |
| [devops/aikya/docs/changes/README.md](analyze/devops/aikya/docs/changes/README.md) | /aikya-analyze | `aikya/docs/changes/README.md` |
| [devops/aikya/docs/indice.md](analyze/devops/aikya/docs/indice.md) | /aikya-analyze | `aikya/docs/indice.md` |
| [devops/aikya/docs/infrastructure/README.md](analyze/devops/aikya/docs/infrastructure/README.md) | /aikya-analyze | `aikya/docs/infrastructure/README.md` |
| [devops/aikya/docs/operations/deployment.md](analyze/devops/aikya/docs/operations/deployment.md) | /aikya-analyze | `aikya/docs/operations/deployment.md` |
| [devops/aikya/docs/overview.md](analyze/devops/aikya/docs/overview.md) | /aikya-analyze | `aikya/docs/overview.md` |
| [devops/aikya/docs/plan/testing.md](analyze/devops/aikya/docs/plan/testing.md) | /aikya-analyze | `aikya/docs/plan/testing.md` |
| [devops/aikya/docs/skills.md](analyze/devops/aikya/docs/skills.md) | /aikya-analyze | `aikya/docs/skills.md` |
| [devops/aikya/docs/tools/agents.md](analyze/devops/aikya/docs/tools/agents.md) | /aikya-analyze | `aikya/docs/tools/agents.md` |
| [devops/aikya/docs/tools/token-policy.md](analyze/devops/aikya/docs/tools/token-policy.md) | /aikya-analyze | `aikya/docs/tools/token-policy.md` |
| [devops/CLAUDE.md](analyze/devops/CLAUDE.md) | /aikya-analyze | `CLAUDE.md` |
| [devops/aikya/analysis/report.md](analyze/devops/aikya/analysis/report.md) | /aikya-analyze | `.aikya/analysis/report.md` |
| [devops/claude/rules/00-project-profile.md](analyze/devops/claude/rules/00-project-profile.md) | /aikya-analyze | `.claude/rules/00-project-profile.md` |

### Features, arquitectura y pruebas

| Ejemplo | Uso | Ruta de salida en el proyecto |
|---|---|---|
| [overview.md](standard/overview.md) | /aikya-init | `aikya/docs/overview.md` |
| [architecture.md](standard/architecture.md) | /aikya-architecture-review | `aikya/docs/architecture/architecture-overview.md` |
| [feature.md](standard/feature.md) | /aikya-feature | `aikya/docs/features/synthetic-catalogue/spec.md` |
| [design.md](standard/design.md) | /aikya-feature | `aikya/docs/architecture/designs/synthetic-catalogue.md` |
| [decision.md](standard/decision.md) | /aikya-architecture-review | `aikya/docs/decisions/synthetic-catalogue.md` |
| [strategy.md](standard/strategy.md) | /aikya-tests | `aikya/docs/plan/testing.md` |
| [case.md](standard/case.md) | /aikya-tests | `aikya/docs/plan/test-cases/synthetic-catalogue.md` |
| [summary.md](standard/summary.md) | /aikya-tests | `aikya/docs/quality/test-reports/synthetic-catalogue.md` |
| [mobile-feature.md](standard/mobile-feature.md) | /aikya-mobile-feature | `aikya/docs/features/synthetic-catalogue/spec.md` |
| [bug-register.md](standard/bug-register.md) | /aikya-bugfix | `aikya/docs/bugs/bugs.md` |

### Registros propios de Aikya

| Ejemplo | Uso | Ruta de salida en el proyecto |
|---|---|---|
| [skill-comparison.md](native/skill-comparison.md) | /aikya-install-skill | `aikya/docs/tools/skill-comparison.md` |
| [REQ-20261022-01234567.md](native/REQ-20261022-01234567.md) | Authorized engineering change | `aikya/docs/changes/REQ-20261022-01234567.md` |

### SDD: especificaciones y ciclo completo

| Ejemplo | Uso | Ruta de salida en el proyecto |
|---|---|---|
| [spec/clarifications.md](sdd/spec/clarifications.md) | /aikya-clarify | `aikya/docs/specs/development/SPEC-001/clarifications.md` |
| [spec/design.md](sdd/spec/design.md) | /aikya-plan | `aikya/docs/specs/development/SPEC-001/design.md` |
| [spec/evidence.md](sdd/spec/evidence.md) | /aikya-verify | `aikya/docs/specs/development/SPEC-001/evidence.md` |
| [spec/plan.md](sdd/spec/plan.md) | /aikya-plan | `aikya/docs/specs/development/SPEC-001/plan.md` |
| [spec/review.md](sdd/spec/review.md) | Explicit reviewed document | `aikya/docs/specs/development/SPEC-001/review.md` |
| [spec/spec.md](sdd/spec/spec.md) | /aikya-specify | `aikya/docs/specs/development/SPEC-001/spec.md` |
| [spec/tasks.md](sdd/spec/tasks.md) | /aikya-tasks + /aikya-implement | `aikya/docs/specs/development/SPEC-001/tasks.md` |
| [spec/verification.md](sdd/spec/verification.md) | /aikya-verify | `aikya/docs/specs/development/SPEC-001/verification.md` |
| [feature/spec.md](sdd/feature/spec.md) | /aikya-specify | `aikya/docs/specs/development/SPEC-002/spec.md` |
| [api/spec.md](sdd/api/spec.md) | /aikya-specify | `aikya/docs/specs/development/SPEC-003/spec.md` |
| [database/spec.md](sdd/database/spec.md) | /aikya-specify | `aikya/docs/specs/development/SPEC-004/spec.md` |
| [README.md](sdd/README.md) | /aikya-init --methodology sdd | `aikya/docs/specs/README.md` |
| [constitution.md](sdd/constitution.md) | Explicit reviewed document | `aikya/docs/specs/constitution.md` |

### Las 120 plantillas opcionales de Milkeles

| Ejemplo | Uso | Ruta de salida en el proyecto |
|---|---|---|
| [ai-assisted-development/evaluation/eval-run-log.md](catalog/ai-assisted-development/evaluation/eval-run-log.md) | Explicit catalog write | `aikya/docs/documents/ai-assisted-development/evaluation/eval-run-log.md` |
| [ai-assisted-development/evaluation/evaluation-plan.md](catalog/ai-assisted-development/evaluation/evaluation-plan.md) | Explicit catalog write | `aikya/docs/documents/ai-assisted-development/evaluation/evaluation-plan.md` |
| [ai-assisted-development/foundations/agent-instructions-file.md](catalog/ai-assisted-development/foundations/agent-instructions-file.md) | Explicit catalog write | `aikya/docs/documents/ai-assisted-development/foundations/agent-instructions-file.md` |
| [ai-assisted-development/foundations/task-plan.md](catalog/ai-assisted-development/foundations/task-plan.md) | Explicit catalog write | `aikya/docs/documents/ai-assisted-development/foundations/task-plan.md` |
| [ai-assisted-development/specification/agent-task-specification.md](catalog/ai-assisted-development/specification/agent-task-specification.md) | Explicit catalog write | `aikya/docs/documents/ai-assisted-development/specification/agent-task-specification.md` |
| [data-engineering/foundations/data-contract.md](catalog/data-engineering/foundations/data-contract.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/foundations/data-contract.md` |
| [data-engineering/foundations/data-pipeline-design-document.md](catalog/data-engineering/foundations/data-pipeline-design-document.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/foundations/data-pipeline-design-document.md` |
| [data-engineering/foundations/dataset-catalog-entry.md](catalog/data-engineering/foundations/dataset-catalog-entry.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/foundations/dataset-catalog-entry.md` |
| [data-engineering/governance/data-classification-and-access-policy.md](catalog/data-engineering/governance/data-classification-and-access-policy.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/governance/data-classification-and-access-policy.md` |
| [data-engineering/governance/data-lineage-record.md](catalog/data-engineering/governance/data-lineage-record.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/governance/data-lineage-record.md` |
| [data-engineering/governance/data-quality-specification.md](catalog/data-engineering/governance/data-quality-specification.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/governance/data-quality-specification.md` |
| [data-engineering/operations/backfill-and-reprocessing-plan.md](catalog/data-engineering/operations/backfill-and-reprocessing-plan.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/operations/backfill-and-reprocessing-plan.md` |
| [data-engineering/operations/freshness-and-sla-log.md](catalog/data-engineering/operations/freshness-and-sla-log.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/operations/freshness-and-sla-log.md` |
| [data-engineering/operations/pipeline-runbook.md](catalog/data-engineering/operations/pipeline-runbook.md) | Explicit catalog write | `aikya/docs/documents/data-engineering/operations/pipeline-runbook.md` |
| [game-development/foundations/art-bible.md](catalog/game-development/foundations/art-bible.md) | Explicit catalog write | `aikya/docs/documents/game-development/foundations/art-bible.md` |
| [game-development/foundations/business-plan.md](catalog/game-development/foundations/business-plan.md) | Explicit catalog write | `aikya/docs/documents/game-development/foundations/business-plan.md` |
| [game-development/foundations/game-design-document.md](catalog/game-development/foundations/game-design-document.md) | Explicit catalog write | `aikya/docs/documents/game-development/foundations/game-design-document.md` |
| [game-development/live-operations/age-rating-compliance-record.md](catalog/game-development/live-operations/age-rating-compliance-record.md) | Explicit catalog write | `aikya/docs/documents/game-development/live-operations/age-rating-compliance-record.md` |
| [game-development/live-operations/balance-log.md](catalog/game-development/live-operations/balance-log.md) | Explicit catalog write | `aikya/docs/documents/game-development/live-operations/balance-log.md` |
| [game-development/live-operations/deployment-plan.md](catalog/game-development/live-operations/deployment-plan.md) | Explicit catalog write | `aikya/docs/documents/game-development/live-operations/deployment-plan.md` |
| [game-development/live-operations/live-ops-plan.md](catalog/game-development/live-operations/live-ops-plan.md) | Explicit catalog write | `aikya/docs/documents/game-development/live-operations/live-ops-plan.md` |
| [game-development/live-operations/privacy-ledger.md](catalog/game-development/live-operations/privacy-ledger.md) | Explicit catalog write | `aikya/docs/documents/game-development/live-operations/privacy-ledger.md` |
| [game-development/live-operations/release-notes.md](catalog/game-development/live-operations/release-notes.md) | Explicit catalog write | `aikya/docs/documents/game-development/live-operations/release-notes.md` |
| [game-development/production/asset-and-contribution-log.md](catalog/game-development/production/asset-and-contribution-log.md) | Explicit catalog write | `aikya/docs/documents/game-development/production/asset-and-contribution-log.md` |
| [game-development/production/cycle-retrospective.md](catalog/game-development/production/cycle-retrospective.md) | Explicit catalog write | `aikya/docs/documents/game-development/production/cycle-retrospective.md` |
| [general-swe/agile-scrum/definition-of-done.md](catalog/general-swe/agile-scrum/definition-of-done.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/definition-of-done.md` |
| [general-swe/agile-scrum/product-backlog-item.md](catalog/general-swe/agile-scrum/product-backlog-item.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/product-backlog-item.md` |
| [general-swe/agile-scrum/product-goal.md](catalog/general-swe/agile-scrum/product-goal.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/product-goal.md` |
| [general-swe/agile-scrum/sprint-backlog.md](catalog/general-swe/agile-scrum/sprint-backlog.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/sprint-backlog.md` |
| [general-swe/agile-scrum/sprint-retrospective.md](catalog/general-swe/agile-scrum/sprint-retrospective.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/sprint-retrospective.md` |
| [general-swe/agile-scrum/sprint-review-notes.md](catalog/general-swe/agile-scrum/sprint-review-notes.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/sprint-review-notes.md` |
| [general-swe/agile-scrum/team-working-agreement.md](catalog/general-swe/agile-scrum/team-working-agreement.md) | Explicit catalog write | `aikya/docs/documents/general-swe/agile-scrum/team-working-agreement.md` |
| [general-swe/foundations/architecture-decision-record.md](catalog/general-swe/foundations/architecture-decision-record.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/architecture-decision-record.md` |
| [general-swe/foundations/architecture-overview.md](catalog/general-swe/foundations/architecture-overview.md) | Explicit catalog write | `aikya/docs/architecture/architecture-overview.md` |
| [general-swe/foundations/branching-strategy.md](catalog/general-swe/foundations/branching-strategy.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/branching-strategy.md` |
| [general-swe/foundations/bug-report.md](catalog/general-swe/foundations/bug-report.md) | Explicit catalog write | `aikya/docs/bugs/bugs.md` |
| [general-swe/foundations/changelog.md](catalog/general-swe/foundations/changelog.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/changelog.md` |
| [general-swe/foundations/code-review-guidelines.md](catalog/general-swe/foundations/code-review-guidelines.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/code-review-guidelines.md` |
| [general-swe/foundations/coding-standards.md](catalog/general-swe/foundations/coding-standards.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/coding-standards.md` |
| [general-swe/foundations/configuration-management-plan.md](catalog/general-swe/foundations/configuration-management-plan.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/configuration-management-plan.md` |
| [general-swe/foundations/contributing-guide.md](catalog/general-swe/foundations/contributing-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/contributing-guide.md` |
| [general-swe/foundations/data-model.md](catalog/general-swe/foundations/data-model.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/data-model.md` |
| [general-swe/foundations/deployment-plan.md](catalog/general-swe/foundations/deployment-plan.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/deployment-plan.md` |
| [general-swe/foundations/deprecation-plan.md](catalog/general-swe/foundations/deprecation-plan.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/deprecation-plan.md` |
| [general-swe/foundations/feature-request.md](catalog/general-swe/foundations/feature-request.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/feature-request.md` |
| [general-swe/foundations/glossary.md](catalog/general-swe/foundations/glossary.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/glossary.md` |
| [general-swe/foundations/governance.md](catalog/general-swe/foundations/governance.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/governance.md` |
| [general-swe/foundations/incident-postmortem.md](catalog/general-swe/foundations/incident-postmortem.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/incident-postmortem.md` |
| [general-swe/foundations/interface-control-document.md](catalog/general-swe/foundations/interface-control-document.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/interface-control-document.md` |
| [general-swe/foundations/onboarding-guide.md](catalog/general-swe/foundations/onboarding-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/onboarding-guide.md` |
| [general-swe/foundations/pull-request-template.md](catalog/general-swe/foundations/pull-request-template.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/pull-request-template.md` |
| [general-swe/foundations/release-notes.md](catalog/general-swe/foundations/release-notes.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/release-notes.md` |
| [general-swe/foundations/rfc.md](catalog/general-swe/foundations/rfc.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/rfc.md` |
| [general-swe/foundations/runbook.md](catalog/general-swe/foundations/runbook.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/runbook.md` |
| [general-swe/foundations/security.md](catalog/general-swe/foundations/security.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/security.md` |
| [general-swe/foundations/service-readme.md](catalog/general-swe/foundations/service-readme.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/service-readme.md` |
| [general-swe/foundations/support.md](catalog/general-swe/foundations/support.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/support.md` |
| [general-swe/foundations/technical-design-document.md](catalog/general-swe/foundations/technical-design-document.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/technical-design-document.md` |
| [general-swe/foundations/test-case-specification.md](catalog/general-swe/foundations/test-case-specification.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/test-case-specification.md` |
| [general-swe/foundations/test-strategy.md](catalog/general-swe/foundations/test-strategy.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/test-strategy.md` |
| [general-swe/foundations/test-summary-report.md](catalog/general-swe/foundations/test-summary-report.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/test-summary-report.md` |
| [general-swe/foundations/threat-model.md](catalog/general-swe/foundations/threat-model.md) | Explicit catalog write | `aikya/docs/documents/general-swe/foundations/threat-model.md` |
| [general-swe/kanban/blocker-log.md](catalog/general-swe/kanban/blocker-log.md) | Explicit catalog write | `aikya/docs/documents/general-swe/kanban/blocker-log.md` |
| [general-swe/kanban/definition-of-workflow.md](catalog/general-swe/kanban/definition-of-workflow.md) | Explicit catalog write | `aikya/docs/documents/general-swe/kanban/definition-of-workflow.md` |
| [general-swe/kanban/flow-review.md](catalog/general-swe/kanban/flow-review.md) | Explicit catalog write | `aikya/docs/documents/general-swe/kanban/flow-review.md` |
| [general-swe/kanban/kanban-system-design.md](catalog/general-swe/kanban/kanban-system-design.md) | Explicit catalog write | `aikya/docs/documents/general-swe/kanban/kanban-system-design.md` |
| [general-swe/kanban/work-item-types.md](catalog/general-swe/kanban/work-item-types.md) | Explicit catalog write | `aikya/docs/documents/general-swe/kanban/work-item-types.md` |
| [general-swe/lean/a3.md](catalog/general-swe/lean/a3.md) | Explicit catalog write | `aikya/docs/documents/general-swe/lean/a3.md` |
| [general-swe/lean/experiment-record.md](catalog/general-swe/lean/experiment-record.md) | Explicit catalog write | `aikya/docs/documents/general-swe/lean/experiment-record.md` |
| [general-swe/lean/improvement-kata.md](catalog/general-swe/lean/improvement-kata.md) | Explicit catalog write | `aikya/docs/documents/general-swe/lean/improvement-kata.md` |
| [general-swe/lean/value-stream-map.md](catalog/general-swe/lean/value-stream-map.md) | Explicit catalog write | `aikya/docs/documents/general-swe/lean/value-stream-map.md` |
| [general-swe/project-management/project-brief.md](catalog/general-swe/project-management/project-brief.md) | Explicit catalog write | `aikya/docs/documents/general-swe/project-management/project-brief.md` |
| [general-swe/project-management/project-charter.md](catalog/general-swe/project-management/project-charter.md) | Explicit catalog write | `aikya/docs/documents/general-swe/project-management/project-charter.md` |
| [general-swe/project-management/risk-register.md](catalog/general-swe/project-management/risk-register.md) | Explicit catalog write | `aikya/docs/documents/general-swe/project-management/risk-register.md` |
| [general-swe/project-management/stakeholder-register.md](catalog/general-swe/project-management/stakeholder-register.md) | Explicit catalog write | `aikya/docs/documents/general-swe/project-management/stakeholder-register.md` |
| [general-swe/requirements/non-functional-requirements.md](catalog/general-swe/requirements/non-functional-requirements.md) | Explicit catalog write | `aikya/docs/documents/general-swe/requirements/non-functional-requirements.md` |
| [general-swe/requirements/product-requirements-document.md](catalog/general-swe/requirements/product-requirements-document.md) | Explicit catalog write | `aikya/docs/documents/general-swe/requirements/product-requirements-document.md` |
| [general-swe/requirements/use-case-specification.md](catalog/general-swe/requirements/use-case-specification.md) | Explicit catalog write | `aikya/docs/documents/general-swe/requirements/use-case-specification.md` |
| [general-swe/requirements/vision-and-scope.md](catalog/general-swe/requirements/vision-and-scope.md) | Explicit catalog write | `aikya/docs/documents/general-swe/requirements/vision-and-scope.md` |
| [general-swe/security-and-compliance/data-protection-impact-assessment.md](catalog/general-swe/security-and-compliance/data-protection-impact-assessment.md) | Explicit catalog write | `aikya/docs/documents/general-swe/security-and-compliance/data-protection-impact-assessment.md` |
| [general-swe/security-and-compliance/data-retention-policy.md](catalog/general-swe/security-and-compliance/data-retention-policy.md) | Explicit catalog write | `aikya/docs/documents/general-swe/security-and-compliance/data-retention-policy.md` |
| [general-swe/security-and-compliance/incident-response-plan.md](catalog/general-swe/security-and-compliance/incident-response-plan.md) | Explicit catalog write | `aikya/docs/documents/general-swe/security-and-compliance/incident-response-plan.md` |
| [general-swe/security-and-compliance/record-of-processing-activities.md](catalog/general-swe/security-and-compliance/record-of-processing-activities.md) | Explicit catalog write | `aikya/docs/documents/general-swe/security-and-compliance/record-of-processing-activities.md` |
| [general-swe/security-and-compliance/security-review-checklist.md](catalog/general-swe/security-and-compliance/security-review-checklist.md) | Explicit catalog write | `aikya/docs/documents/general-swe/security-and-compliance/security-review-checklist.md` |
| [general-swe/shape-up/cool-down-guide.md](catalog/general-swe/shape-up/cool-down-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/shape-up/cool-down-guide.md` |
| [general-swe/shape-up/kick-off-message.md](catalog/general-swe/shape-up/kick-off-message.md) | Explicit catalog write | `aikya/docs/documents/general-swe/shape-up/kick-off-message.md` |
| [general-swe/shape-up/pitch.md](catalog/general-swe/shape-up/pitch.md) | Explicit catalog write | `aikya/docs/documents/general-swe/shape-up/pitch.md` |
| [general-swe/shape-up/scope-map.md](catalog/general-swe/shape-up/scope-map.md) | Explicit catalog write | `aikya/docs/documents/general-swe/shape-up/scope-map.md` |
| [general-swe/user-documentation/documentation-style-guide.md](catalog/general-swe/user-documentation/documentation-style-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/documentation-style-guide.md` |
| [general-swe/user-documentation/explanation.md](catalog/general-swe/user-documentation/explanation.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/explanation.md` |
| [general-swe/user-documentation/how-to-guide.md](catalog/general-swe/user-documentation/how-to-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/how-to-guide.md` |
| [general-swe/user-documentation/installation-guide.md](catalog/general-swe/user-documentation/installation-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/installation-guide.md` |
| [general-swe/user-documentation/reference-page.md](catalog/general-swe/user-documentation/reference-page.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/reference-page.md` |
| [general-swe/user-documentation/troubleshooting-guide.md](catalog/general-swe/user-documentation/troubleshooting-guide.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/troubleshooting-guide.md` |
| [general-swe/user-documentation/tutorial.md](catalog/general-swe/user-documentation/tutorial.md) | Explicit catalog write | `aikya/docs/documents/general-swe/user-documentation/tutorial.md` |
| [general-swe/waterfall/change-request.md](catalog/general-swe/waterfall/change-request.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/change-request.md` |
| [general-swe/waterfall/master-test-plan.md](catalog/general-swe/waterfall/master-test-plan.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/master-test-plan.md` |
| [general-swe/waterfall/phase-gate-review.md](catalog/general-swe/waterfall/phase-gate-review.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/phase-gate-review.md` |
| [general-swe/waterfall/requirements-traceability-matrix.md](catalog/general-swe/waterfall/requirements-traceability-matrix.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/requirements-traceability-matrix.md` |
| [general-swe/waterfall/software-design-description.md](catalog/general-swe/waterfall/software-design-description.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/software-design-description.md` |
| [general-swe/waterfall/software-requirements-specification.md](catalog/general-swe/waterfall/software-requirements-specification.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/software-requirements-specification.md` |
| [general-swe/waterfall/user-acceptance-test-plan.md](catalog/general-swe/waterfall/user-acceptance-test-plan.md) | Explicit catalog write | `aikya/docs/documents/general-swe/waterfall/user-acceptance-test-plan.md` |
| [platform-engineering/foundations/platform-onboarding-guide.md](catalog/platform-engineering/foundations/platform-onboarding-guide.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/foundations/platform-onboarding-guide.md` |
| [platform-engineering/foundations/service-catalog-entry.md](catalog/platform-engineering/foundations/service-catalog-entry.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/foundations/service-catalog-entry.md` |
| [platform-engineering/reliability/error-budget-policy.md](catalog/platform-engineering/reliability/error-budget-policy.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/reliability/error-budget-policy.md` |
| [platform-engineering/reliability/slo-document.md](catalog/platform-engineering/reliability/slo-document.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/reliability/slo-document.md` |
| [platform-engineering/reliability/toil-log.md](catalog/platform-engineering/reliability/toil-log.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/reliability/toil-log.md` |
| [platform-engineering/resilience/capacity-plan.md](catalog/platform-engineering/resilience/capacity-plan.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/resilience/capacity-plan.md` |
| [platform-engineering/resilience/disaster-recovery-plan.md](catalog/platform-engineering/resilience/disaster-recovery-plan.md) | Explicit catalog write | `aikya/docs/documents/platform-engineering/resilience/disaster-recovery-plan.md` |
| [web-development/accessibility/accessibility-conformance-report.md](catalog/web-development/accessibility/accessibility-conformance-report.md) | Explicit catalog write | `aikya/docs/documents/web-development/accessibility/accessibility-conformance-report.md` |
| [web-development/accessibility/accessibility-statement.md](catalog/web-development/accessibility/accessibility-statement.md) | Explicit catalog write | `aikya/docs/documents/web-development/accessibility/accessibility-statement.md` |
| [web-development/accessibility/accessibility-test-plan.md](catalog/web-development/accessibility/accessibility-test-plan.md) | Explicit catalog write | `aikya/docs/documents/web-development/accessibility/accessibility-test-plan.md` |
| [web-development/foundations/api-design-guide.md](catalog/web-development/foundations/api-design-guide.md) | Explicit catalog write | `aikya/docs/documents/web-development/foundations/api-design-guide.md` |
| [web-development/foundations/brand-and-visual-guidelines.md](catalog/web-development/foundations/brand-and-visual-guidelines.md) | Explicit catalog write | `aikya/docs/documents/web-development/foundations/brand-and-visual-guidelines.md` |
| [web-development/foundations/browser-support-policy.md](catalog/web-development/foundations/browser-support-policy.md) | Explicit catalog write | `aikya/docs/documents/web-development/foundations/browser-support-policy.md` |
| [web-development/foundations/design-system-guide.md](catalog/web-development/foundations/design-system-guide.md) | Explicit catalog write | `aikya/docs/documents/web-development/foundations/design-system-guide.md` |
| [web-development/foundations/frontend-architecture.md](catalog/web-development/foundations/frontend-architecture.md) | Explicit catalog write | `aikya/docs/documents/web-development/foundations/frontend-architecture.md` |
| [web-development/foundations/rollout-plan.md](catalog/web-development/foundations/rollout-plan.md) | Explicit catalog write | `aikya/docs/documents/web-development/foundations/rollout-plan.md` |
| [web-development/performance/performance-budget.md](catalog/web-development/performance/performance-budget.md) | Explicit catalog write | `aikya/docs/documents/web-development/performance/performance-budget.md` |
| [web-development/performance/performance-review.md](catalog/web-development/performance/performance-review.md) | Explicit catalog write | `aikya/docs/documents/web-development/performance/performance-review.md` |

El catálogo muestra una sección informada por plantilla para demostrar que se omiten las demás cuando no hay datos. Los ejemplos estándar muestran composiciones más amplias. Consulta las entradas JSON de inputs/ para las composiciones estándar y manifest.json para cobertura y huellas.

GENERATED BY AIKYA HARNESS
