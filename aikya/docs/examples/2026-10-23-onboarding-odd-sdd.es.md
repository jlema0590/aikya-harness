# Ejemplos de onboarding: ODD y SDD por tipo de proyecto

Estos recorridos son ejemplos explicativos con actividades y métricas simuladas.
El núcleo ODD, la elección ODD/SDD y el protocolo de fases ya están implementados;
la matriz automatizada verifica 48 combinaciones de onboarding. No representan
mediciones de la cuenta ni despliegues reales. Los resultados de validación están
en [la evidencia histórica](../validation/archive/2026-10-22/ODD_EXECUTION.md).
Los nombres públicos de fase y estado están en inglés. Las explicaciones están en
español. Las actividades mostradas son textos de ejemplo, no evidencia del runtime.

## Entrada correcta

- **Proyecto nuevo:** /aikya-init, entrevista de tipo/stack, metodología y documentación.
- **Proyecto existente:** /aikya-analyze, descubrimiento y propuesta de adopción;
  no repite la entrevista técnica de un proyecto nuevo.
- Si se lanza /aikya-init sobre código existente: Explore detecta la situación y la
  ejecución de init queda Blocked con indicación de usar /aikya-analyze; no crea ni
  reemplaza código. No empieza analyze silenciosamente.
- En SDD ya configurado, una actualización conserva SDD. El valor predeterminado
  ODD no lo convierte automáticamente. Un perfil personalizado exige revisión.

En un proyecto nuevo basta lanzar /aikya-init y elegir odd o sdd durante la
entrevista. ODD es la recomendación y la elección inicial debe confirmarse.

Para un proyecto existente, primero se presenta una vista previa. Ejemplo SDD:

```text
/aikya-analyze --dry-run --methodology sdd --docs-lang en
```

Para elegir ODD explícitamente, el equivalente es:

```text
/aikya-analyze --dry-run --methodology odd --docs-lang en
```

La opción odd está admitida y se conserva en el perfil confirmado.
La vista previa termina sin instalar Aikya. Una adopción posterior autorizada usa
el mismo alcance, metodología e idioma y vuelve a comprobar las precondiciones.

## Qué significa cada estado

| Estado | Ejemplo de significado |
|---|---|
| Pending | La fase aplica, pero aún no ha comenzado. |
| Running | Hay una acción identificada en ejecución. |
| Waiting | Falta una respuesta, una aprobación o una dependencia pendiente. |
| Done | La acción/fase terminó con el resultado y evidencias declarados; no implica despliegue ni certificación. |
| Failed | Una operación o comprobación ejecutada falló. |
| Skipped | La receta omite la fase con motivo; por ejemplo, no se solicitó revisión independiente. |
| Blocked | Una precondición o control obligatorio impide continuar. |
| Interrupted | La ejecución fue interrumpida; requiere reconciliar su estado antes de reanudar. |

No se recorren los ocho estados obligatoriamente. Una fase habitual pasa de
Pending a Running y luego a Done. Waiting, Failed, Blocked e Interrupted aparecen
cuando ocurre la condición correspondiente. Skipped representa una omisión explícita.
Los estados no son fases adicionales y no expresan un porcentaje de avance.

## Secuencia común del onboarding

Ejemplo de proyecto nuevo con aprobación concedida y controles disponibles:

```text
Explore    Pending → Running → Waiting → Running → Done
Plan       Pending → Running → Waiting → Running → Done
Implement  Pending → Running → Done
Validate   Pending → Running → Done
Security   Pending → Running → Done
Review     Skipped
Run        Done
```

Explore/Waiting corresponde a respuestas de la entrevista; Plan/Waiting corresponde
a revisar y autorizar el plan concreto de archivos. Review/Skipped significa que
este ejemplo no invocó un revisor independiente. Si la receta o el usuario requiere
revisión: Review pasa Pending → Running → Done/Failed, con su actor y evidencia.
Aprobar el plan no se contabiliza como revisión independiente ya ejecutada.

