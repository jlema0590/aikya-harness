# Gentle Shell y Aikya: funcionalidades y oportunidades de integración

Análisis estático del 23 de octubre de 2026. Repositorio externo:
[Gentle Shell, revisión 05065e7a0437d13eb158191681ce672319b9a8e0](https://github.com/Gentleman-Programming/gentle-shell/tree/05065e7a0437d13eb158191681ce672319b9a8e0).
El package.json de esa revisión declara gentle-pi 4.3.0; el README todavía presenta
una sección de novedades 4.1. La comparación usa el código de la revisión fijada,
sin tomar esa sección como inventario exhaustivo de la versión.

No se ejecutó Gentle Shell, su postinstall, sus pruebas ni sus dependencias.
Las funcionalidades se identifican por registros de herramientas/comandos,
implementaciones y contratos; esto no constituye una auditoría de seguridad ni
una medición de rendimiento. Aikya se compara con la implementación local del
agent loop posterior a 0d99950. Su prueba real con Claude se hará en otro entorno.

## Diferencia de arquitectura

Gentle Shell es un entorno de trabajo para Pi: extensiones TypeScript, interfaz de
terminal, procesos de agentes y adaptadores hacia componentes como Gentle AI y
Engram. Aikya organiza metodología, documentación, instalación y evidencias sobre
Claude Code, con un nuevo adaptador opcional del Agent SDK. Las extensiones de Pi
no pueden copiarse directamente a Aikya como si fueran skills de Claude Code.

Fuentes: [paquete y dependencias](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/package.json),
[extensión principal](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/gentle-ai.ts).
En Aikya: aikya_setup.py, install.py, agent_runtime.py y agent_loop.py.

## Funcionalidades verificadas y comparación

| Funcionalidad | Gentle Shell | Aikya local | Evaluación |
|---|---|---|---|
| ODD proporcional | Trabajo pequeño inline; seguimiento recuperable para trabajo sustancial, con documento y espejo en memoria cuando está disponible. | Clasificación ODD, worklist con dependencias y evidencia, y vía inline sin dossier para cambios pequeños. | Ya hay una base equivalente; evitar duplicar expedientes. |
| SDD | Hay vocabulario, contratos de vinculación a recibos y compatibilidad con assets SDD; esas referencias no prueban un motor independiente completo dentro de Shell. | Motor propio con especificación, aclaraciones, plan, tareas y aprobaciones separadas. | Mantener sdd_engine.py como autoridad de estado de Aikya. |
| Ejecución de agentes | Procesos separados, ejecución focalizada, delegación, control de parada, mensajería y trabajo en segundo plano. | Catálogo de especialistas; el nuevo loop ejecuta una tarea autorizada por vez sobre Claude, sin habilitar delegación/paralelismo del hijo. | Es una diferencia real de alcance. Añadir concurrencia exigiría aislamiento y permisos nuevos. |
| Modelos y perfiles | Perfiles con modelo/esfuerzo por rol y orquestador, con selección ligada a la sesión. | Política de modelos y observación del modelo real; el loop usa el runtime configurado, sin un selector de perfiles equivalente. | Interesa la distinción entre modelo configurado, heredado y observado. |
| Memoria | Integración con gentle-engram/Engram y comprobaciones de procedencia/compatibilidad del almacén. ODD documenta un espejo de recuperación. | Memorias Markdown de proyecto, tipos, TTL, huella de fuente y recuperación léxica acotada; no servidor Engram ni espejo remoto. | Adoptar contratos de proveedor solo si se necesita una memoria externa. |
| Permisos | El código reconoce normal, auto, yolo y super-yolo. Auto incorpora un clasificador con contexto humano y consumo propio. | Consentimiento explícito por alcance; SDK en modo default y filtros de herramientas/rutas. | No trasladar automáticamente la semántica de Auto/YOLO a Aikya. |
| Revisión según riesgo | Evaluación passive/medium/high, motivos y plan de verificación; coordinación con revisión nativa y capacidades del proveedor. | Validate/Security/Review y huellas del candidato; el loop inicial requiere revisión independiente de solo lectura para su tarea. | Primera oportunidad: proporcionalidad sin debilitar los gates SDD ni la evidencia. |
| Recibos y publicación | Contratos de candidato congelado, resultados tipados y gates para objetivos de commit, push, PR y release. Parte de la autoridad pertenece a Gentle AI nativo. | Evidencia JSON del candidato/tarea y registros ODD/SDD. No existe ese contrato completo de publicación nativa. | Diseñar recibos propios antes de considerar gates de entrega; ningún recibo concede permiso para publicar. |
| Jobs y monitores | bash_background comunica la terminación; monitor convierte líneas de salida en eventos. Hay registro acotado y cancelación de procesos. | Procesos locales acotados para checks y worker SDK, en primer plano; sin registro general de jobs ni monitores. | Útil después del loop estable, especialmente para builds/CI largos. |
| Vista de cambios | Interfaz de diferencias sobre Git y worktrees; captura cambios de sesión desde eventos verificados de write/edit. | Git, documentación e índice de artefactos, más barra de fases; sin visor TUI propio equivalente. | Un informe de estado/exportación aporta valor antes de construir una terminal completa. |
| Vista de agentes y tareas | Paneles de agentes, historial recuperado, estados y Todo como proyección de trabajo. | Fases/actores, snapshots y documentos de tareas. | Unificar una vista de lectura; no crear otra fuente de verdad. |
| Historial de prompts | Captura opt-in, ámbito proyecto/global, búsqueda y eliminación; apagar captura no borra los archivos anteriores. | La conversación pertenece a Claude Code. Los checkpoints/cachés Aikya excluyen prompts y salidas crudas. | Conservar este contrato de datos salvo petición explícita de historial. |
| Métricas | Contabilidad por ejecutor/modelo, uso disponible/desconocido y una política para el transporte de telemetría. | Métricas de fase/actor y consumo disponible; el loop distingue acumulados por sesión y estimación de coste. | Interesa homogeneizar ámbitos y disponibilidad, no inferir facturas/cuotas de tokens. |
| Skills y grafo de código | Registro/refresco de skills y una herramienta codegraph integrada mediante adaptador. | Inventario de skills y evaluación/instalación externa explícita; no una herramienta codegraph equivalente incorporada al loop. | Integrar adaptadores concretos solo con procedencia, permisos y pruebas de disponibilidad. |
| Voz, notificaciones y personalización | Extensiones y paneles de voz, avisos, atajos, temas y opciones de interfaz. | No hay una interfaz de terminal propia con esas funciones. | Prioridad baja para el objetivo actual de Aikya. |
| Instalación y mantenimiento | Lanzador y modo bundled, actualización/desinstalación, recursos y componentes verificados. | Registro global/project, instalación conservadora, migraciones y SDK opcional separado. | Mejorar diagnósticos/migraciones sin introducir instalaciones externas implícitas. |

### Fuentes por área

- ODD y recuperación: [referencia operativa](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/docs/readme-reference.md),
  [assets de agentes](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/agent-assets.ts).
- Agentes/coordinación: [extensión de agentes](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/gentle-agents.ts),
  [consultas de sesiones](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/orchestrator-consultation.ts),
  [perfiles](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/agent-profiles.ts).
- Memoria: [control de arranque bundled](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/runtime/gentle-shell-bundled.mjs),
  [vinculación de operaciones de memoria](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/auto-permission-memory.ts).
- Permisos: [modos](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/permission-mode-policy.ts),
  [política de sesión](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/yolo-session-policy.ts),
  [clasificador Auto](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/auto-permission-classifier.ts).
- Revisión y publicación: [evaluación de riesgo](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/review-risk-assessment.ts),
  [gates de publicación](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/review-publication-gate.ts),
  [contrato del ledger](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/skills/_shared/review-ledger-contract.md).
- Procesos y cambios: [jobs/monitor](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/background-jobs.ts),
  [captura de cambios](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/session-change-capture.ts),
  [interfaz del shell](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/gentle-shell.ts).
- Historial y métricas: [historial opt-in](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/history/index.ts),
  [contabilidad](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/runtime-metrics.ts),
  [política de métricas](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/lib/runtime-metrics-policy.ts).
- Skills/grafo/voz: [registro](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/skill-registry.ts),
  [codegraph](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/codegraph-tools.ts),
  [voz](https://github.com/Gentleman-Programming/gentle-shell/blob/05065e7a0437d13eb158191681ce672319b9a8e0/extensions/gentle-voice.ts).

## Límites que cambian la decisión

**La memoria de Engram es una dependencia, no un servicio reimplementado por Shell.**
El código inspeccionado comprueba identidad/procedencia y compatibilidad antes de
reutilizar ciertos almacenes/servidores. Incluso contempla desactivar memoria si
no puede acreditar seguridad de reutilización. No atribuyo sincronización remota,
embeddings, migración universal ni garantías del motor de Engram a esta revisión.
El espejo ODD y el documento local no se escriben en una transacción conjunta.

**Los cuatro modos de permisos tienen semánticas distintas.** El código de YOLO
mantiene confirmaciones destructivas; Super YOLO amplía el permiso de la sesión
principal incluso para esas operaciones, con restricciones específicas. Por eso
no basta con leer la frase general del README sobre guardas destructivas. Mi
recomendación para Aikya es conservar scope y gates explícitos, sin añadir ahora
un clasificador de permisos ni un modo de elusión.

**Los recibos no equivalen a entregar cambios.** La autoridad del proveedor nativo,
la revisión del candidato y el permiso para commit/push/PR/release son decisiones
separadas. Copiar un esquema JSON no implementaría las garantías de ese proveedor.
En Aikya las huellas actuales detectan cambios y resultados obsoletos, pero no son
recibos firmados ni transacciones completas sobre el repositorio.

**No hay base para prometer ahorro económico frente a Aikya.** El README presenta
benchmarks de escenarios propios. No se han repetido con las mismas tareas,
modelos, proveedores, permisos y pruebas en Aikya. La orquestación, revisión y Auto
pueden añadir llamadas a modelos; una política más proporcional puede reducirlas,
pero ese efecto exige medición controlada.

## Recomendación

Priorizar evaluación de riesgo explicable, recibos del candidato y una vista de
estado común. Después, perfiles ligados a la sesión y jobs acotados si existen
casos reales. Mantener memoria Markdown y el loop secuencial como base mientras
se valida su funcionamiento real. Posponer una TUI completa, historial de prompts,
voz, modos YOLO y paralelismo de escritura.

El [plan de adopción](../../aikya/docs/plan/archive/harness-development/2026-10-23-gentle-shell-adoption.es.md)
convierte esas oportunidades en entregas y pruebas. Son propuestas pendientes:
esta comparación no instala ni integra Gentle Shell.

GENERATED BY AIKYA HARNESS
