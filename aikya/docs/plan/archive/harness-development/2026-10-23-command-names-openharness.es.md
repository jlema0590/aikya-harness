# Plan: nombres de comandos, OpenHarness y agent loop

Los apartados 1–4 corresponden al cambio implementado y verificado. El apartado 5 se implementa de forma opcional y se valida localmente. La prueba real con Claude se realizará en el otro entorno elegido por el usuario; no se afirma haberla superado aquí.

## Objetivo y alcance

Renombrar los cuatro comandos solicitados y consolidar las instalaciones externas en /aikya-install-skill. Comparar el código real de OpenHarness con Aikya en memoria, observación y persistencia. No integrar OpenHarness ni ejecutar su código.

| Antes | Nombre definitivo |
|---|---|
| /aikya-project-init | /aikya-project |
| /aikya-infra-project | /aikya-infra |
| /aikya-architecture-review | /aikya-arc-review |
| /aikya-documentation-sync | /aikya-docs-sync |
| /aikya-skills-install y /aikya-install-skill | /aikya-install-skill |

El registro público tendrá 27 comandos, sin aliases activos para los cinco nombres retirados. Las instalaciones existentes migrarán únicamente copias verificadas; las personalizaciones se conservarán con aviso de revisión. Se mantiene 6.1.1, el flujo ODD/SDD, los permisos y el pie Markdown. No hacer push.

## 1. Contratos y migración

Archivos: aikya_setup.py, install.py, aikya_analyze.py, command_workflows.py, documentation_workflows.py, docs_migration_hashes.py y tests/test_command_renames.py.

- [x] Probar registro nuevo, recetas de fases y arquitectura de solo lectura; los nombres retirados dejan de ser comandos públicos.
- [x] Probar actualización global/project desde cinco skills verificadas, respaldo previo a retirada y reinstalación idempotente.
- [x] Probar preservación de comandos personalizados y rechazo de rutas o respaldos inseguros antes de retirar archivos.
- [x] Actualizar consumidores, vistas previas y hashes del predecesor c3daaf3 sin reescribir registros históricos ni documentos del usuario.

## 2. Skills y documentación

Archivos: aikya-skills/, template/, README.md, README.es.md, skills_registry.py, documentación vigente y pruebas afectadas.

- [x] Mover cuatro skills al nombre definitivo y corregir sus nombres en frontmatter.
- [x] Convertir /aikya-install-skill en el flujo completo de revisión, autorización, instalación y comparación; eliminar el wrapper duplicado.
- [x] Actualizar referencias activas y ejemplos vigentes. Mantener los nombres antiguos únicamente en migraciones, fixtures o evidencias históricas identificadas.

## 3. Comparación de OpenHarness

Entrega: docs/research/OPENHARNESS_COMPARISON.es.md, con revisión fijada a un commit.

- [x] Leer README y código de memoria, contexto, sesiones, eventos, herramientas y almacenamiento sin ejecutar el proyecto externo.
- [x] Separar memoria persistente, compactación de contexto, observación y auditoría; contrastar con el código actual de Aikya.
- [x] Identificar límites y propuestas de adopción con costes y riesgos cualitativos, sin atribuir capacidades no verificadas ni modificar Aikya fuera del cambio de nombres.

## 4. Validación y entrega

- [x] Ejecutar la suite y contratos de assets, catálogo, contexto y versión; comprobar los 27 comandos.
- [x] Revisar independientemente migraciones y conclusiones técnicas; corregir hallazgos reproducibles.
- [x] Guardar commit local y entregar comparación en español con fuentes enlazadas.

## 5. Agent loop dentro de Aikya — implementación opcional

### Viabilidad y decisión recomendada

**Sí es viable, con desarrollo adicional.** Aikya ya dispone de recetas de fases,
expedientes ODD/SDD, comprobación de dependencias, evidencias, revisiones y rechazo
de resultados obsoletos. Esos componentes permiten gobernar un loop, pero todavía
no constituyen un ejecutor autónomo que llame al modelo y use herramientas.

