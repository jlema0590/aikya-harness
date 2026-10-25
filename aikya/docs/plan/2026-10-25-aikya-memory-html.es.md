# Plan de ampliación: /aikya-memory y visor HTML local

**Estado:** núcleo del visor, comando y actualización automática implementados en `feat/automatic-local-memory`. El [HTML generado](../examples/aikya-memory-generated.html) procede del exportador real sobre una fixture controlada. El [informe](../validation/LOCAL_MEMORY_IMPLEMENTATION.md) registra pruebas y límites; V5 conserva como ampliación separada la resolución Maven/Spring y los recorridos semánticos, sin presentarlos como capacidades entregadas.

**Objetivo:** ejecutar `/aikya-memory` y obtener un HTML navegable con la memoria registrada del proyecto, sus fuentes, relaciones verificables y límites de cobertura.

**Arquitectura:** una proyección de lectura sobre las notas existentes, la documentación y el índice incremental del [plan base](2026-10-25-indice-local-codigo.es.md). El HTML es una instantánea regenerable; no se convierte en otra base de conocimiento ni sustituye los documentos originales.

**Tecnologías:** Python 3.10–3.13, bibliotecas estándar, HTML/CSS/JavaScript propios y un grafo SVG acotado. No se necesita instalar un servidor, Node.js, un modelo ni una biblioteca JavaScript remota para generar o abrir el informe.

**Requisito de origen:** petición de `/aikya-memory` con salida HTML y un grafo navegable como referencia visual. La [revisión de referencia](../research/2026-10-25-graphify-memory-viewer.md) registra el commit inspeccionado y las diferencias. Por aclaración posterior del desarrollador, se retirarán las integraciones preseleccionadas de Aikya y los README, conservando la instalación genérica a elección del usuario; véase el [plan de desacoplamiento y coste](2026-10-25-skills-a-eleccion-del-usuario.es.md).

## 1. Qué significa toda la memoria

| Fuente | Datos mostrados | Disponibilidad |
|---|---|---|
| Notas de `aikya/docs/memory/` | Texto válido completo, tipo real, revisión, caducidad, fuente y vigencia comprobable | Ya existe; se reutiliza su validador |
| Índice `.harness/state/code-index/index.sqlite` | Archivos, clases, funciones, métodos, firmas, posiciones, importaciones y relaciones registradas | Requiere implementar el plan base |
| Documentación de `aikya/docs/` | Ruta, título, encabezados, enlaces internos explícitos y extracto acotado; incluye planes, bugs, features y dossiers ODD/SDD existentes | Ya existe; no se inventan documentos ni se interpretan como aprobaciones |

Toda significa todos los registros elegibles del proyecto dentro de los límites declarados. No significa copiar todo el código fuente ni conocer objetos dinámicos, conversaciones, secretos o datos de otros proyectos. Las notas pendientes, rechazadas o caducadas se pueden inspeccionar con su estado; mostrarlas no las habilita para recuperación por la IA.

Se excluyen los almacenes privados externos al proyecto, transcripciones, credenciales, directorios ignorados y rutas fuera del alcance autorizado. Los archivos con esquemas inválidos se contabilizan como omitidos sin mostrar su contenido. No se recoge ningún dato por fuera del proyecto para completar el grafo.

Un documento de memoria se representa una sola vez, aunque también figure en `indice.md`. Los archivos del propio visor quedan excluidos de la recolección para evitar que cada exportación incorpore la anterior.

## 2. Comando y archivos resultantes

```text
/aikya-memory
/aikya-memory --open
/aikya-memory --refresh --open
/aikya-memory --dry-run
/aikya-memory --watch --open
```