En proyectos existentes, Explore normalmente descubre manifiestos, rutas e
indicadores del stack sin entrevista. Puede entrar en Waiting por una decisión
real que no se pueda resolver con la evidencia, como el idioma documental.

En una vista previa de analyze, Explore/Plan describen lo observado y propuesto;
Implement, los controles posteriores sobre archivos que no se han creado y Review
no ejecutada quedan Skipped con motivo. Plan termina con el preview preparado,
Run termina Done indicando writes=false; no queda una instalación ejecutándose.
Una nueva petición autorizada crea otra invocación y conserva el vínculo al preview.

Implement durante onboarding significa **instalar/configurar Aikya y sus documentos**.
No significa implementar funcionalidades, ejecutar generadores de aplicación,
instalar dependencias, aplicar infraestructura o publicar pipelines.
Validate comprueba lo pertinente al perfil/runtime/documentación; no presenta
pruebas de una aplicación inexistente como superadas. Security se limita al alcance
revisado y a los controles realmente disponibles.

## Matriz de los doce casos

| Caso | Situación | Tipo | Metodología | Entrada |
|---|---|---|---|---|
| 01 | Nuevo | Desarrollo | ODD | /aikya-init |
| 02 | Nuevo | Desarrollo | SDD | /aikya-init |
| 03 | Nuevo | Infraestructura | ODD | /aikya-init |
| 04 | Nuevo | Infraestructura | SDD | /aikya-init |
| 05 | Nuevo | DevOps | ODD | /aikya-init |
| 06 | Nuevo | DevOps | SDD | /aikya-init |
| 07 | Existente | Desarrollo | ODD | /aikya-analyze |
| 08 | Existente | Desarrollo | SDD | /aikya-analyze |
| 09 | Existente | Infraestructura | ODD | /aikya-analyze |
| 10 | Existente | Infraestructura | SDD | /aikya-analyze |
| 11 | Existente | DevOps | ODD | /aikya-analyze |
| 12 | Existente | DevOps | SDD | /aikya-analyze |

## 01. Proyecto nuevo · Desarrollo · ODD

API Java y frontend React, como decisiones simuladas.

Entrada: `/aikya-init`. Perfil: `mode=new`, `project_type=development`, `methodology=odd`.
La metodología odd y los estados compartidos son parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Waiting → Running → Done | Inspect empty workspace and collect application stack decisions |
| Plan | Pending → Running → Waiting → Running → Done | Preview application profile and Aikya file changes with ODD as the selected workflow |
| Implement | Pending → Running → Done | Write approved Aikya profile, runtime and documentation |
| Validate | Pending → Running → Done | Check Aikya profile, runtime integrity and documentation layout |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and secret-handling configuration |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No genera la API o el frontend durante init ni ejecuta pruebas de aplicación durante analyze.

Después del onboarding: /aikya-feature, /aikya-bugfix o la operación propia del tipo aplicará ODD. Un trabajo sustancial creará su expediente y tareas cuando exista una petición autorizada; init/analyze no inventan una feature para rellenarlo.

## 02. Proyecto nuevo · Desarrollo · SDD

API Java y frontend React, como decisiones simuladas.

Entrada: `/aikya-init`. Perfil: `mode=new`, `project_type=development`, `methodology=sdd`.
La metodología SDD existe; la presentación de fases/estados compartida es parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Waiting → Running → Done | Inspect empty workspace and collect application stack decisions |
| Plan | Pending → Running → Waiting → Running → Done | Preview application profile and Aikya file changes with explicit SDD selection |
| Implement | Pending → Running → Done | Write approved Aikya profile, runtime and documentation and SDD guide/runtime |
| Validate | Pending → Running → Done | Check Aikya profile, runtime integrity and documentation layout and SDD engine availability |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and secret-handling configuration |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No genera la API o el frontend durante init ni ejecuta pruebas de aplicación durante analyze.

Después del onboarding: /aikya-specify → /aikya-clarify cuando haya preguntas → /aikya-plan → /aikya-tasks → /aikya-implement. Se requieren aprobaciones independientes de especificación, plan y tareas antes de implementar. Init/analyze no crean SPEC-001 ni aprueban esas etapas.

