# Plan de ampliación: memoria y HTML con actualización automática local

**Estado:** implementación realizada en `feat/automatic-local-memory`, creada desde `origin/develop` actualizado el 2026-10-25. El índice, observador, exportador y cliente en vivo están implementados en el paquete; los resultados locales y las comprobaciones remotas pendientes se registran en el [informe de implementación](../validation/LOCAL_MEMORY_IMPLEMENTATION.md). Las vistas previas anteriores siguen siendo ejemplos; el [HTML generado](../examples/aikya-memory-generated.html) usa ahora el exportador real sobre una fixture identificada.

**Objetivo:** al guardar código o crear, renombrar o eliminar una clase, actualizar la memoria derivada del código y el informe HTML automáticamente, sin invocar modelos ni consumir tokens para ese mantenimiento.

**Arquitectura:** un observador local por proyecto/worktree alimenta el sincronizador incremental del [plan base](2026-10-25-indice-local-codigo.es.md) y reutiliza el colector/exportador del [visor](2026-10-25-aikya-memory-html.es.md). No añade otra base de memoria, analizador ni servidor de lenguaje. Un modo de visualización en vivo permite actualizar también la página abierta.

**Tecnologías:** Python 3.10–3.13, biblioteca estándar, los analizadores aprobados del índice y HTML/CSS/JavaScript propios. La primera entrega usa sondeo acotado; los eventos nativos son una optimización posterior.

**Requisito de origen:** actualización automática después de cualquier cambio elegible dentro del proyecto, incluidos editores externos, herramientas de IA y cambios de Git. Se mantienen las exclusiones, identidades y límites de los planes relacionados.

## 1. Qué se actualiza sin tokens

| Elemento | Actualización local prevista |
|---|---|
| Código nuevo o modificado | Huella, clases, funciones, firmas, posiciones e importaciones mediante el analizador disponible |
| Código eliminado o renombrado | Retirar registros anteriores y reconstruir las relaciones afectadas |
| Grafo, árbol e inventario | Recalcular desde una generación coherente del índice, sin deducir relaciones mediante IA |
| Notas existentes vinculadas a fuentes | Recalcular vigencia, caducidad y elegibilidad; una fuente cambiada se muestra como desactualizada |
| Documentos y notas editados por el usuario | Validar y proyectar su contenido actual dentro del alcance autorizado |
| HTML y reporte | Regenerar los artefactos derivados y su cobertura después de un cambio relevante |

El proceso no escribe explicaciones semánticas, decisiones ni aprobaciones de notas por su cuenta. Una clase creada durante la ejecución del programa, sin declaración analizable en archivos, no se detecta mediante este mecanismo. Sin analizador compatible se actualiza el inventario del archivo y se mantiene `file_only`, sin inventar clases.

El mantenimiento no importa SDK de proveedores, usa embeddings ni envía contenido a modelos. Consume CPU, memoria y disco del equipo. Las consultas o ediciones posteriores que haga la IA mantienen su consumo habitual de tokens. Invocar un slash command mediante un asistente puede consumir tokens del propio asistente: el proceso Python persistente realiza las actualizaciones sucesivas sin volver a convocarlo.

## 2. Activación y duración

- La incorporación aprobada mediante `/aikya-init` o `/aikya-analyze` registra la política local de actualización automática y exportación. Un proyecto vacío no recibe notas ni clases ficticias.
- La política amplía `.aikya/code-index.json` con campos `watch` y `auto_export`, separados de `enabled` para el índice. Si el índice está deshabilitado, el visor puede actualizar notas/documentos sin habilitarlo. Se reutiliza un único archivo de política.
- En una sesión de trabajo de Aikya, iniciar un único observador cuando el runtime instalado ofrezca un punto de entrada de sesión compatible. Detenerlo al finalizar y publicar su estado real; no anunciar esta integración en un runtime sin verificarla.
- Proponer `/aikya-memory --watch --open`, equivalente a `python -m aikya memory --target <project> --watch --open`, como proceso explícito para mantener la observación durante el trabajo con cualquier editor. `--watch` sin `--open` actualiza archivos sin iniciar un servidor ni abrir navegador. Interrumpir el proceso lo detiene.
- `--watch --open` mantiene la observación y abre la vista en vivo local descrita en la sección 4. Reutilizar `/aikya-memory`; no crear otro slash command.
- Los clientes explícitos reutilizan el observador existente mediante una concesión de sesión propia: cerrar un visor no detiene otras sesiones. El proceso deja de observar al terminar la última concesión; los clientes explícitos la renuevan cada 30 segundos. Las concesiones abandonadas caducan tras seis horas sin eventos.
- No instalar servicios del sistema, tareas programadas ni procesos al iniciar el equipo. Si Aikya y el observador están detenidos, los cambios se reconcilian al volver a iniciar: no existe actualización mientras ningún proceso está ejecutándose.
- `--dry-run` sigue sin escrituras, sockets ni procesos y es incompatible con `--watch` y `--refresh`. La observación respeta la política existente; no amplía rutas ni autoriza un índice deshabilitado.