| Opción | Comportamiento previsto |
|---|---|
| Sin opciones | Exportar notas y documentación actuales y la generación del índice disponible; devolver un enlace al HTML |
| `--open` | Abrir el archivo local al terminar correctamente; junto con `--watch`, abrir la vista en vivo en localhost |
| `--refresh` | Sincronizar primero el índice bajo su política previamente autorizada y sus límites; nunca crear/revisar notas ni habilitar un índice desactivado |
| `--dry-run` | Informar fuentes, límites y destinos; sin escribir documentos, caché, estado, bytecode, sockets ni abrir el navegador; incompatible con `--refresh` y `--watch` |
| `--watch` | Mantener actualización automática local de índice/HTML; con `--open`, refrescar también la vista abierta mediante el servidor local explícito del plan complementario |
| `--docs-lang en\|es` | Usar el idioma de documentación elegido; por defecto, resolver la política del proyecto con el mecanismo existente |

La CLI del paquete será `python -m aikya memory --target <project> [opciones]`. No se añade un script Python en la raíz. La skill del slash command resolverá el paquete/runtime instalado existente, sin reinstalarlo.

```text
aikya/docs/memory/
  MEMORY.md                 # Índice de notas existente; el visor no lo modifica
  <id>.md                   # Notas existentes; el visor no las modifica
  view/
    index.html              # HTML autocontenido y regenerable
    report.md               # Cobertura, generación, límites y omisiones reales
```

El HTML llevará JSON, CSS y JavaScript embebidos. Abrirá con `file://`, sin `fetch`, CDN, servidor ni llamadas de red. `report.md` tendrá el pie habitual y aparecerá en `aikya/docs/indice.md`; no se añade un índice Markdown paralelo. El HTML mostrará también `GENERATED BY AIKYA HARNESS` como pie visible.

La inicialización nueva añade una exclusión precisa para `aikya/docs/memory/view/index.html`, conservando las reglas del usuario. La adopción de proyectos existentes preserva su archivo de ignore y documenta los patrones que puede añadir el desarrollador. El informe Markdown es versionable según su política; no contiene textos de notas ni fragmentos sensibles. Exportar no ejecuta `git add`, commit, push ni publicación.

Si no hay notas, índice o documentación, se genera un estado vacío útil y se señalan las fuentes ausentes. Sin índice, el visor funciona con notas/documentos y muestra `code_index: unavailable`. Si `--refresh` requiere una política que no está habilitada, explica el requisito sin modificarla.

## 3. Experiencia visual

- Cabecera **Aikya Memory**, identidad relativa del proyecto, fecha de instantánea, generación del índice y cobertura completa/parcial.
- Grafo con archivos, símbolos, notas y documentos; colores por tipo de dato y agrupación determinista por carpetas, sin inventar subsistemas.
- Búsqueda por nombre, ruta y texto de las notas incluidas. Filtros por tipo, lenguaje, carpeta, revisión y vigencia.
- Selección de un nodo: contenido o firma, ruta relativa, líneas cuando existan, procedencia y conexiones documentadas. Las rutas se pueden copiar; no se generan enlaces ejecutables desde texto no confiable.
- Vista de lista con paginación, navegación por teclado y detalle legible, también si el grafo no puede renderizarse. No depender del color como única indicación de estado.
- Temas claro/oscuro/sistema; respetar movimiento reducido. El idioma de la interfaz sigue en/es y las fases públicas siguen en inglés.
- Contadores calculados a partir del conjunto exportado, diferenciados del total de fuentes elegibles. Nunca anunciar cobertura total cuando hubo omisiones.

El HTML exportado es una instantánea con hora y generación. La [ampliación de actualización automática](2026-10-25-memory-actualizacion-automatica.es.md) añade un observador local que regenera el archivo tras cambios elegibles, sin llamadas a modelos. Una pestaña abierta con `file://` conserva la instantánea hasta recargar; `--watch --open` abre una vista en vivo en localhost que recibe nuevas generaciones y conserva filtros/selección. El modo estático mantiene su funcionamiento sin servidor ni conexiones de red. La implementación y sus pruebas se registran en el informe; las vistas previas históricas conservan su carácter de ejemplos.