## 03. Proyecto nuevo · Infraestructura · ODD

Repositorio de infraestructura Terraform con entornos declarados.

Entrada: `/aikya-init`. Perfil: `mode=new`, `project_type=infrastructure`, `methodology=odd`.
La metodología odd y los estados compartidos son parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Waiting → Running → Done | Inspect empty workspace and collect infrastructure ownership and environment decisions |
| Plan | Pending → Running → Waiting → Running → Done | Preview infrastructure-only profile and Aikya adoption files with ODD as the selected workflow |
| Implement | Pending → Running → Done | Write approved Aikya infrastructure profile and documentation |
| Validate | Pending → Running → Done | Check infrastructure profile consistency and Aikya documentation |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check proposed harness permissions and declared infrastructure-sensitive boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta terraform init/plan/apply/destroy ni Ansible y no contacta proveedores durante onboarding.

Después del onboarding: /aikya-feature, /aikya-bugfix o la operación propia del tipo aplicará ODD. Un trabajo sustancial creará su expediente y tareas cuando exista una petición autorizada; init/analyze no inventan una feature para rellenarlo.

## 04. Proyecto nuevo · Infraestructura · SDD

Repositorio de infraestructura Terraform con entornos declarados.

Entrada: `/aikya-init`. Perfil: `mode=new`, `project_type=infrastructure`, `methodology=sdd`.
La metodología SDD existe; la presentación de fases/estados compartida es parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Waiting → Running → Done | Inspect empty workspace and collect infrastructure ownership and environment decisions |
| Plan | Pending → Running → Waiting → Running → Done | Preview infrastructure-only profile and Aikya adoption files with explicit SDD selection |
| Implement | Pending → Running → Done | Write approved Aikya infrastructure profile and documentation and SDD guide/runtime |
| Validate | Pending → Running → Done | Check infrastructure profile consistency and Aikya documentation and SDD engine availability |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check proposed harness permissions and declared infrastructure-sensitive boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta terraform init/plan/apply/destroy ni Ansible y no contacta proveedores durante onboarding.

Después del onboarding: /aikya-specify → /aikya-clarify cuando haya preguntas → /aikya-plan → /aikya-tasks → /aikya-implement. Se requieren aprobaciones independientes de especificación, plan y tareas antes de implementar. Init/analyze no crean SPEC-001 ni aprueban esas etapas.

## 05. Proyecto nuevo · DevOps · ODD

Repositorio de automatización con contenedores y Kustomize declarados.

Entrada: `/aikya-init`. Perfil: `mode=new`, `project_type=devops`, `methodology=odd`.
La metodología odd y los estados compartidos son parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Waiting → Running → Done | Inspect empty workspace and collect delivery-tooling decisions |
| Plan | Pending → Running → Waiting → Running → Done | Preview DevOps-only profile and preservation of existing delivery files with ODD as the selected workflow |
| Implement | Pending → Running → Done | Write approved Aikya DevOps profile, runtime and living documentation |
| Validate | Pending → Running → Done | Check DevOps profile, Aikya runtime and documentation consistency |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and recorded delivery boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta builds de imágenes, pipelines, publicación de artefactos ni despliegues durante onboarding.

Después del onboarding: /aikya-feature, /aikya-bugfix o la operación propia del tipo aplicará ODD. Un trabajo sustancial creará su expediente y tareas cuando exista una petición autorizada; init/analyze no inventan una feature para rellenarlo.

## 06. Proyecto nuevo · DevOps · SDD

Repositorio de automatización con contenedores y Kustomize declarados.

Entrada: `/aikya-init`. Perfil: `mode=new`, `project_type=devops`, `methodology=sdd`.
La metodología SDD existe; la presentación de fases/estados compartida es parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Waiting → Running → Done | Inspect empty workspace and collect delivery-tooling decisions |
| Plan | Pending → Running → Waiting → Running → Done | Preview DevOps-only profile and preservation of existing delivery files with explicit SDD selection |
| Implement | Pending → Running → Done | Write approved Aikya DevOps profile, runtime and living documentation and SDD guide/runtime |
| Validate | Pending → Running → Done | Check DevOps profile, Aikya runtime and documentation consistency and SDD engine availability |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and recorded delivery boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta builds de imágenes, pipelines, publicación de artefactos ni despliegues durante onboarding.