## 3. Ciclo incremental y consistencia

```text
Guardar archivo / crear clase / cambiar rama
  -> detectar candidatos y agrupar cambios
  -> verificar contenido y alcance
  -> analizar únicamente archivos cambiados
  -> confirmar generación del índice
  -> recalcular vista y vigencia de notas
  -> publicar HTML y reporte coherentes
  -> refrescar la página si está en modo en vivo
```

1. Sondeo inicial cada 2 segundos sobre rutas elegibles, filtrando exclusiones antes de recorrer directorios. Metadatos seleccionan candidatos; las huellas deciden si cambió el contenido. Hooks de escritura correcta marcan pendientes y despiertan el mismo coordinador, sin reconstruir el proyecto dentro del hook.
2. Agrupar cambios durante 750 ms, con espera máxima de 3 segundos desde el primer evento. Esos tiempos son valores de planificación, no una garantía de latencia: lectura, análisis y exportación se miden por separado y dependen del tamaño del proyecto.
3. Realizar reconciliación de contenido completa al arrancar, al solicitar `--refresh` y cada 60 segundos mientras se observa. Antes de entregar contexto, verificar además las huellas de los archivos seleccionados sin imponer un escaneo completo por consulta. Detectar también contenido cambiado con fecha/tamaño conservados. Aplicar límites por lote y continuar el trabajo pendiente sin bloquear el editor ni declarar cobertura completa antes de tiempo.
4. Reutilizar `sync()` y el bloqueo de escritor del índice. Guardados atómicos, renombrados y ráfagas se agrupan; un error de sintaxis invalida los símbolos antiguos del archivo. Un segundo observador del mismo worktree se rechaza con estado comprensible; otros worktrees permanecen independientes.
5. Proyectar solo una generación confirmada. Verificar las huellas de las fuentes incluidas; si cambian durante la colección, reintentar de forma acotada o mostrar cobertura parcial. Publicar HTML y después reporte con la misma generación y huella, mediante el exportador recuperable existente en el plan.
6. Excluir `aikya/docs/memory/view/**` de observación y colección. Tratar `aikya/docs/indice.md` como catálogo de rutas, sin crear un nodo de contenido ni usar sus cambios como disparador: sus documentos se detectan directamente. Así las propias publicaciones y la actualización del índice documental no producen un ciclo.
7. No reescribir HTML/reporte si la proyección relevante no cambia. Si caduca una nota, programar la siguiente comprobación de vigencia aunque no haya ediciones; no modificar su cuerpo ni revisión. Mantener la última publicación coherente ante fallos y mostrar su fecha, error y pendientes.
8. Una desconexión o pérdida del estado pendiente obliga a reconciliar al reiniciar. No se presupone que los hooks capturen cambios hechos por Git, shell u otro editor.

Los límites heredados son 12.000 archivos elegibles, 1 MiB por archivo de código y 100 MiB por lote de sincronización; el visor conserva sus propios límites. Registrar tiempos, bytes, omisiones y generaciones localmente, sin transcripciones ni secretos. El objetivo inicial de pruebas es una actualización útil en menos de 5 segundos tras quedar estable un cambio pequeño en el fixture medido; documentar el equipo, tamaño y resultado antes de prometer rendimiento.

## 4. HTML exportable y vista en vivo