### Animación solicitada y ejemplo interactivo

El [HTML de ejemplo](../examples/aikya-memory-preview.html) usa 19 nodos y 19 relaciones extraídos de una selección real de archivos de Aikya; no contiene notas ficticias ni constituye una exportación completa. Permite probar selección, búsqueda, filtros, inventario, enfoque, zoom, temas y movimiento reducido. Su captura está en [la vista previa](../examples/aikya-memory-preview.png). Es un artefacto de diseño, no la implementación de `/aikya-memory`.

| Interacción | Movimiento propuesto | Propósito |
|---|---|---|
| Primera apertura o repetir entrada | Opacidad de grupos en 180 ms, desfase máximo de 40 ms entre tipos | Mostrar la aparición de las fuentes sin simular trabajo en segundo plano |
| Selección con puntero | Cambio de opacidad y detalle en 140–160 ms | Confirmar la selección y distinguir sus relaciones |
| Enfocar o cambiar zoom mediante botones | Transformación de la vista en 220 ms | Mantener la orientación espacial |
| Búsqueda, filtros y selección con teclado | Resultado inmediato, sin desplazamientos animados | Mantener velocidad y estabilidad en uso frecuente |
| Preferencia de movimiento reducido o botón Motion off | Sin movimiento, zoom instantáneo y transiciones desactivadas | Respetar la elección del usuario desde la carga |

Tokens compartidos: `--fast: 140ms`, `--enter: 220ms`, salida `cubic-bezier(0.23, 1, 0.32, 1)` y movimiento de la vista `cubic-bezier(0.77, 0, 0.175, 1)`. CSS para opacidad; Web Animations API para entradas y enfoque controlados. Animar solo opacidad y transformaciones. No hay librería de animación ni proceso continuo obligatorio.

Las animaciones deben poder interrumpirse y continuar desde el estado visible, sin acumular movimientos. Detenerlas al cambiar a movimiento reducido o al ocultar la página. No mover nodos de forma permanente, hacer parpadear cifras, simular sincronización ni animar búsquedas por cada pulsación. La repetición de entrada solo ocurre por petición del usuario.

Reservar 4–8 h adicionales para esta animación y sus comprobaciones en navegador; no volver a contar el desarrollo ordinario de V2. Probar carga, acciones rápidas, teclado y cambio de preferencia del sistema con movimiento normal y reducido.

### Estructura y flujos para proyectos Java grandes

El [ejemplo Java interactivo](../examples/aikya-memory-java-preview.html) presenta un escenario **ilustrativo**, no extraído de un repositorio Java real: cinco módulos Maven y trece archivos Java. Las capturas muestran la [arquitectura](../examples/aikya-memory-java-architecture.png) y el [flujo de ejemplo](../examples/aikya-memory-java-flow.png).

```text
meridian-commerce/                 # Escenario ilustrativo
  pom.xml                         # Agregador Maven
  apps/api-host/                  # Entrada de la aplicación Spring
  modules/orders/                 # API, aplicación, dominio, puertos, persistencia y tests
  modules/inventory/              # Inventario y reservas
  modules/payments/               # Pagos y sus interfaces
  modules/shared-kernel/          # Tipos compartidos
```

Esta estructura no se impone a los proyectos analizados: un monolito, un proyecto Gradle o una distribución diferente se mostrarán conforme a sus archivos reales.

| Vista conectada | Contenido y navegación |
|---|---|
| Knowledge graph | Red de nodos de módulos, clases, interfaces, tests y documentos; colores, vecinos, filtros y zoom, conservando el estilo de grafo de la primera propuesta |
| Árbol del proyecto | Módulos, source sets, paquetes y clases desplegables; nombres cualificados para distinguir homónimos |
| Arquitectura | Grafo inicial por módulos y dependencias declaradas; paquetes y clases bajo demanda, conservando el contexto del módulo |
| Request flow | Entradas y relaciones con evidencia, bifurcaciones y bindings no resueltos; sin completar huecos |
| Inventario y detalle | Búsqueda de clases/rutas, firmas, procedencia y tests/documentos vinculados explícitamente |

