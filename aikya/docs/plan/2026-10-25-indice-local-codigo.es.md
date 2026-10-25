# Plan de implementación: índice local e incremental de código

**Estado:** propuesta pendiente de revisión del desarrollador. Este documento no implementa ni activa la funcionalidad.

**Objetivo:** que Aikya localice rápidamente clases, funciones, métodos y sus archivos, reutilice el análisis del código que no cambió y entregue a la IA únicamente el contexto relevante y actualizado.

**Arquitectura:** índice regenerable por proyecto en SQLite, analizadores por lenguaje y actualización por huellas de contenido. La memoria documental existente conserva decisiones y convenciones; el índice conserva información derivada del código. Ambos permanecen locales al proyecto en este flujo.

**Tecnologías:** Python 3.10–3.13, `sqlite3`, `hashlib`, `ast`, analizadores Tree-sitter opcionales y pruebas `unittest`. LSP queda para una ampliación posterior, después de validar este índice.

**Requisitos de origen:** petición del desarrollador de conservar el conocimiento de clases y cambios por proyecto, evitar relecturas completas por la IA y no añadir servicios de memoria de pago. La implementación se realizará en una rama independiente después de revisar este plan.

## 1. Alcance y límites

- Almacenamiento y consultas sin llamadas a un modelo, embeddings remotos, cuentas adicionales ni bases de datos externas.
- La IA seguirá leyendo el fragmento actual antes de editarlo. El índice no garantiza comprensión permanente ni sustituye pruebas, evidencias o aprobaciones ODD/SDD.
- La primera indexación analiza los archivos elegibles; las siguientes solo vuelven a analizar los que cambiaron. Verificar huellas puede leer bytes localmente: el objetivo es reducir el análisis repetido y el código enviado al modelo, no prometer cero lecturas de disco.
- Cada proyecto y worktree tiene identidad y caché propias. Cambiar de rama, mover el proyecto o modificar la versión del analizador obliga a reconciliar o reconstruir la información afectada.
- No se importará ni ejecutará código del proyecto para indexarlo. No se instalarán analizadores, SDK ni servidores de lenguaje automáticamente.
- No se creará otra memoria de decisiones, otro compactador de conversaciones ni un segundo motor de búsqueda de notas. Se reutilizará `aikya.memory.knowledge` para las notas revisadas existentes.
- No se añaden slash commands públicos en la primera versión: se mantienen los 27 actuales y se incorpora una CLI interna del paquete.
- Código e instrucciones de ingeniería en inglés. Este plan está en español por petición expresa; documentación generada según la política en/es del proyecto.

## 2. Datos y ubicación

| Ruta propuesta | Contenido | Git |
|---|---|---|
| `.aikya/code-index.json` | Política versionada: habilitado, alcance y límites; sin credenciales | Según la política del proyecto; documento de configuración protegido |
| `.harness/state/code-index/index.sqlite` | Archivos, símbolos, importaciones, relaciones detectadas, generaciones y cambios pendientes | Excluido, regenerable y local |
| `aikya/docs/memory/` | Notas de decisiones y convenciones con el mecanismo existente | Según la política del proyecto |
| `aikya/docs/validation/code-index-<id>.md` | Informe solicitado con cobertura, omisiones y resultados reales | Auditable, con pie e índice de documentación |

No se almacenarán copias completas de archivos fuente en SQLite. Cada símbolo incluirá nombre, tipo, nombre cualificado, archivo relativo, posiciones, firma acotada, huella del archivo, analizador y versión. Las relaciones sintácticas no se presentarán como resolución semántica completa. Los objetos creados dinámicamente durante la ejecución no se observarán en esta primera versión.

La tabla de archivos distinguirá `indexed`, `file_only`, `parse_error`, `excluded` y `oversized`. Los registros eliminados perderán sus símbolos y relaciones en la misma transacción.

Contratos del paquete: `SymbolRecord` contiene `name`, `qualified_name`, `kind`, `path`, `start_byte`, `end_byte`, `start_line`, `end_line`, `signature`, `file_sha256`, `parser_id` y `parser_version`. Las líneas son base 1 y los rangos de bytes UTF-8 son base 0, con extremo final exclusivo. `ParsedFile` contiene `path`, `sha256`, `status`, `symbols`, `imports`, `relations` y `diagnostics`. `SyncResult` contiene `generation`, `status`, `parsed_files`, `verified_bytes` y `skipped_files`. `QueryResult` contiene `generation`, `status`, `matches`, `truncated` y `diagnostics`; cada coincidencia identifica su archivo, huella y fragmento. Ninguna relación sintáctica se marca como semánticamente resuelta.