Después del onboarding: /aikya-specify → /aikya-clarify cuando haya preguntas → /aikya-plan → /aikya-tasks → /aikya-implement. Se requieren aprobaciones independientes de especificación, plan y tareas antes de implementar. Init/analyze no crean SPEC-001 ni aprueban esas etapas.

## 07. Proyecto existente · Desarrollo · ODD

Repositorio Java/React con manifiestos existentes, solo como escenario.

Entrada: `/aikya-analyze`. Perfil: `mode=existing`, `project_type=development`, `methodology=odd`.
La metodología odd y los estados compartidos son parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Done; Waiting si falta una decisión real | Inspect existing manifests, modules and test-path indicators |
| Plan | Pending → Running → Waiting → Running → Done | Preview application profile and Aikya file changes with ODD as the selected workflow |
| Implement | Pending → Running → Done | Write approved Aikya profile, runtime and documentation |
| Validate | Pending → Running → Done | Check Aikya profile, runtime integrity and documentation layout |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and secret-handling configuration |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No genera la API o el frontend durante init ni ejecuta pruebas de aplicación durante analyze.

Se conservan la estructura implementada, las decisiones existentes compatibles, los archivos personalizados y el historial. Si hay conflicto de propiedad, perfil incompleto o runtime incompatible, se informa y se bloquea antes de adoptar; no se inventan valores.

Después del onboarding: /aikya-feature, /aikya-bugfix o la operación propia del tipo aplicará ODD. Un trabajo sustancial creará su expediente y tareas cuando exista una petición autorizada; init/analyze no inventan una feature para rellenarlo.

## 08. Proyecto existente · Desarrollo · SDD

Repositorio Java/React con manifiestos existentes, solo como escenario.

Entrada: `/aikya-analyze`. Perfil: `mode=existing`, `project_type=development`, `methodology=sdd`.
La metodología SDD existe; la presentación de fases/estados compartida es parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Done; Waiting si falta una decisión real | Inspect existing manifests, modules and test-path indicators |
| Plan | Pending → Running → Waiting → Running → Done | Preview application profile and Aikya file changes with explicit SDD selection |
| Implement | Pending → Running → Done | Write approved Aikya profile, runtime and documentation and SDD guide/runtime |
| Validate | Pending → Running → Done | Check Aikya profile, runtime integrity and documentation layout and SDD engine availability |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and secret-handling configuration |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No genera la API o el frontend durante init ni ejecuta pruebas de aplicación durante analyze.

Se conservan la estructura implementada, las decisiones existentes compatibles, los archivos personalizados y el historial. Si hay conflicto de propiedad, perfil incompleto o runtime incompatible, se informa y se bloquea antes de adoptar; no se inventan valores.

Después del onboarding: /aikya-specify → /aikya-clarify cuando haya preguntas → /aikya-plan → /aikya-tasks → /aikya-implement. Se requieren aprobaciones independientes de especificación, plan y tareas antes de implementar. Init/analyze no crean SPEC-001 ni aprueban esas etapas.

## 09. Proyecto existente · Infraestructura · ODD

Repositorio Terraform/Ansible ya existente, solo como escenario.

Entrada: `/aikya-analyze`. Perfil: `mode=existing`, `project_type=infrastructure`, `methodology=odd`.
La metodología odd y los estados compartidos son parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Done; Waiting si falta una decisión real | Inspect existing infrastructure manifests and repository boundaries |
| Plan | Pending → Running → Waiting → Running → Done | Preview infrastructure-only profile and Aikya adoption files with ODD as the selected workflow |
| Implement | Pending → Running → Done | Write approved Aikya infrastructure profile and documentation |
| Validate | Pending → Running → Done | Check infrastructure profile consistency and Aikya documentation |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check proposed harness permissions and declared infrastructure-sensitive boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta terraform init/plan/apply/destroy ni Ansible y no contacta proveedores durante onboarding.