Por petición del desarrollador se conserva también la experiencia de grafo de nodos de la primera versión, inspirada visualmente en la referencia revisada. El HTML Java abre en **Knowledge graph**, con 23 nodos ilustrativos: mantiene arquitectura, recorrido e inventario como vistas complementarias sobre los mismos datos. La [captura del grafo Java](../examples/aikya-memory-java-network.png) muestra el resultado.

La selección del grafo comparte el contexto con el árbol y el detalle. Añadir filtros por tipo y módulo, búsqueda, zoom y **Only neighbors** para aislar conexiones del nodo elegido; informar cuántos nodos y relaciones permanecen visibles. Volver al grafo completo no modifica la memoria ni reconstruye el índice. Es una vista propia del mismo snapshot, no otra integración, dependencia o base de conocimiento.

El recorrido ilustrado de `POST /orders` pasa por `OrderController` y `PlaceOrderService`. El servicio crea el agregado mediante `Order.create()` y persiste a través de `OrderRepository`, el adaptador JPA y PostgreSQL. El servicio llama al dominio y al puerto: no se dibuja una llamada falsa del agregado al repositorio. La vinculación interfaz–implementación está declarada como ejemplo, no como un binding Spring verificado.

**Next step** recorre el ejemplo por acción del usuario y actualiza el detalle. La animación no representa ejecución, latencia ni éxito real. La referencia a `PlaceOrderServiceTest` tampoco demuestra que el test haya pasado. En el producto, módulos y ramas se renderizan bajo demanda; buscar un símbolo abre su contexto sin materializar todo el árbol en el DOM ni dibujar todas las clases a la vez.

**Límites de fidelidad:**

- Leer la estructura y las dependencias desde archivos permitidos. En Maven distinguir agregación, dependencias, scopes y propiedades no resueltas. No ejecutar Maven/Gradle ni descargar dependencias; rechazar entidades XML externas y acotar las lecturas.
- Construir paquetes y declaraciones con el analizador Java de la etapa B. El nombre de una carpeta no demuestra una capa arquitectónica; una capa documentada manualmente mantiene esa procedencia.
- Anotaciones Spring literales pueden identificar entradas; expresiones, propiedades, herencia e inyección compleja permanecen sin resolver si falta evidencia suficiente.
- Un AST no prueba el destino efectivo de interfaces, proxies, aspectos o reflexión ni el orden de ejecución. Distinguir estructura extraída, recorrido declarado, relaciones resueltas y traza observada.
- Una vista estática no se etiqueta como traza real por tener flechas. Cualquier futura ingestión de trazas requiere fuente y alcance explícitos; no habilita instrumentación, conexiones a producción ni LSP automáticamente.

Entregar estructura/módulos primero y relaciones Java/Spring después de disponer del analizador y sus evidencias. El visor de notas/documentos sigue funcionando antes de esas ampliaciones.

## 4. Relaciones y estado de confianza

- `contains`: relación sintáctica registrada entre archivo, clase y método.
- `references`: fuente explícita de una nota o enlace Markdown interno validado.
- `imports`: importación que el analizador ha registrado; una dependencia no resuelta conserva ese estado y no se transforma en una llamada entre clases.
- `aggregated`: grupo visual calculado con sus miembros y recuentos; no se presenta como una relación semántica extraída.

Cada relación enlaza su evidencia, archivo y posición cuando exista. En el MVP solo hay conexiones explícitas; no se deducen asociaciones por parecido de texto ni se llama a un modelo para rellenar huecos. Las etapas futuras pueden incluir resolución determinista, identificada por separado y con pruebas.