## 3. Cobertura por etapas

| Etapa | Cobertura verificable |
|---|---|
| A: núcleo funcional | Python mediante `ast`: clases, funciones, métodos, anidamiento e importaciones. Inventario y búsqueda por ruta para otros archivos de texto elegibles, identificados como `file_only` |
| B: primera ampliación | JavaScript, TypeScript/TSX, Java, C# y Go mediante gramáticas Tree-sitter aprobadas y fijadas; pruebas de símbolos y posiciones por lenguaje |
| C: móvil y ampliaciones | Kotlin, Swift y Dart; después Rust, PHP, Ruby y C/C++, incorporados uno a uno con la misma aceptación |
| D: opcional posterior | LSP para referencias, tipos y llamadas resueltas cuando exista un servidor compatible y el desarrollador autorice su ejecución |

No se anunciará soporte completo para todos los lenguajes. Sin analizador compatible seguirá disponible el inventario por archivo y la lectura directa de fragmentos; se mostrará la limitación. Antes de añadir cada dependencia se verificará su versión, licencia, compatibilidad de gramática y distribución en Linux/macOS/Windows. Si falta una rueda compatible, se mantiene el modo básico y se informa; no se compila ni descarga sin autorización.

## 4. Experiencia prevista

1. `/aikya-init` o `/aikya-analyze --approved` configura el índice local junto con la incorporación aprobada. Un proyecto vacío conserva únicamente la política; no genera notas, clases ni documentos de memoria ficticios.
2. Al comenzar un comando de trabajo, una sincronización local identifica archivos nuevos, modificados, renombrados y eliminados. Los hashes sin cambios evitan volver a ejecutar analizadores.
3. Tras una escritura correcta del host, un hook acotado marca archivos como pendientes. No reconstruye todo el repositorio durante el hook ni reemplaza hooks personalizados.
4. Antes de recuperar contexto, se sincronizan los pendientes y se validan las huellas de los fragmentos seleccionados. Cambios mediante editor, Git, herramientas externas o comandos de shell también se detectan en la reconciliación al entrar en el comando o al solicitar una sincronización completa.
5. La IA consulta símbolos, rutas e importaciones; recibe ubicaciones y fragmentos actuales con límites. Ejemplo: buscar `UserService` identifica su clase y sus métodos, sin incluir todos los controladores del repositorio.
6. Un archivo modificado se vuelve a analizar; sus relaciones anteriores se invalidan. Para dependientes se actualizan las relaciones resolubles y se marca la incertidumbre restante.
7. Si la caché está deshabilitada, dañada, incompleta o no puede actualizarse dentro del límite, el comando conserva su funcionamiento habitual y realiza lecturas directas. Nunca entrega una caché antigua como si estuviera actualizada.

No habrá un daemon obligatorio en el MVP. La actualización es automática en los puntos de integración anteriores; no se promete observación instantánea de cualquier editor mientras Aikya está inactivo.

## 5. Seguridad y límites iniciales

- Reutilizar las validaciones de rutas e identidad existentes, sin crear una copia de `safe_file` ni mezclar este índice con el descubrimiento de frameworks de `discovery/scanner.py`.
- Excluir `.git`, `.harness`, `.aikya`, `.claude`, entornos, dependencias, compilados, binarios y archivos ignorados por Git; excluir siempre credenciales, claves, `.env` y rutas secretas, aunque estén versionadas.
- No seguir enlaces simbólicos ni atravesar submódulos o raíces externas. Revisar nuevamente contención y huella al leer un fragmento para reducir carreras entre indexación y consulta.
- Límites predeterminados: 12.000 archivos elegibles, 1 MiB por archivo de código, 100 MiB de entrada por sincronización. Alcance ampliado solo por configuración explícita. Informar omisiones y estado parcial.
- Consultas con SQL parametrizado, máximo 20 resultados y 6.000 caracteres de contexto serializado por defecto; techo configurable de 16.000 caracteres. Distinguir este límite del presupuesto de notas `memory_budget_chars` y de los costes del modelo.
- Una generación de índice por transacción; bloqueo de escritor, espera acotada y rollback si se interrumpe. Un lector no mezcla generaciones. Validar integridad y versión de esquema antes de reutilizar SQLite.
- Registrar métricas locales de archivos analizados, bytes verificados, aciertos, omisiones y fragmentos entregados; no guardar prompts completos, conversaciones ni valores de secretos.
- Los previews, `--dry-run` y `--report-only` no crean política, caché ni informes. La lectura por el agent loop respeta sus archivos/contexto ya autorizados: el índice no amplía el alcance del hijo.

## 6. Estructura propuesta