Se conservan la estructura implementada, las decisiones existentes compatibles, los archivos personalizados y el historial. Si hay conflicto de propiedad, perfil incompleto o runtime incompatible, se informa y se bloquea antes de adoptar; no se inventan valores.

Después del onboarding: /aikya-feature, /aikya-bugfix o la operación propia del tipo aplicará ODD. Un trabajo sustancial creará su expediente y tareas cuando exista una petición autorizada; init/analyze no inventan una feature para rellenarlo.

## 10. Proyecto existente · Infraestructura · SDD

Repositorio Terraform/Ansible ya existente, solo como escenario.

Entrada: `/aikya-analyze`. Perfil: `mode=existing`, `project_type=infrastructure`, `methodology=sdd`.
La metodología SDD existe; la presentación de fases/estados compartida es parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Done; Waiting si falta una decisión real | Inspect existing infrastructure manifests and repository boundaries |
| Plan | Pending → Running → Waiting → Running → Done | Preview infrastructure-only profile and Aikya adoption files with explicit SDD selection |
| Implement | Pending → Running → Done | Write approved Aikya infrastructure profile and documentation and SDD guide/runtime |
| Validate | Pending → Running → Done | Check infrastructure profile consistency and Aikya documentation and SDD engine availability |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check proposed harness permissions and declared infrastructure-sensitive boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta terraform init/plan/apply/destroy ni Ansible y no contacta proveedores durante onboarding.

Se conservan la estructura implementada, las decisiones existentes compatibles, los archivos personalizados y el historial. Si hay conflicto de propiedad, perfil incompleto o runtime incompatible, se informa y se bloquea antes de adoptar; no se inventan valores.

Después del onboarding: /aikya-specify → /aikya-clarify cuando haya preguntas → /aikya-plan → /aikya-tasks → /aikya-implement. Se requieren aprobaciones independientes de especificación, plan y tareas antes de implementar. Init/analyze no crean SPEC-001 ni aprueban esas etapas.

## 11. Proyecto existente · DevOps · ODD

Repositorio con Dockerfile, workflows y manifests existentes, solo como escenario.

Entrada: `/aikya-analyze`. Perfil: `mode=existing`, `project_type=devops`, `methodology=odd`.
La metodología odd y los estados compartidos son parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Done; Waiting si falta una decisión real | Inspect existing pipeline and deployment configuration indicators |
| Plan | Pending → Running → Waiting → Running → Done | Preview DevOps-only profile and preservation of existing delivery files with ODD as the selected workflow |
| Implement | Pending → Running → Done | Write approved Aikya DevOps profile, runtime and living documentation |
| Validate | Pending → Running → Done | Check DevOps profile, Aikya runtime and documentation consistency |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and recorded delivery boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta builds de imágenes, pipelines, publicación de artefactos ni despliegues durante onboarding.

Se conservan la estructura implementada, las decisiones existentes compatibles, los archivos personalizados y el historial. Si hay conflicto de propiedad, perfil incompleto o runtime incompatible, se informa y se bloquea antes de adoptar; no se inventan valores.

Después del onboarding: /aikya-feature, /aikya-bugfix o la operación propia del tipo aplicará ODD. Un trabajo sustancial creará su expediente y tareas cuando exista una petición autorizada; init/analyze no inventan una feature para rellenarlo.

## 12. Proyecto existente · DevOps · SDD

Repositorio con Dockerfile, workflows y manifests existentes, solo como escenario.

Entrada: `/aikya-analyze`. Perfil: `mode=existing`, `project_type=devops`, `methodology=sdd`.
La metodología SDD existe; la presentación de fases/estados compartida es parte de la propuesta.

