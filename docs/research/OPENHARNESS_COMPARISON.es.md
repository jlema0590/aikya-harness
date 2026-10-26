# Aikya frente a OpenHarness: memoria, observación y persistencia

Revisión estática del 23 de octubre de 2026. OpenHarness fijado al commit
[9b2efd795c6aa09f88b0c257d269a9e518da6ae7](https://github.com/HKUDS/OpenHarness/tree/9b2efd795c6aa09f88b0c257d269a9e518da6ae7).
Base de Aikya: c3daaf3 y el cambio local de nombres de comandos. Se consultaron el
README y los archivos de implementación. No se instalaron dependencias ni se
ejecutó OpenHarness. Tampoco se midieron su rendimiento, sus proveedores o su consumo real.

## Conclusión

OpenHarness controla el bucle de conversación, las llamadas al modelo y las
herramientas. Por eso puede guardar y reconstruir sesiones, recuperar recuerdos
e intervenir directamente al compactar el contexto. Aikya añade metodología,
registros y observabilidad sobre Claude Code; su motor ODD/SDD no sustituye el
motor de conversación del cliente.

Lo más útil para Aikya es adoptar una capa de recuerdos duraderos tipados y
recuperación selectiva, conservando los expedientes y las aprobaciones como fuente
de estado verificado. Trasplantar el motor completo de OpenHarness supondría
cambiar la arquitectura y mantener dos sistemas de sesión/contexto.

Actualización posterior: Aikya añade un agent loop opcional y memorias de proyecto
tipadas con TTL y recuperación léxica acotada. La ampliación del 23 de octubre añade
ámbitos project/private, estados de revisión, migración explícita de identidad y
extracción opcional de candidatos mediante el mismo runtime. La tabla siguiente conserva la
comparación inicial; la [guía vigente](../AGENT_LOOP.md) detalla el código nuevo,
los límites y la prueba real pendiente en el otro entorno elegido por el usuario.
Aikya sigue delegando conversación y compactación al runtime de Claude Code.

## Comparación verificada inicial

| Aspecto | OpenHarness | Aikya en la revisión inicial |
|---|---|---|
| Conocimiento entre sesiones | MEMORY.md como índice y notas Markdown con metadatos, recuperación e inyección en el prompt. | Documentación y expedientes versionables; no se ha encontrado un motor propio equivalente de recuerdos y recuperación automática. |
| Memoria por sesión | Checkpoint Markdown determinista con objetivo, estado y actividad reciente; habilitado por defecto en MemorySettings. | Caché de ejecución con fases y actores; continuidad ODD/SDD en expedientes. No conserva la conversación completa en esa caché. |
| Extracción de recuerdos | Pasada opcional por el modelo; desactivada por defecto. | No implementada como servicio propio. El registro de documentación y evidencia es explícito. |
| Compactación | Microcompactación, reducción de contexto y resumen mediante modelo con metadatos de continuidad. | La compactación de la conversación pertenece al cliente Claude Code; Aikya mantiene su estado externo. |
| Observación de herramientas | Eventos del motor con inicio, argumentos, resultado y error de la herramienta. | Hooks y transiciones explícitas de fases; metadatos mínimos y evidencia de procesos locales. |
| Progreso visible | Eventos de streaming, estado observable y progreso específico de compactación. | Explore, Plan, Implement, Validate, Security y Review; estados separados, modelos observados y métricas disponibles. |
| Persistencia de conversación | JSON por sesión y latest.json, con mensajes, prompt de sistema, modelo, uso y metadatos seleccionados. | El cliente mantiene la conversación; Aikya persiste tareas, aprobaciones, documentación y caché propia de ejecución. |
| Persistencia del trabajo | Sesiones, memoria y salidas de tareas bajo su directorio de datos. | spec.md/state.json ODD y documentos/estado SDD bajo aikya/docs/, además de REQ e índice. |
| Continuidad validada | Conserva contexto y normaliza secuencias de herramientas incompletas al restaurar. | Comprueba revisiones, dependencias y huellas de archivos/evidencias; invalida resultados obsoletos. |
| Coste de observación | Los eventos locales no requieren por sí mismos un modelo; extracción, consolidación y resumen sí pueden invocarlo. | El adaptador de fases/métricas y la barra no realizan llamadas a modelos. |

Fuentes principales: [motor](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/query_engine.py),
[eventos](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/stream_events.py),
[sesiones](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/session_storage.py).
En Aikya: execution_state.py, execution_observer.py, runtime_metrics.py,
odd_engine.py, sdd_engine.py y los hooks/documentos de template/.

## 1. Control de memoria

Las notas tienen frontmatter con ID, tipo, ámbito, importancia, procedencia,
firma de contenido, fechas, TTL, desactivación y referencias supersedes. Los tipos
son user, feedback, project y reference; los ámbitos son private, project y team.
La firma normaliza contenido para detectar duplicados. El borrado manual puede
ser lógico: desactivar la nota y retirarla del índice. Las notas caducadas o
inactivas se filtran durante el escaneo.

[Esquema](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/schema.py) ·
[gestión](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/manager.py) ·
[escaneo](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/scan.py).

La recuperación por defecto revisada es léxica/heurística. Pondera coincidencias
en título/descripción y cuerpo, importancia, uso previo y antigüedad. La función
admite un selector adicional opcional; el ensamblador de contexto consultado usa
la selección por defecto. No debe describirse esta implementación como una base
vectorial o búsqueda por embeddings.

El índice se limita por defecto a 200 líneas y 25.000 bytes; max_files es 5.
La función que presenta recuerdos limita el contenido de cada nota a 8.000
caracteres por defecto: ese límite no es un presupuesto global de todos los
recuerdos ni una medición de tokens. Para Aikya convendría un límite total adicional.

[Búsqueda](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/search.py) ·
[selección](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/relevance.py) ·
[inyección en contexto](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/prompts/context.py).

La extracción automática consulta al modelo y propone hasta tres recuerdos por
defecto. También existe consolidación auto-dream con respaldos, diff y funciones
de restauración. Ambos automatismos están desactivados inicialmente. La
consolidación automática tiene umbrales configurables de 24 horas y cinco sesiones
por defecto; el modo manual puede tener condiciones distintas. No son servicios
que deban asumirse ejecutándose siempre.

[Configuración](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/config/settings.py) ·
[extracción](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/memory_extract/__init__.py) ·
[consolidación](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/autodream/service.py) ·
[respaldos](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/autodream/backup.py).

Hay memoria por agente con ámbitos user/project/local y snapshots de agente dentro
de .openharness/agent-memory-snapshots/. El almacén team consultado es una carpeta
del almacén local del proyecto; por sí solo no demuestra sincronización remota,
permisos distribuidos o colaboración entre máquinas. Las etiquetas private y
project tampoco equivalen por sí solas a aislamiento mediante ACL: el gestor
consultado guarda ambas en el almacén de proyecto, reservando una subcarpeta para team.

[Agentes](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/agent.py) ·
[equipo](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/team.py).

## 2. Observación

El motor emite AssistantTurnComplete con uso, ToolExecutionStarted,
ToolExecutionCompleted con is_error, ErrorEvent, StatusEvent y CompactProgressEvent.
Esto permite observar la ejecución desde su origen. Su AppStateStore notifica a
suscriptores en memoria; ese objeto no es, por sí mismo, un registro persistente.
Los hooks incluyen inicio/fin de sesión, antes/después de compactar y usar
herramientas, entrada de usuario y cierre de subagente.

[Emisión real de herramientas](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/query.py) ·
[estado observable](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/state/store.py) ·
[hooks](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/hooks/events.py).

En Aikya el resultado de una herramienta no completa automáticamente una fase:
Validate/Security requieren evidencia y Review identifica revisor y candidato.
Las comprobaciones asíncronas quedan vinculadas a candidate_generation para que
un resultado anterior a un cambio no valide el candidato nuevo. Los eventos se
correlacionan por proyecto/worktree, sesión e invocación.

OpenHarness puede observar argumentos y salidas completos porque es el runtime.
Aikya mantiene una caché reducida sin prompts ni salidas crudas. Copiar los eventos
completos cambiaría ese contrato de datos y no es necesario para mostrar fases.
En ninguno de los dos sistemas una notificación de herramienta, por sí sola,
certifica que la funcionalidad es correcta o que un proyecto es seguro.

## 3. Persistencia y recuperación

Rutas predeterminadas verificadas de OpenHarness; se pueden cambiar mediante
OPENHARNESS_CONFIG_DIR, OPENHARNESS_DATA_DIR y OPENHARNESS_LOGS_DIR:

```text
~/.openharness/
  settings.json
  data/
    memory/<nombre>-<hash-de-ruta>/MEMORY.md y notas
    memory/<nombre>-<hash-de-ruta>/team/
    memory/<nombre>-<hash-de-ruta>/agent/<tipo>/
    agent-memory/<tipo>/
    session-memory/<nombre>-<hash-de-ruta>/<sesion>.md
    sessions/<nombre>-<hash-de-ruta>/latest.json
    sessions/<nombre>-<hash-de-ruta>/session-<id>.json
    tasks/
  logs/
```

[Rutas](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/config/paths.py) ·
[identidad del almacén](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/memory/paths.py) ·
[memoria de sesión](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/session_memory/__init__.py).

El hash depende de la ruta absoluta: mover un repositorio o usar otro checkout
cambia la clave del almacén. Las notas bajo el directorio del usuario no se
versionan automáticamente en el Git del proyecto. Los snapshots de agente dentro
del proyecto son una opción distinta. Aikya, en cambio, puede versionar sus
expedientes y documentación dentro del repositorio; su caché de ejecución está
fuera de Git y no debe ser la única fuente de continuidad.

Los snapshots de conversación guardan mensajes y prompt de sistema, no solo
metadatos. sanitize_conversation_messages normaliza turnos y pares de herramientas
para restauración; no se presenta en ese código como redacción general de secretos.
El filtro de secretos de team usa patrones concretos y no debe confundirse con
una garantía sobre todo el historial.

[Snapshot y carga por ID](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/services/session_storage.py) ·
[normalización de mensajes](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/engine/messages.py).

La escritura atómica de OpenHarness usa archivo temporal, flush, fsync y reemplazo.
El gestor de memoria combina escritura atómica con bloqueo. Cada snapshot y
latest.json se escriben atómicamente por separado; esto no equivale a una
transacción conjunta de todos los archivos. En la caché de Aikya se usa bloqueo y
reemplazo atómico; no se ha encontrado fsync en execution_state.atomic. Por ello
no atribuyo a ambos la misma garantía ante un corte eléctrico.

[Escritura atómica](https://github.com/HKUDS/OpenHarness/blob/9b2efd795c6aa09f88b0c257d269a9e518da6ae7/src/openharness/utils/fs.py).

## 4. Agent loop: decisión e implementación posterior

Sí. Tras esta evaluación se implementa un controlador opcional de tareas
Aikya sobre el runtime de Claude Code: selección de trabajo autorizado, ejecución,
validación, revisión y otra iteración solo cuando corresponda. Los expedientes
ODD/SDD y los controles de execution_state.py proporcionan parte de la base;
los motores ODD/SDD por separado no ejecutan llamadas al modelo/herramientas.
El nuevo adaptador opcional agent_runtime.py proporciona esa integración.

El Claude Agent SDK ofrece el loop y las herramientas de Claude Code de forma
programable. Esto permite evaluar un adaptador opcional sin reproducir el motor
de OpenHarness. Se debe probar su compatibilidad con las skills, configuración
y permisos de Aikya antes de decidir la integración.
[Documentación oficial](https://code.claude.com/docs/en/agent-sdk/overview).

El loop necesita límites de iteraciones, turnos y tiempo, cancelación, persistencia
recuperable y cierre con evidencia actual. Los recuerdos ayudan a reconstruir
contexto, pero no autorizan tareas ni sustituyen revisiones. La salida final del
modelo tampoco demuestra por sí sola que las pruebas hayan pasado.

La propuesta y sus pruebas de aceptación están en el
[apartado 5 del plan](../../aikya/docs/plan/archive/harness-development/2026-10-23-command-names-openharness.es.md#5-agent-loop-dentro-de-aikya--implementación-opcional).
Construir además un runtime propio, con conversación y compactación, sería un
proyecto distinto de mayor esfuerzo. El loop sobre Claude tiene implementación
y pruebas locales; la prueba real con el proveedor se hará en otro entorno.

## Qué recomiendo incorporar a Aikya

1. Un registro de recuerdos duraderos tipados, separado de los expedientes y de
   los eventos: decisiones difíciles de reconstruir, preferencias y correcciones.
   Cada recuerdo tendría procedencia, fecha, ámbito, TTL y estado de revisión.
2. Índice compacto y recuperación léxica por petición, con presupuesto global de
   contexto y validación contra el proyecto actual. La memoria no concedería
   aprobaciones SDD ni daría por válidas evidencias antiguas.
3. Persistencia revisable: conocimientos de proyecto versionables bajo
   aikya/docs/memory/ y recuerdos privados fuera del repositorio. Identidad del
   proyecto y worktree explícita, con política de migración al moverlo.
4. Si se necesita mayor resistencia ante cortes, añadir fsync y pruebas de fallo
   a la persistencia que lo requiera. Mantener la caché de presentación prescindible.
5. Más adelante, extracción asistida por modelo como opción explícita: candidatos
   pendientes de revisión, con coste y límites visibles. No activar un segundo
   compactador de conversación mientras Claude Code siga siendo el runtime.

El esfuerzo relativo es bajo/medio para metadatos e índice, medio para recuperación
con presupuesto y migraciones, y alto para extracción/consolidación automática y
su evaluación. No son presupuestos económicos ni mediciones de rendimiento.
Las cinco recomendaciones tienen ahora una implementación local: metadatos y
revisión explícita, recuperación única con presupuesto combinado, almacén privado
externo y migración revisada, escritura duradera compartida y extracción opt-in
que deja candidatos pendientes. Las notas antiguas sin identidad se conservan y
requieren una revisión para entrar en el contexto del checkout actual.
La extracción no ejecuta consolidación automática ni otro compactador. No se ha
ejecutado OpenHarness ni se sustituye el motor de conversación de Claude Code.

La [validación de adopción](../../aikya/docs/validation/archive/2026-10-22/OPENHARNESS_ADOPTION.es.md) registra el
alcance, los controles de seguridad y mantenibilidad, la eliminación de copias de
distribución y la prueba real con el proveedor que continúa pendiente en el otro
entorno elegido por el usuario.

GENERATED BY AIKYA HARNESS