```text
src/aikya/code_index/
  __init__.py
  __main__.py        # CLI interna
  contracts.py       # Tipos y límites
  policy.py          # Configuración y exclusiones
  store.py           # SQLite y transacciones
  scan.py            # Inventario y huellas
  sync.py            # Generaciones y cambios
  query.py           # Búsqueda y fragmentos verificados
  hooks.py           # Marcado acotado de archivos pendientes
  parsers/
    __init__.py
    python.py        # AST de Python
    registry.py      # Analizadores aprobados
    treesitter.py    # Adaptadores opcionales de la etapa B
```

Se ampliará el inventario de distribución existente para incluir este paquete: no se crearán adaptadores Python nuevos en la raíz. SQLite y las gramáticas opcionales no serán herramientas arbitrarias disponibles para el modelo hijo.

## 7. Tareas de implementación y aceptación

### Tarea 1: política local y almacenamiento

**Archivos:** nuevos `contracts.py`, `policy.py`, `store.py`; pruebas `tests/test_code_index_store.py` y `tests/test_code_index_policy.py`.

**Interfaces:** `IndexOptions` con habilitación, alcance y límites; `load_policy(root: Path) -> IndexOptions`; `IndexStore(root: Path)` con transacciones y `status() -> dict`. La política no contiene opciones de facturación ni almacenes globales.

- [ ] Escribir pruebas que fallen para aislamiento de dos proyectos/worktrees, symlinks, secretos versionados, SQL no parametrizado, esquema incompatible y escritura interrumpida.
- [ ] Implementar las tablas de archivos/símbolos/importaciones/relaciones y generaciones de acuerdo con las secciones 2 y 5.
- [ ] Ejecutar `python -m unittest discover -s tests -p 'test_code_index_*store*.py' -v` y las pruebas de política; comprobar que una escritura cancelada conserva la generación previa.
- [ ] Guardar un commit verificable de esta tarea.

### Tarea 2: inventario incremental y analizador Python

**Archivos:** `scan.py`, `sync.py`, `parsers/python.py`, `parsers/registry.py`; `tests/test_code_index_sync.py`, `tests/test_code_index_python.py` y fixtures de lenguajes.

**Interfaces:** `parse_file(path: str, content: bytes) -> ParsedFile`; `sync(root: Path, *, full: bool = False) -> SyncResult`, con generación, archivos analizados/omitidos, bytes verificados y estado completo/parcial. Los analizadores nunca importan módulos del proyecto.

- [ ] Probar que una segunda sincronización sin cambios ejecuta cero analizadores, y que editar un único archivo Python ejecuta exactamente uno.
- [ ] Probar altas, borrados, renombrados, cambios de rama, Unicode, archivos truncados, errores de sintaxis, rutas largas y huellas modificadas aunque coincidan tamaño/fecha en una reconciliación completa.
- [ ] Implementar reconciliación por hash y sustitución transaccional de los símbolos de cada archivo. No conservar símbolos válidos de una versión que ya no coincide.
- [ ] Ejecutar las pruebas de sincronización y Python; guardar el commit.

### Tarea 3: recuperación de contexto y CLI interna

**Archivos:** `query.py`, `__main__.py`; `tests/test_code_index_query.py` y `tests/test_code_index_cli.py`.

**Interfaces:** `query(root: Path, text: str, *, allowed_files: list[str] | None = None, max_chars: int = 6000) -> QueryResult`; resultado con generación, cobertura, símbolos, referencias detectadas y fragmentos verificados. CLI: `python -m aikya.code_index {build,sync,query,status,clear}`; `clear` elimina solo la caché propia y exige aprobación explícita.

- [ ] Probar clases homónimas en módulos distintos, código anidado, ausencia de resultados, lenguajes `file_only`, límites y cambios del archivo entre búsqueda y lectura.
- [ ] Probar que `allowed_files` impide recuperar archivos fuera del alcance del loop y que ningún resultado obsoleto se presenta como vigente.
- [ ] Implementar búsqueda determinista por nombre/ruta con SQLite; FTS solo si la biblioteca local lo soporta, manteniendo un fallback probado sin FTS.
- [ ] Verificar los resultados públicos y códigos de salida de la CLI; guardar el commit.

### Tarea 4: incorporación, comandos y cambios de archivos

**Archivos:** `installation/preflight.py`, `installation/pipeline.py`, inventario `installation/assets.py`, `middleware/configuration.py`, `code_index/hooks.py`, `cli/main.py`, `core/loop.py` y las instrucciones de los comandos afectados. Pruebas `tests/test_code_index_integration.py`.