| Fase | Estados en este ejemplo autorizado | Activity de ejemplo |
|---|---|---|
| Explore | Pending → Running → Done; Waiting si falta una decisión real | Inspect existing pipeline and deployment configuration indicators |
| Plan | Pending → Running → Waiting → Running → Done | Preview DevOps-only profile and preservation of existing delivery files with explicit SDD selection |
| Implement | Pending → Running → Done | Write approved Aikya DevOps profile, runtime and living documentation and SDD guide/runtime |
| Validate | Pending → Running → Done | Check DevOps profile, Aikya runtime and documentation consistency and SDD engine availability |
| Security | Pending → Running → Done, si se completan los controles exigidos | Check generated harness permissions and recorded delivery boundaries |
| Review | Skipped con motivo, o Pending → Running → Done/Failed si se exige | Review the current Aikya onboarding changes and recorded findings |

Resultado del ejemplo satisfactorio: `Run · Done`, con resumen de qué se configuró y qué no se verificó. No ejecuta builds de imágenes, pipelines, publicación de artefactos ni despliegues durante onboarding.

Se conservan la estructura implementada, las decisiones existentes compatibles, los archivos personalizados y el historial. Si hay conflicto de propiedad, perfil incompleto o runtime incompatible, se informa y se bloquea antes de adoptar; no se inventan valores.

Después del onboarding: /aikya-specify → /aikya-clarify cuando haya preguntas → /aikya-plan → /aikya-tasks → /aikya-implement. Se requieren aprobaciones independientes de especificación, plan y tareas antes de implementar. Init/analyze no crean SPEC-001 ni aprueban esas etapas.

## Documentos: qué cambia con tipo y metodología

| Elemento | Regla real / prevista |
|---|---|
| overview.md, architecture/architecture-overview.md, indice.md | Documentación contextual de onboarding y navegación de archivos reales. |
| tools/agents.md, tools/token-policy.md, skills.md | Contexto e inventarios de Aikya; no prueban que los agentes o skills se hayan ejecutado. |
| plan/testing.md | Estrategia declarada para nuevo proyecto u observaciones disponibles para existente; no acredita pruebas ejecutadas. |
| Operaciones, seguridad e infraestructura | Solo con decisiones/indicadores que respalden su creación; init puede incluir propuestas locales según el perfil. |
| tools/skill-comparison.md | Solo al registrar una instalación externa solicitada; no se crea por seleccionar ODD/SDD. |
| bugs/bugs.md y features/<slug>/spec.md | Solo al existir un bug o trabajo concreto con contenido revisado. |
| specs/README.md | Guía añadida al seleccionar SDD. |
| specs/<project_type>/SPEC-NNN/ | Se crea con /aikya-specify y avanza con los comandos SDD; no aparece por completar init/analyze. |
| changes/REQ-*.md | Registro de cambios realmente realizados cuando corresponda; no un historial ficticio de acciones. |

Los documentos Markdown generados terminan con GENERATED BY AIKYA HARNESS.
Las instrucciones raíz CLAUDE.md, el perfil JSON y el informe técnico de analyze
mantienen sus rutas propias; el pie se aplica al Markdown, no a los archivos JSON.

Hay ejemplos **ya generados por el código actual** en la
[galería documental](../../../examples/documentation/generated/README.es.md).
No deben confundirse con estas simulaciones de la futura interfaz ODD/fases.

## Diferencia entre onboarding y ciclo SDD

Los siguientes son estados actuales del motor SDD, separados de las fases públicas
propuestas de la barra:

| Acción posterior al onboarding | Estado actual que informa el motor |
|---|---|
| /aikya-specify con requisitos revisados | SPEC_DRAFT |
| /aikya-clarify, si hay preguntas | Conserva SPEC_DRAFT mientras no se apruebe la especificación |
| Aprobación explícita de especificación | SPEC_APPROVED |
| /aikya-plan | PLAN_DRAFT |
| Aprobación explícita del plan | PLAN_APPROVED |
| /aikya-tasks | TASKS_DRAFT |
| Aprobación explícita de tareas | IMPLEMENTING |
| /aikya-implement | IMPLEMENTING; las tareas registran su progreso y evidencias |
| Registro de todas las evidencias requeridas declaradas passed | EVIDENCE_RECORDED |
| Registro de evidencia declarada failed | FAILED |