Para las notas se conservan `kind` y `review_state` del contrato actual. Se calculan, por separado, identidad del proyecto, vencimiento, estado de la fuente y `eligible_for_recall`; el HTML no puede aprobar, borrar ni editar notas. Los criterios de recuperación siguen teniendo una única implementación compartida.

La lectura de una generación antigua del índice no basta para marcar el código como vigente. Sin `--refresh`, se muestra la fecha de verificación conocida y `not_revalidated` cuando corresponda. Cambios, errores o límites detectados durante exportación se muestran como parciales; nunca se mezclan dos generaciones de SQLite.

## 5. Límites, privacidad y escritura

- Reutilizar la política de exclusión del índice y las validaciones existentes de identidad, rutas y enlaces simbólicos. Evitar recorrer directorios excluidos antes de aplicar límites, no filtrarlos después de leerlos.
- Límite de entrada: 5.000 notas y 5.000 documentos, 1 MiB por documento y 100 MiB de lectura documental por exportación; las notas conservan sus límites actuales de validación. Mostrar recuentos y motivos de omisión.
- Máximo 50.000 nodos, 200.000 relaciones y 20 MiB UTF-8 de datos serializados. Renderizar hasta 500 nodos simultáneos y paginar la lista en bloques de 100. Un exceso genera una selección determinista con aviso parcial; no elimina registros originales ni aparenta contenerlos todos.
- Incluir el texto completo de las notas válidas dentro del presupuesto; extractos documentales de hasta 2.000 caracteres y firmas de código, sin duplicar archivos fuente enteros.
- Escapar los datos embebidos para que no puedan cerrar bloques de script. Mostrar texto no confiable con `textContent`; no ejecutar HTML/Markdown, URLs `javascript:`, eventos inline ni expresiones procedentes de notas, rutas o comentarios.
- Política CSP con hashes de los scripts/estilos propios, sin conexiones de red ni objetos externos en la exportación estática. El modo en vivo explícito solo permite conexiones al mismo origen local según el plan complementario. Ningún enlace del contenido provoca una descarga o abre una aplicación.
- Sin telemetría, llamadas SDK o extracción de memoria mediante modelo. El uso normal de tokens del asistente que invoca el slash command es independiente del exportador Python local.
- Escritura atómica del HTML mediante `aikya.storage.atomic_write`, huellas de los artefactos y bloqueo acotado del exportador. Verificar propiedad/esquema antes de reemplazar salidas; conservar archivos personalizados.
- Publicar un `report.md` completo solo después del HTML correspondiente y sus validaciones, con la huella del HTML. Si se interrumpe la exportación, la diferencia se detecta por esa huella y la próxima ejecución puede reconstruirla sin afirmar éxito previo. Usar el escritor documental compartido y actualizar el índice únicamente después de una escritura válida.
- No guardar rutas absolutas del equipo, prompts, transcripciones, tokens de acceso ni cadenas de error sin depurar en los artefactos. La inspección no recorre el almacén privado ni cambia el presupuesto `memory_budget_chars`.

## 6. Estructura e interfaces propuestas

```text
src/aikya/memory/viewer/
  __init__.py
  contracts.py       # Snapshot y límites
  collect.py         # Adaptación de las fuentes existentes
  graph.py           # Identidad, deduplicación y relaciones explícitas
  render.py          # HTML seguro y datos serializados
  export.py          # Publicación y cobertura
src/aikya/resources/memory-viewer/
  index.html.tmpl
  viewer.css
  viewer.js
src/aikya/resources/commands/aikya-memory/
  SKILL.md
```