| Alternativa | Alcance | Esfuerzo relativo y decisión |
|---|---|---|
| Loop de tareas Aikya sobre Claude Code | Aikya selecciona trabajo permitido, delega su ejecución al runtime, valida resultados y decide continuar, corregir o detenerse. | Medio/alto. Opción recomendada, empezando por ejecución secuencial y acotada. |
| Runtime propio como OpenHarness | Aikya gestiona directamente llamadas al modelo, herramientas, conversación, compactación y proveedores. | Alto. Viable como proyecto separado, con nuevas dependencias y mantenimiento; fuera de esta primera etapa. |

La vía de integración a evaluar es el Claude Agent SDK, que expone el loop de
Claude Code en Python y TypeScript. Su disponibilidad documentada no demuestra
que Aikya esté integrado: se necesita una prueba de compatibilidad de versiones,
permisos, configuración, sesiones y carga de skills antes de adoptarlo.
[SDK oficial](https://code.claude.com/docs/en/agent-sdk/overview) ·
[funcionamiento del loop](https://code.claude.com/docs/en/agent-sdk/agent-loop).

### Arquitectura y secuencia prevista

Un controlador Aikya rodearía al loop del runtime. El controlador decide qué tarea
puede ejecutarse y cuándo aceptar su resultado; el runtime realiza las llamadas
al modelo y las herramientas dentro de los permisos recibidos. Mostrar fases o
repetir comandos de estado por sí solo no implementa ese comportamiento.

```text
Petición y alcance autorizado
  -> Explore -> Plan -> comprobación de permisos y gates ODD/SDD
  -> Implement mediante el adaptador de runtime
  -> Validate -> Security -> Review
  -> aceptar evidencia y continuar con la siguiente tarea
     o volver a Implement dentro del límite
     o detenerse con motivo y checkpoint
```

Las fases permanecen en inglés. Su aplicabilidad sigue la receta del comando;
una consulta de solo lectura no habilita Implement. Un fallo de validación o
revisión solo autoriza otra iteración dentro del alcance ya permitido.

### Trabajo pendiente y pruebas de aceptación

- [x] **AL-1 — Contrato y prueba de compatibilidad.** Evaluar el SDK como dependencia
  opcional sin añadirlo a la instalación básica. Proponer agent_runtime.py como
  adaptador, con ejecución y cancelación, eventos normalizados y una referencia
  de sesión. Probar carga explícita de configuración/skills Aikya, denegación de
  herramientas, respuesta estructurada y ausencia del SDK. No iniciar un proceso
  recursivo desde un hook ni abrir otra sesión por cada evento de observación.
- [x] **AL-2 — Controlador secuencial.** Crear agent_loop.py sobre command_workflows.py,
  odd_engine.py, sdd_engine.py y execution_state.py. Propuesta inicial: una tarea
  activa y un máximo de tres iteraciones por tarea, incluida la primera; detener
  tras dos intentos consecutivos sin evidencia de avance. Exigir max_turns y un
  tiempo máximo por ejecución en la configuración revisada. Probar éxito real,
  corrección de un fallo, agotamiento de límites, error del runtime y cancelación.
  El máximo del SDK y el límite de Aikya se aplican juntos.
- [x] **AL-3 — Gates y permisos.** Empezar con /aikya-feature, /aikya-bugfix y
  /aikya-implement mediante una opción explícita por diseñar, sin añadir otro
  comando público. En SDD, comprobar la especificación, el plan, las tareas
  aprobadas y sus dependencias antes de cada ejecución. En ODD, respetar alcance,
  dependencias y criterios de aceptación. Probar que el loop no se autoaprueba,
  no utiliza permisos amplios para saltar reglas y se detiene en waiting cuando
  hace falta una decisión o autorización. Instalaciones externas y despliegues
  conservan sus autorizaciones específicas.
- [x] **AL-4 — Persistencia y recuperación.** Crear agent_loop_state.py y una
  propuesta de expediente aikya/docs/loops/<run-id>/ con state.json y summary.md.
  Guardar identidad de proyecto/worktree, tarea, iteración, versión de esquema,
  revisión, candidate_generation, referencias de evidencia y motivo de parada.
  Registrar intención antes de un efecto y resultado después; si hay un corte
  entre ambos, marcar el efecto como incierto y reconciliar antes de reintentar.
  Probar escrituras atómicas, bloqueo, efectos duplicados, cambio de archivos y
  recuperación en un checkout distinto. La recuperación no depende de la caché
  de presentación ni implica poder repetir cualquier efecto exactamente una vez.
- [x] **AL-5 — Memoria y observación.** Añadir como extensión los recuerdos tipados y
  recuperación selectiva propuestos en la comparación; mientras no existan, usar
  únicamente expedientes y archivos actuales como contexto. No hacer de esa
  memoria un requisito para el primer prototipo ni una fuente de aprobaciones.
  Publicar fases, actor, modelo observado y consumo disponible por ejecución.
  Probar aislamiento entre proyectos, recuerdos obsoletos, modelos desconocidos y
  eventos tardíos. Mantener prompts, secretos y salidas crudas fuera de esta caché.
- [x] **AL-6 — Presupuestos y cierre verificable.** Registrar consumos por ID y
  ámbito para no sumar dos veces mensajes ni totales acumulados de una sesión
  reanudada. Mantener el presupuesto del loop entre reintentos y reanudaciones.
  Presentar costes del SDK como estimaciones, no facturación ni cuota semanal.
  Si se exige un límite basado en una métrica no disponible, bloquear el arranque
  en vez de asumir cero. Probar que la respuesta final del modelo no cierra una
  tarea sin evidencias actuales de Validate, Security y Review cuando sean
  requeridas; un cambio de candidato invalida comprobaciones anteriores.

Cada bloque se implementará con pruebas de regresión previas en
tests/test_agent_loop.py, tests/test_agent_loop_runtime.py y
tests/test_agent_loop_recovery.py, según corresponda. La prueba inicial del SDK
necesitará un entorno de ensayo y una invocación expresamente habilitada; las
pruebas locales de política usarán un adaptador de prueba sin consumir modelos.

[Permisos del SDK](https://code.claude.com/docs/en/agent-sdk/permissions) ·
[consumo y estimaciones](https://code.claude.com/docs/en/agent-sdk/cost-tracking).

### Dependencias, entrega y límites

Orden previsto: AL-1, AL-2/AL-3, AL-4, AL-5/AL-6, y después validación integrada.
La memoria duradera puede añadirse tras el prototipo; la persistencia del loop,
los permisos y los límites son necesarios antes de una ejecución real de cambios.
Revisar en conjunto ODD/SDD, en/es, instalación global/project y los tres tipos de
proyecto. El cierre requiere suite completa, contratos de assets/instalación y una
prueba real controlada del adaptador; los fixtures no prueban ejecución con un LLM.

Esta etapa sería opt-in. /aikya-init y /aikya-analyze seguirían solicitando las
opciones del proyecto; no arrancarían automáticamente un loop. Tampoco se añade
paralelismo, ejecución en segundo plano, otro compactador ni un proveedor nuevo.
El esfuerzo es cualitativo: la estimación de tiempo y gasto requiere completar
AL-1 y acordar modelos, presupuesto y entorno. Los seis bloques tienen implementación
y pruebas locales; el smoke real del SDK permanece pendiente en el entorno del usuario.
La guía vigente está en docs/AGENT_LOOP.md y la evidencia en docs/validation/AGENT_LOOP.md.

GENERATED BY AIKYA HARNESS