La aprobación de tareas hace que el motor informe IMPLEMENTING; por sí sola no
prueba que ya haya código implementado. EVIDENCE_RECORDED tampoco es un certificado:
el motor conserva independently_executed=false. /aikya-sdd-status consulta el
estado sin generar otro informe. Los estados de permisos/espera de la futura barra
no inventan aprobaciones adicionales dentro de este motor.

En la interfaz propuesta, especificar/diseñar/descomponer tareas corresponde a
Plan, con Waiting en cada decisión de aprobación necesaria. Validate y Security
registran las comprobaciones reales, y Review es una revisión real del candidato,
no una aprobación automática por haber ejecutado los comandos anteriores.

## Casos alternativos: estados que no son el camino satisfactorio

| Situación | Representación propuesta y siguiente paso |
|---|---|
| /aikya-init detecta código existente | Explore detecta la precondición; Run Blocked, resto sin ejecutar; indicar /aikya-analyze. |
| analyze no encuentra proyecto ni evidencia | El resultado actual es EMPTY; la barra explica Blocked/entrada inadecuada e indica /aikya-init. |
| analyze obtiene información insuficiente | Resultado actual PARTIAL; Explore/Plan Blocked hasta resolver evidencia o alcance; sin adopción. |
| Hay perfil/runtime/archivo personalizado incompatible | Resultado actual NEEDS_REVIEW; Run Blocked con motivo. No confundirlo con Review ya ejecutada. |
| Falta elegir idioma o contestar una decisión | Fase actual Waiting; después continúa Running al recibir la respuesta. |
| Falta autorización para archivos propuestos | Plan Waiting; Implement continúa Pending. |
| Falla una comprobación ejecutada | Validate Failed; se registra evidencia y puede volver a Plan/Implement con alcance autorizado. |
| Falta un control de seguridad exigido | Security Blocked; cobertura no verificada identificada, sin éxito ficticio. |
| Hay un hallazgo de seguridad sin resolver | Security Failed/Blocked según el control; resolver el hallazgo o una decisión de riesgo explícita antes del cierre exigido. |
| Se solicita revisión y encuentra un defecto | Review Failed; volver a Explore/Plan/Implement y repetir controles afectados. |
| Usuario interrumpe o proceso termina interrumpido | Run Interrupted; fases pendientes no se completan. Reconciliar archivos, estado y evidencias antes de reanudar. |
| Se intenta cambiar silenciosamente un SDD existente a ODD | Blocked; conservar SDD y exigir una migración revisada. |

PARTIAL, EMPTY, READY y NEEDS_REVIEW pertenecen al resultado actual del analizador;
no son nuevas fases. El campo approval_required del preview distingue un resultado
READY preparado de una adopción efectivamente ejecutada con writes=true.

## Modelo y tokens durante cualquier caso

Ejemplo ficticio de la futura barra, no datos de esta cuenta:

```text
AIKYA · /aikya-init · ODD · Implement · Running · Sonnet [observed]
Activity: Writing approved Aikya configuration
Context: 28% · Session: 91k recorded tokens · Account 5h: 34% · Account 7d: 62%
```

- El modelo se muestra por actor y acción cuando haya observación; N/D si falta.
- Una comprobación Python local muestra Local · Python, sin asignarle un modelo LLM.
- El contexto no es consumo acumulado. Las cuotas de cuenta no pertenecen solo a
  esta invocación ni al proyecto; no se suman sus porcentajes entre fases.
- Review puede usar otro actor/modelo si realmente se invoca; no se presupone Opus,
  Sonnet o Haiku por el nombre de la fase.
- Esperar aprobación no consume automáticamente llamadas de un modelo para animar
  la barra. Los campos ausentes o vencidos se señalan como tales.

Referencia del diseño: [especificación](../design/harness/2026-10-23-odd-observabilidad.es.md)
y [plan conjunto](../plan/archive/harness-development/2026-10-23-odd-observabilidad.es.md).

GENERATED BY AIKYA HARNESS