- Ampliar `memory/knowledge.py` con `inspect_notes(root: Path, *, now: float, limit: int = 5000) -> NoteInspection`, reutilizando `_note()` y los criterios compartidos de identidad/revisión/vigencia. Definir `NoteInspection` en `src/aikya/memory/contracts.py`, fuera del visor: contiene `notes`, `omitted_count` y `diagnostics`; cada nota incluye los campos actuales más su estado calculado. El núcleo de memoria no importa módulos de presentación. No duplicar el esquema en el visor ni reutilizar el recorte de cinco resultados de `recall()` para un inventario.
- `ViewerOptions` contiene los límites de notas, documentos, bytes de entrada, nodos, relaciones, bytes serializados, extractos y nodos dibujados de la sección 5; los valores predeterminados son exactamente los allí indicados. Validar enteros positivos y aplicar los límites antes de materializar el conjunto completo.
- `collect_snapshot(root: Path, *, options: ViewerOptions, now: float) -> MemorySnapshot` consume esa inspección, documentos seguros y el lector transaccional del índice cuando esté disponible. No crea una caché ni cambia notas.
- `MemorySnapshot` contiene `schema_version`, `generated_at`, `index_generation`, `coverage`, `nodes`, `edges`, `counts` y `diagnostics`. `coverage` informa por fuente `available`, `missing`, `partial` o `invalid`; los identificadores llevan espacio de nombres `memory:`, `file:`, `symbol:` o `document:`.
- `MemoryNode` contiene `id`, `type`, `label`, `path`, `source_hash`, `status` y `details`; nunca requiere una ruta absoluta. `MemoryEdge` contiene `id`, `source`, `target`, `relation`, `provenance` y `evidence` con ruta/posición cuando exista.
- La ampliación estructural deriva el árbol de rutas/declaraciones ya indexadas y conserva identificadores cualificados. `SourceFlow` contiene `id`, `title`, `evidence_kind`, `steps`, `edges` y `limitations`. `evidence_kind` distingue `declared`, `syntax`, `resolved` y `observed`; solo un recorrido declarado o evidencia suficiente determina un orden. Los fixtures `illustrative` del ejemplo nunca entran automáticamente en un informe real.
- `render_html(snapshot: MemorySnapshot, *, language: str) -> str` usa únicamente el snapshot y los recursos propios del renderizador; no relee fuentes del proyecto ni hace llamadas externas. Comparte `encoded_snapshot()` con el colector para aplicar el presupuesto sobre los bytes UTF-8 del JSON final escapado para HTML.
- `export_view(root: Path, *, refresh: bool = False, open_browser: bool = False, dry_run: bool = False, language: str | None = None) -> ExportResult` coordina lectura, validación y escritura. `ExportResult` contiene `status`, `html_path`, `report_path`, `coverage` y `diagnostics`; CLI: 0 completo, 4 parcial útil, 2 bloqueado/error, sin apertura en caso bloqueado.

## 7. Tareas y aceptación

### Tarea V1: inventario compartido y grafo

**Archivos:** `memory/contracts.py`, `memory/knowledge.py`, `memory/viewer/contracts.py`, `collect.py`, `graph.py`; pruebas nuevas `tests/test_memory_viewer_collect.py` y `tests/test_memory_viewer_graph.py`.

- [ ] Escribir pruebas que fallen para notas aprobadas/pendientes/rechazadas, TTL, fuentes cambiadas/ausentes, identidad antigua, notas inválidas, ausencia de memoria e índice y más de 101 notas; inventariar sin alterar notas ni habilitar su recall.
- [ ] Probar enlaces explícitos válidos, duplicados, enlaces rotos, símbolos homónimos y ausencia de relaciones inventadas. Un documento enlazado fuera del proyecto no se lee.
- [ ] Implementar las interfaces compartidas de la sección 6, primero para notas/documentos; añadir el adaptador de índice cuando existan el almacén y el lector del plan base.
- [ ] Ejecutar `python -B -m unittest discover -s tests -p 'test_memory_viewer_collect.py' -v` y el patrón `test_memory_viewer_graph.py`; comprobar cero escrituras en las fuentes; guardar commit.

### Tarea V2: HTML navegable y seguro

**Archivos:** `memory/viewer/render.py`, recursos `memory-viewer/`; pruebas `tests/test_memory_viewer_html.py` y fixture `tests/fixtures/memory-viewer/hostile-notes.json`.