**Archivo exportado:** `aikya/docs/memory/view/index.html` sigue siendo autocontenido y abre con `file://`, sin conexiones de red. El observador regenera el archivo; una pestaña que ya lo cargó conserva su instantánea hasta recargarla. No presentar ese archivo como si estuviera observando el disco.

**Vista en vivo:** solo con `--watch --open`, un servidor efímero del propio paquete sirve la interfaz en `127.0.0.1`, con puerto asignado por el sistema. La página consulta cada 2 segundos una generación disponible y obtiene un snapshot acotado cuando cambia. No requiere internet, CDN, instalación de servidor externo ni modelo. Al cerrar el proceso termina también el servidor.

Reutilizar renderizado, datos y límites del visor. Conservar selección, filtros, zoom y ramas abiertas al recibir datos; si desaparece el nodo seleccionado, indicar su eliminación. Mostrar `Watching`, `Updating`, `Up to date`, `Partial` o `Disconnected` según evidencia real, junto con generación y hora de verificación. `Up to date` significa consistente con la última verificación terminada, no conocimiento instantáneo de todo el disco. Pausar las consultas con la pestaña oculta y reconciliar al volver.

El servidor solo expone interfaz, generación y snapshot del proyecto autorizado: sin listado de archivos arbitrarios, escrituras ni ejecución de comandos. Validar Host/origen y una capacidad aleatoria por sesión que no se guarda en el HTML ni en reportes; no habilitar acceso LAN ni CORS abierto. Mantener CSP con conexiones limitadas al mismo origen en modo en vivo y `connect-src 'none'` en la exportación estática. Un error del observador no se representa como una actualización exitosa.

## 5. Archivos e interfaces

| Archivo propuesto | Responsabilidad |
|---|---|
| `src/aikya/code_index/watch.py` | Candidatos, agrupación y reconciliación, reutilizando política, huellas, pendientes y sincronizador |
| `src/aikya/memory/viewer/watch.py` | Coordinación de vigencia y exportaciones por generación; ciclo de vida del proceso |
| `src/aikya/memory/viewer/live.py` | Servidor de lectura local explícito y snapshot publicado |
| `src/aikya/memory/viewer/client.py` | Clientes explícitos que comparten el observador y mantienen su propia concesión |
| `src/aikya/memory/viewer/contracts.py` | `WatchOptions`, `WatchStatus` y estado de publicación |
| `src/aikya/cli/main.py` y recursos del comando | Opciones `--watch`, incompatibilidades y salida al interrumpir |
| `src/aikya/middleware/configuration.py` e instalación | Integración de sesión/hooks donde el runtime la soporte, sin duplicar hooks personalizados |
| `src/aikya/resources/memory-viewer/viewer.js` | Refresco en vivo, conservación de navegación y estados de conexión |

`WatchOptions` define `poll_interval_ms=2000`, `debounce_ms=750`, `max_batch_wait_ms=3000`, `reconcile_interval_s=60` y `live=False`, con validación y límites de las políticas heredadas. `WatchStatus` contiene `state`, `index_generation`, `published_generation`, `pending_count`, `last_verified_at`, `coverage` y `diagnostics`. `published_generation` identifica por huella la proyección publicada e incorpora revisión del esquema, idioma, configuración y vigencia: cambia también al variar documentos/notas, aunque `index_generation` sea igual. No incluir la hora de cada sondeo en esa huella, para evitar reexportaciones sin cambios.

`watch_project(root: Path, *, options: WatchOptions, stop_event: threading.Event) -> None` coordina el ciclo y su cierre. `publish_if_changed(root: Path, *, now: float) -> ExportResult | None` reutiliza colección/exportación y devuelve `None` si no cambia la proyección. `serve_live(root: Path, *, stop_event: threading.Event) -> LiveEndpoint` produce dirección local y capacidad temporal; nunca se invoca en exportación estática ni dry-run. Definir `LiveEndpoint` en los contratos del visor. Ninguno de estos módulos depende de un SDK de modelos.

## 6. Tareas y aceptación

### Tarea A1: observación y actualización del índice

**Pruebas:** `tests/test_code_index_watch.py`, `tests/test_code_index_integration.py`.

