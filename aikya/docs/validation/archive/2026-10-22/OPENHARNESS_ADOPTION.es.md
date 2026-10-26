# Adopción de OpenHarness y controles de código: validación

> Historical acceptance evidence. Original results and baselines are preserved; this is not a new execution report.

Fecha: 23 de octubre de 2026. Base: 6838bd1. Rama: feat/sdd-spec-coding-templates.
Esta ampliación se prepara localmente sobre la rama existente; no incluye push,
publicación ni llamadas a un modelo real.

## Resultado de las cinco recomendaciones

| Recomendación | Implementación local |
|---|---|
| Memoria tipada con procedencia, fecha, ámbito, TTL y revisión | agent_memory.py añade schema 2, identidad de checkout, project/private, pending/approved/rejected, fecha de revisión y origen manual/modelo. |
| Índice y recuperación con presupuesto global | Un único motor léxico para ambos ámbitos, hasta cinco notas únicas y presupuesto combinado en caracteres; excluye notas no aprobadas, caducadas, con fuentes modificadas o de otro checkout. |
| Persistencia revisable, privada y migrable | Proyecto en aikya/docs/memory/; privada fuera de Git, con directorios 0700 y archivos 0600 en POSIX. Migración explícita con validación de fuentes y recibo Markdown, conservando el almacén privado anterior. |
| Escritura duradera y pruebas de fallo | durable_io.py comparte fsync y reemplazo atómico entre documentos, memoria y checkpoints del loop. Se prueban interrupciones de reemplazo, migración y proyección del resumen. |
| Extracción asistida opcional | agent_memory_extract.py reutiliza ProcessRuntime, realiza una consulta acotada y genera hasta tres candidatos pendientes. Persiste intención, consumo disponible y resultado; no reintenta automáticamente consultas inciertas. |

Las notas schema 1 se conservan sin alterarlas, pero necesitan revisión explícita
para asociarlas al checkout actual: no contenían una identidad verificable. La
migración de recuerdos no migra aprobaciones del agent loop ni elimina límites.
Una migración interrumpida se inspecciona y se repite explícitamente; no es una
transacción conjunta de todos los archivos.

No se añade sincronización team, consolidación automática, otro motor de sesión
ni un segundo compactador. El runtime de conversación sigue siendo Claude Code.
La memoria privada no está cifrada; los modos POSIX no sustituyen controles de
acceso del sistema o del equipo. La extracción revela al runtime/proveedor el
contexto seleccionado y requiere autorización específica.

## Duplicidad encontrada y tratada

La auditoría estática inicial encontró 17 grupos de cuerpos Python repetidos.
Se eliminan las copias completas de external_skills.py y skills_registry.py bajo
template/scripts/harness/: la distribución utiliza los dos módulos canónicos de
la raíz mediante EXECUTION_FILES. Son 14 grupos de cuerpos eliminados, sin añadir
otro motor de memoria, otro adaptador SDK ni otra contabilidad de consumo.

La auditoría posterior examina 138 archivos de código y detecta tres grupos
restantes, todos vinculados a fixtures históricos de regresión: expected_versions
en el detector v5.6 y start_request/main en el docs_guard v3. Se conservan porque
representan versiones anteriores necesarias para comprobar migraciones.
La comparación es de cuerpos AST Python no triviales; no certifica ausencia de
duplicidad semántica en todos los lenguajes.

En actualizaciones global/project se retiran únicamente las copias de distribución
registradas y sin personalizaciones, dejando un respaldo. Una copia personalizada
permanece en disco. También se comparte el escritor duradero y la selección de
fuentes de configuración del runtime.

## Seguridad y mantenibilidad

El loop aplica alcance de archivos, herramientas limitadas, protección de rutas,
revisión de hooks, gates ODD/SDD, presupuestos, evidencia Validate/Security y Review
de solo lectura. Una afirmación de éxito del modelo no basta para cerrar la tarea.
Los procesos configurados y los hooks tienen los permisos del usuario: no se
presentan como un sandbox ni como una auditoría universal de vulnerabilidades.

code_quality.py añade un control de mantenibilidad independiente:

- Más de 1.000 líneas físicas por archivo de código candidato: error; exige
  modularización por responsabilidad o excepción justificada con SHA-256 vigente.
- Más de 100 líneas por función Python: aviso para revisar cohesión y extracción
  de helpers; no genera una reescritura automática.
- Cuerpos Python repetidos no triviales: aviso con ubicaciones para revisar una
  implementación común.
- El loop no completa tareas con errores. El hook normal informa después de
  Edit/Write; fuera del loop se necesita configurar el checker como gate requerido
  de proyecto/CI. El workflow de pruebas de Aikya lo ejecuta sobre cambios.

La inspección de los archivos de código modificados no presenta errores de tamaño
ni cuerpos duplicados. Sí avisa de la función run de agent_loop.py, de 147 líneas.
La auditoría completa detecta install.py, de 1.309 líneas, como deuda histórica;
no se ha modificado ni exceptuado para ocultar el hallazgo. Un análisis --all
devuelve fallo mientras exista ese archivo por encima del límite. Su separación
por responsabilidades requiere una refactorización específica con las pruebas de
instalación correspondientes. Una PR cuyo diff incluya ese archivo también debe
resolver el gate o aportar una excepción explícitamente revisada.

La [guía de controles](../../../../../docs/SECURITY_CONTROLS.md) distingue qué comprueba el código,
qué orientan las instrucciones y qué análisis de seguridad debe configurar cada
proyecto. La [guía del loop](../../../../../docs/AGENT_LOOP.md) documenta las operaciones de memoria.

## Evidencia de verificación

- Suite completa final: 472 pruebas OK con Python 3.10 y 472 OK con Python 3.13.
  Los logs contienen el ResourceWarning preexistente de project_discovery.py,
  sin fallos de unittest. No se afirma haber ejecutado esta revisión completa
  también con Python 3.11/3.12; esos entornos permanecen en la matriz de CI.

- Pruebas dirigidas de memoria: 14 métodos; incluyen revisión, aislamiento privado,
  compatibilidad conservadora, migración interrumpida, rutas simbólicas, cambio de
  fuente entre lectura y llamada, salida inválida, timeout y consumo desconocido.
- Pruebas dirigidas de calidad: cinco métodos; límite 1.000/1.001, excepciones
  caducadas por cambios, clones, rutas inseguras, feedback y bloqueo del loop.
- Contrato del SDK instalado: opciones reales y hooks de solo lectura para Review
  y extracción, esquema de tres candidatos, permisos y límites; sin autenticación
  ni llamadas a un modelo.
- Actualización desde la fuente real del commit 6838bd1: registro global/project y
  proyecto inicializado; las herramientas nuevas arrancan desde sus instalaciones,
  se retiran copias gestionadas y se conserva un CLAUDE.md personalizado.
- Assets: 30 agentes, 29 skills de ingeniería y 27 comandos públicos válidos.
- Catálogo: 120 plantillas y 155 referencias verificadas contra el commit fijado.
- Perfiles: 14/14 ejemplos. Proxy estático de instrucciones: 3.107 frente a 6.000;
  no equivale a tokens facturados.
- Versión 6.1.1 conservada, sin tag de publicación.

La aceptación con un proveedor real, tanto del loop como de la extracción,
permanece en el otro entorno elegido por el usuario. Los workers sintéticos no
demuestran comportamiento de un LLM ni costes reales. Los recibos muestran
estimaciones informadas por el SDK; los datos ausentes no se convierten en cero.

GENERATED BY AIKYA HARNESS