- [ ] Escribir pruebas que fallen con etiquetas `</script>`, `<!--`, comillas, Unicode, URLs ejecutables, nombres de archivo hostiles y datos que superen límites; no debe ejecutarse ningún contenido de las fuentes.
- [ ] Implementar búsqueda, filtros, selección, vecinos, grafo acotado, lista paginada, temas, idiomas y estados vacíos usando solo los datos exportados.
- [ ] Mantener Knowledge graph junto a arquitectura y recorridos: selección compartida, filtros por módulo/tipo, zoom, vecindad y contadores consistentes; ningún filtro añade relaciones ni altera las fuentes.
- [ ] Verificar en un navegador real que el archivo abre con `file://`, sin red, sin errores de consola y sin solicitudes externas; comprobar teclado, movimiento reducido, filtros y la consistencia entre grafo/lista/detalle.
- [ ] Comprobar los tiempos y límites de la tabla de animación; selección por teclado sin animación, interrupción de zoom, parada al ocultar la página y ausencia de movimiento continuo. La animación no cambia contadores ni estados de confianza.
- [ ] Ejecutar `python -B -m unittest discover -s tests -p 'test_memory_viewer_html.py' -v`; guardar evidencia de la revisión visual y commit. No considerar un snapshot HTML estático como prueba de interacción.

### Tarea V3: exportación y nuevo comando

**Archivos:** `memory/viewer/export.py`, `cli/main.py`, `cli/commands.py`, `middleware/commands.py`, skill `commands/aikya-memory/SKILL.md`, inventario `installation/assets.py`, incorporación `installation/infrastructure.py` y documentación README en/es; pruebas `tests/test_memory_viewer_export.py`, `tests/test_memory_viewer_command.py` y contratos de comandos existentes.

- [ ] Escribir pruebas que fallen para `--dry-run` sin cambios, conflicto con `--refresh`, caché desactivada, archivo personalizado, symlink, interrupción tras publicar HTML, índice documental personalizado y dos exportadores concurrentes.
- [ ] Implementar publicación recuperable, reporte con huella e índice exacto; preservar salidas personalizadas y todas las notas originales. `--open` solo después de una exportación útil y validada.
- [ ] Registrar un único `/aikya-memory`: pasar de 27 a 28 comandos sin renombrar ninguno, sin crear alias ni adaptadores raíz y sin ejecutar instaladores externos. Actualizar los contratos afectados en lugar de relajar sus comprobaciones.
- [ ] Integrar las fases existentes: Explore para fuentes, Plan para alcance, Implement para artefactos, Validate para comprobaciones y Security para inspección del exportador. Review solo con evidencia real cuando corresponda; si no, registrar skipped con motivo. Las fases locales no anuncian un modelo inexistente.
- [ ] Ejecutar `python -B -m unittest discover -s tests -p 'test_memory_viewer_*.py' -v` y `test_command_renames.py`; comprobar la CLI y la skill desde instalación global/project, runtimes copiados y wheel; guardar commit.

### Tarea V4: integración, rendimiento y cierre

**Archivos:** `tests/test_memory_viewer_distribution.py`, `tests/test_memory_viewer_adversarial.py`; controles CI existentes e informe `aikya/docs/validation/MEMORY_VIEWER.md` cuando haya resultados.

- [ ] Probar ODD/SDD, desarrollo/infraestructura/DevOps, en/es, Python 3.10–3.13 y Linux/macOS/Windows; un proyecto sin archivos fuente conserva una vista documental válida.
- [ ] Medir 100, 1.000 y 10.000 símbolos y los límites máximos: tiempo, tamaño del HTML y respuesta del navegador. Separar presupuesto de datos exportados del de nodos dibujados; ninguna omisión silenciosa.
- [ ] Verificar que la exportación estática no importa SDK, llama modelos, instala herramientas, inicia servicios ni accede a memorias privadas, incluso si hay otras herramientas presentes. Probar el proceso local explícito de `--watch --open` por separado según el plan de actualización automática.
- [ ] Ejecutar la batería completa, catálogo de 28 comandos, perfiles, contratos de instalación, presupuesto de contexto y controles de documentación. Registrar resultados observados y actualizar changelog, README en/es e índice.