**Interfaces:** `mark_dirty(root: Path, paths: list[str]) -> None` acotado y con validación; integración del recuperador en el orquestador del loop, manteniendo sus herramientas y autorizaciones actuales.

- [ ] Probar init/analyze aprobados, proyecto vacío, ODD/SDD, en/es, scopes global/project y previews sin escrituras.
- [ ] Probar escrituras mediante `Write`/`Edit`, eliminación/renombrado externos y cambios no observados por hooks que se detectan al reconciliar.
- [ ] Fusionar hooks sin duplicarlos ni sustituir los personalizados; un fallo del índice no bloquea el trabajo ordinario ni concede permisos.
- [ ] Integrar recuperación previa al trabajo y actualizar únicamente documentación con datos reales; guardar el commit.

### Tarea 5: multilenguaje progresivo

**Archivos:** `parsers/treesitter.py`, registro, consultas por gramática y fixtures; dependencia opcional en `pyproject.toml` y atribuciones cuando correspondan. Pruebas `tests/test_code_index_languages.py`.

- [ ] Aprobar un manifiesto de versiones exactas y licencias para el runtime Tree-sitter y cada gramática de la etapa B, después de verificar compatibilidad en los tres sistemas; sin dependencias flotantes ni instalaciones automáticas.
- [ ] Escribir expectativas independientes para clases, métodos, funciones, firmas, importaciones y posiciones en cada lenguaje anunciado.
- [ ] Implementar cada adaptador y su fallback por separado. En el MVP se vuelve a analizar el archivo cambiado; reutilizar árboles internos de Tree-sitter requiere conservar y aplicar ediciones exactas y queda como optimización posterior.
- [ ] Guardar cobertura y limitaciones por lenguaje. Aplicar la misma puerta de aceptación a cada incorporación de la etapa C.

### Tarea 6: batería adversarial, rendimiento y distribución

**Archivos:** pruebas `test_code_index_adversarial.py`, `test_code_index_performance.py`, `test_code_index_distribution.py`; CI de pruebas/instaladores; informe bajo `aikya/docs/validation/`.

- [ ] Probar corrupción de SQLite, límites de entrada, concurrencia, salida durante commit, caché copiada, gramática ausente/incompatible, contenido no confiable y rutas de secretos.
- [ ] Medir en fixtures de 100, 1.000 y 10.000 archivos: primer análisis, consulta caliente, un archivo editado, reconstrucción y tamaño de caché. Registrar tiempos y bytes reales; no prometer porcentajes de ahorro de tokens sin medirlos.
- [ ] Verificar wheel/sdist, instalación sin clonar, actualización y uso del paquete desde runtimes copiados; ejecutar Python 3.10–3.13 y Linux/macOS/Windows.
- [ ] Ejecutar la batería completa, los 27 comandos/contratos existentes, perfiles y controles de documentación/calidad. Mantener la prueba autenticada del modelo como aceptación separada.
- [ ] Actualizar README en/es, changelog y `indice.md`; guardar commit e informe antes de abrir la PR de la funcionalidad.

## 8. Orden, esfuerzo y aprobación

| Entrega | Estimación orientativa de trabajo técnico |
|---|---|
| Etapa A: tareas 1–4 y aceptación inicial | 5–8 jornadas |
| Etapa B y aceptación multilenguaje | 4–7 jornadas adicionales |
| Etapa C | 1–3 jornadas por grupo de lenguajes, según gramáticas y plataformas |
| LSP | Evaluación posterior; no comprometida en este alcance |

Son estimaciones de esfuerzo, no una tarifa, consumo de tokens ni fecha comprometida. La indexación y recuperación locales no requieren un proveedor de IA; los fragmentos usados por el modelo participan en su consumo habitual de contexto.

Primero se revisa y aprueba la PR de adaptadores/instaladores/worker actual contra `develop`. La nueva rama `feat/local-code-index` se prepara desde esa cabeza para conservar las correcciones; después de integrar la PR se actualiza respecto a `develop`. Si la fusión es squash, se trasladarán únicamente los commits propios de la funcionalidad. La implementación de este plan empieza después de revisarlo con el desarrollador; no se mezcla con la PR de mantenimiento.

## 9. Referencias técnicas

- [Tree-sitter: introducción y gramáticas](https://tree-sitter.github.io/tree-sitter/): análisis sintáctico y cobertura por analizador.
- [Tree-sitter: edición de árboles](https://tree-sitter.github.io/tree-sitter/using-parsers/3-advanced-parsing.html): requisitos para reutilizar árboles tras cambios exactos.
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/): posibles ampliaciones de navegación y referencias; no dependencia del MVP.

GENERATED BY AIKYA HARNESS