- [ ] Escribir y ejecutar pruebas inicialmente fallidas para creación/edición/borrado/renombrado, guardado atómico, cambios Git, fecha/tamaño iguales, ráfagas, dos procesos y worktrees distintos.
- [ ] Implementar observador, límites, agrupación y reconciliación sobre `sync()`, con reloj y señal de parada sustituibles en pruebas. Una segunda verificación sin cambios ejecuta cero analizadores; editar un archivo ejecuta únicamente su analizador.
- [ ] Ejecutar los dos patrones con `python -B -m unittest discover -s tests -p '<patrón>' -v`; verificar cierre, reinicio, exclusiones y permisos en Linux/macOS/Windows. Guardar commit de la tarea cuando pasen.

### Tarea A2: publicación automática y notas vigentes

**Pruebas:** `tests/test_memory_viewer_watch.py`, `tests/test_memory_viewer_export.py`.

- [ ] Escribir y ejecutar pruebas inicialmente fallidas para una clase nueva visible en HTML, fuente cambiada con nota desactualizada, vencimiento sin ediciones, cambio durante colección, reporte interrumpido, salidas personalizadas y ausencia de bucle de autoexportación.
- [ ] Implementar coordinación y publicación sin tocar notas/revisión ni duplicar el almacén. Varias observaciones sin cambios no escriben artefactos. Reporte, HTML y estado publicado coinciden por generación y huella.
- [ ] Ejecutar los dos patrones con `python -B -m unittest discover -s tests -p '<patrón>' -v`; comprobar que no se importan proveedores ni se realizan conexiones externas. Guardar commit con resultados observados.

### Tarea A3: vista en vivo y distribución

**Pruebas:** `tests/test_memory_viewer_live.py`, `tests/test_memory_viewer_distribution.py` y comprobaciones de navegador sobre el servidor local.

- [ ] Escribir y ejecutar pruebas inicialmente fallidas para accesos sin capacidad, Host/origen ajenos, rutas no autorizadas, incompatibilidades CLI, cierre y cero sockets en modo estático/dry-run.
- [ ] Implementar servidor y refresco por generación conservando navegación; mostrar desconexión y cobertura parcial sin simular éxito. No reiniciar la animación del grafo completo después de cada guardado.
- [ ] Verificar en navegador una edición real del fixture: clase nueva aparece sin recargar manualmente; desaparece al borrarla; filtros/zoom se conservan y movimiento reducido se respeta. Comprobar exportación `file://` sin conexiones y modo en vivo sin tráfico externo.
- [ ] Ejecutar los patrones anteriores y los contratos CLI/instalación en la matriz existente. Medir latencia, lecturas y exportaciones, registrar evidencia en `aikya/docs/validation/MEMORY_AUTO_UPDATE.md` y actualizar README en/es, changelog e índice cuando esté implementado. Guardar commit de la tarea.

## 7. Orden y esfuerzo adicional

Depende de las tareas 1–4 del índice y V1–V3 del visor; no vuelve a presupuestarlas. A1–A2: **12–20 h**; A3 y aceptación integrada: **12–20 h**. Total adicional orientativo: **24–40 h**, sujeto al runtime y las mediciones multiplataforma. No incluye servicios del sistema, resolución semántica universal ni instrumentación de aplicaciones.

La operación local no añade una tarifa de API o tokens. El trabajo de implementación y pruebas tiene esfuerzo propio, y el equipo consume recursos mientras observa. Esta ampliación sustituye la limitación anterior de actualizar solo al ejecutar comandos. En esta rama, la incorporación aprobada instala la política y los hooks; un proyecto todavía no configurado no activa observadores automáticamente.

## 8. Registro de implementación

Las tareas A1–A3 están implementadas. Las pruebas se consolidaron en `test_code_index.py`, `test_code_index_languages.py`, `test_memory_watch.py`, `test_memory_viewer.py`, `test_memory_live.py` y `test_memory_integration.py`, en lugar de duplicar archivos por cada interfaz del diseño. La batería ejecutable de los 28 comandos y el smoke test del wheel incluyen el visor.

El [informe](../validation/LOCAL_MEMORY_IMPLEMENTATION.md) es la fuente de resultados observados: no convertir la matriz de CI preparada ni una fixture en una prueba de Claude Code autenticado o de otra plataforma. Los checkboxes originales conservan el detalle del plan; no son una lista de funcionalidades ausentes que deban implementarse de nuevo.

GENERATED BY AIKYA HARNESS