### Tarea V5: estructura navegable y recorridos con evidencia

**Archivos propuestos:** `memory/viewer/structure.py`, `memory/viewer/flows.py`, adaptadores del colector y recursos de interfaz; `code_index/contracts.py` y el analizador Java de la etapa B cuando corresponda. Pruebas nuevas `tests/test_memory_viewer_structure.py`, `tests/test_memory_viewer_flows.py` y fixtures `tests/fixtures/memory-viewer/java/`.

- [ ] Escribir pruebas para módulos Maven anidados, source sets, scopes, propiedades sin resolver, XML hostil, clases homónimas y métodos sobrecargados; sin ejecutar herramientas del proyecto ni descargar dependencias.
- [ ] Implementar jerarquía y dependencias documentadas sobre el índice existente, expansión bajo demanda, búsqueda global acotada y selección compartida. Mostrar discrepancias entre ruta y paquete.
- [ ] Probar entradas Spring literales/no resueltas e interfaces con varias implementaciones. Proxies y llamadas dinámicas no producen un destino ni una traza inventados.
- [ ] Implementar `SourceFlow` y navegación; conservar la procedencia de recorridos declarados. Las relaciones sintácticas sin resolución no adquieren un orden artificial.
- [ ] Probar grafo–árbol–detalle–test con teclado, movimiento reducido y ramas de 1.000/10.000 clases. Referenciar un test no cambia su resultado.
- [ ] Verificar que Knowledge graph conserva todas las vistas Java, funciona sin dependencias de visualización remotas y aplica los límites de snapshot al aislar vecinos o cambiar filtros.
- [ ] Ejecutar los patrones `test_memory_viewer_structure.py` y `test_memory_viewer_flows.py`; registrar cobertura y limitaciones antes de anunciar la capacidad.

## 8. Orden y esfuerzo adicional

El visor de notas/documentos se diseñó para poder construirse antes del índice y adaptar después su lector transaccional. La propuesta inicial se preparó en `feat/local-code-index`; la implementación aceptada usa `feat/automatic-local-memory`, creada desde `origin/develop` después de la fusión de la PR #19.

Estimación orientativa adicional: 3–5 jornadas para V1–V3 y 1–2 para V4 y las correcciones observadas. No incluye un servicio de memoria de pago ni una predicción de consumo del asistente. No cambia la estimación del índice base y no implica soporte semántico universal desde la primera entrega.

La ampliación V5 reserva **8–16 h** para árbol/estructura y dependencias declaradas, y **16–32 h** para recorridos Java con procedencia y sus pruebas, una vez disponible el analizador Java de la etapa B. No vuelve a presupuestar ese analizador ni incluye resolución universal Spring/LSP o instrumentación de producción. Revisar el esfuerzo cuando exista el repositorio Java real y se conozcan su build y sus patrones dinámicos.

El plan base y la ampliación fueron aceptados. La implementación registra `/aikya-memory`; las vistas previas históricas conservan su condición de ejemplos. Las pruebas, los límites y el alcance entregado se describen en el informe de implementación.

La petición posterior de actualizar memoria/HTML tras cada cambio añade las tareas A1–A3 del [plan de actualización automática](2026-10-25-memory-actualizacion-automatica.es.md): observación, publicación incremental y refresco en vivo sin modelos. Reserva **24–40 h adicionales**, sin duplicar las tareas del índice o del exportador. Los cambios en notas originales conservan las reglas de revisión existentes.

GENERATED BY AIKYA HARNESS
