# Plan de corrección de Memory: inventario, distribución y animación

**Estado:** implementado y validado localmente el 29 de octubre de 2026 en `feat/memory-interactive-graphs` (v7.1.1).
El HTML del proyecto privado no se modifica; las pruebas utilizan fixtures sintéticas.
**Fecha:** 28 de octubre de 2026.
**Objetivo:** separar correctamente Inventario de las vistas gráficas, evitar
la acumulación de nodos y etiquetas y facilitar la exploración con movimiento
controlable en Grafo de conocimiento y Arquitectura, incluyendo arrastre
individual de nodos y animación de sus conexiones.
**Arquitectura:** mantener el visor local SVG existente; corregir visibilidad,
distribución, navegación y transiciones sin cambiar el modelo de memoria ni
la publicación verificada de HTML/reporte.
**Tecnologías:** JavaScript, SVG, CSS, Python/unittest y la prueba de navegador
existente con Playwright como herramienta de desarrollo.
**Especificación:** captura aportada por el usuario, con Inventario seleccionado,
275 nodos, paginación 1/3 y el grafo dibujado encima de las filas.
Segunda captura: Arquitectura con carpetas y archivos amontonados en columnas,
etiquetas superpuestas y mucho espacio lateral sin aprovechar.
Ampliación solicitada: poder mover los objetos y animar también las líneas que
conectan componentes en las dos vistas gráficas.
**Ejecución:** secuencial, desde `origin/develop` actualizado, base `177f032`.

## 1. Diagnóstico y alcance confirmado

- `index.html.tmpl` define `#graph` como `<svg>` y `#inventory` como `<div>`.
- `viewer.js`, en `render()`, asigna `$('graph').hidden = view === 'inventory'`.
  La propiedad reflejada `hidden` está definida en `HTMLElement`; no debe
  suponerse ese comportamiento sobre un `SVGElement`.
- El CSS ya contiene `[hidden] { display: none !important; }`. La hipótesis
  principal es que la asignación al SVG no establece el atributo que esa regla
  necesita; el grafo conserva su posición absoluta encima del inventario.
- El HTML generado en `jourpass_app` contiene las mismas instrucciones. No es
  suficiente añadir otra regla CSS o elevar las filas con `z-index`.
- La aceptación actual sólo comprueba que existen `.inventory-row`; no comprueba
  que el grafo se oculte ni que las filas reciban los clics.

La reproducción sintética confirmó que el SVG interceptaba los clics de las filas.
La aceptación posterior verifica ocultación calculada, clics reales y navegación
por teclado. La URL privada `file://` fue rechazada por el navegador de inspección;
no se eludió esa restricción ni se modificó el HTML privado.

Referencias de API: [HTMLElement.hidden](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/hidden),
[SVGElement](https://developer.mozilla.org/en-US/docs/Web/API/SVGElement) y
[Element.toggleAttribute](https://developer.mozilla.org/en-US/docs/Web/API/Element/toggleAttribute).

### Acumulación y movimiento: hechos del código

- `hierarchy()` agrupa por profundidad de ruta y reparte todos los miembros de
  cada nivel entre 45 y 605 unidades verticales. No reserva espacio para el
  tamaño de los subárboles ni para sus etiquetas. Más archivos implican menor
  separación dentro de la misma altura.
- La distribución del grafo también limita las posiciones a un rectángulo fijo.
  Calcula repulsión entre puntos y atracción entre enlaces, pero no colisiones
  de cajas de texto. Las carpetas mantienen sus etiquetas visibles incluso
  cuando hay muchos nodos.
- El visor usa un espacio SVG de 1000 × 650 y zoom entre 0,5 y 3, sin navegación
  por arrastre ni ajuste a los límites reales del contenido.
- El caché de posiciones considera los identificadores de nodos, pero no los
  cambios de relaciones con esos mismos identificadores.
- `graph()` recrea sus elementos mediante `replaceChildren()` en cada render.
  Esto dificulta conservar foco, posiciones y transiciones entre estados.
- El botón de movimiento ya existe. Actualmente controla principalmente las
  transiciones de opacidad y zoom; el cálculo de posiciones termina antes de
  dibujar los nodos. No hay una simulación animada continua del grafo.

Estos hechos explican la falta de separación que muestra la segunda captura.
La aceptación visual se realizó con escenarios sintéticos de 275, 1001 nodos y
un árbol de 180 niveles. Las capturas y las mediciones están en el informe de
validación. No se abrió ni modificó el HTML privado para reproducirla.

## 2. Restricciones y puntos de revisión

- Conservar el tema, los datos, filtros,
  buscador, paginación, selección e inspector.
- Mantener una única vista visible y operable en el escenario, también tras
  búsquedas vacías, cambios repetidos de pestaña y actualizaciones en vivo.
- No ocultar el problema con `z-index`, transparencias o borrado del grafo.
  Conservar su estado para volver a las vistas gráficas.
- Mantener CSP, hashes de recursos y controles de propiedad. Regenerar mediante
  el exportador; no parchear manualmente HTML ya publicado.
- Conservar índice, notas, documentos y caché. La captura no acredita corrupción
  ni justifica borrarlos o reconstruir toda la memoria.
- Utilizar únicamente nodos, rutas y relaciones presentes en el snapshot. Un
  grupo visual de carpeta no representa una nueva dependencia ni un recorrido
  de ejecución. Mantener esa distinción en la leyenda y el inspector.
- Mostrar menos detalle inicialmente mediante expansión progresiva; mantener
  todos los elementos accesibles por búsqueda, inspector e Inventario. Indicar
  cuántos están visibles, agrupados o fuera del límite de representación.
- Reutilizar el control de movimiento, los idiomas y los tokens CSS existentes.
  Todo el cálculo será local, sin llamadas a modelos ni consumo de tokens; sí
  utiliza recursos del navegador y debe quedar acotado.

## 3. Archivos previstos

| Archivo | Responsabilidad |
|---|---|
| `src/aikya/resources/memory-viewer/viewer.js` | Visibilidad, distribución, expansión, cámara, arrastre de nodos y actualización de conexiones. |
| `src/aikya/resources/memory-viewer/layout.js` (nuevo) | Árbol, proyección progresiva y distribución acotada con separación. |
| `src/aikya/resources/memory-viewer/camera.js` (nuevo) | Encuadre, zoom, navegación, arrastre y cancelación de gestos. |
| `src/aikya/resources/memory-viewer/labels.js` (nuevo) | Medición y colocación de etiquetas sin superposición. |
| `src/aikya/resources/memory-viewer/graph.js` (nuevo) | Estado por vista, elementos SVG estables, expansión y conexiones. |
| `src/aikya/memory/viewer/render.py` | Integrar los módulos en un único script offline y calcular su CSP/fingerprint. |
| `src/aikya/resources/memory-viewer/viewer.css` | Etiquetas legibles, estados de interacción, transiciones y flujo animado de conexiones. |
| `src/aikya/resources/memory-viewer/index.html.tmpl` | Controles accesibles de ajustar vista y expansión, con traducción en/es. |
| `scripts/ci/memory_viewer_browser.cjs` | Exclusión visual, clics, paginación, separación, navegación y movimiento. |
| `scripts/ci/memory_interactions_browser.cjs` (nuevo) | Arrastre, teclado, posiciones, flujo y exclusión de Inventario. |
| `scripts/ci/memory_density_browser.cjs` (nuevo) | Escenarios densos/profundos, interrupciones y publicaciones en vivo. |
| `tests/memory_layout.test.cjs` (nuevo) | Comportamiento puro de distribución, agrupación, ciclos y posiciones manuales. |
| `tests/memory_viewer_fixture.py` (nuevo) | Generar escenarios sintéticos con 275 nodos y variantes densas y profundas, sin datos privados. |
| `tests/test_memory_viewer.py` | Verificar regeneración por cambio de recursos sin cambios en los datos. |
| `scripts/ci/run_isolated_tests.py` (nuevo) | Aislar la configuración personal en un proceso de pruebas hijo. |
| `.github/workflows/tests.yml` | Añadir aceptación del visor con fixture sintética y Chromium en CI. |
| `CHANGELOG.md`, `VERSION` | Preparar el siguiente parche disponible tras confirmar las versiones existentes. |
| `aikya/docs/validation/2026-10-29-memory-interactive-graphs.md` | Documentar resultados observados y capturas de aceptación. |
| `aikya/docs/indice.md` | Registrar este plan y posteriormente el informe. |

## 4. Tarea de corrección y regresión

**Interfaz conservada:** `render()` sigue usando `view`, los filtros y `page`;
no cambia el esquema de `MemorySnapshot` ni el contrato de `render_html()`.

- [x] Crear `feat/memory-interactive-graphs` desde `origin/develop` actualizado,
  sin modificar cambios locales o instalaciones del usuario.
- [x] Crear la fixture mediante `write_fixture(output: Path, language: str) -> None`
  en `tests/memory_viewer_fixture.py`: 275 nodos sintéticos con relaciones de
  pertenencia verificables, exportables en inglés y español con `render_html()`.
- [x] Añadir a la aceptación de navegador la secuencia Grafo → Arquitectura →
  Inventario. En Inventario, esperar `#graph` no visible y `display: none`,
  `#inventory` visible y 100 filas en la primera página. Comprobar atributos como
  apoyo al diagnóstico, no como sustituto de la visibilidad calculada.
- [x] Comprobar un clic real sobre una fila y que el inspector muestre su ruta;
  ningún nodo del grafo oculto debe interceptar clics o recibir foco al tabular.
- [x] Ejecutar la prueba antes del cambio y conservar el fallo que reproduce la
  superposición. Ajustar las comprobaciones de etiquetas existentes al idioma de
  la fixture para que un texto inglés fijo no produzca un fallo ajeno al bug.
- [x] Sustituir la asignación de propiedad del SVG por una operación de atributo
  compatible, como `toggleAttribute('hidden', view === 'inventory')`, utilizando
  la regla CSS existente. Aplicar cambios adicionales sólo si la reproducción
  los requiere; no introducir un segundo sistema de vistas.
- [x] Verificar el retorno Inventario → Grafo → Arquitectura: SVG visible,
  inventario y paginación ocultos, selección e inspector coherentes.
- [x] Validar las páginas 100/100/75, botones anterior/siguiente, búsqueda sin
  resultados, filtros y selección. Tras cambiar un filtro, la página debe seguir
  siendo válida y el grafo debe continuar oculto en Inventario.
- [x] Repetir alternancia y clics con temas claro/oscuro, movimiento desactivado,
  idioma en/es y anchos 1560, 1024, 768 y 390; conservar ausencia de desbordamiento
  horizontal. Una captura correcta por sí sola no sustituye estas comprobaciones.
- [x] Añadir la comprobación de cambio de recursos al exportador: con el mismo
  snapshot, un nuevo recurso genera otra proyección y un par HTML/reporte con
  hashes concordantes; una segunda exportación idéntica no reescribe archivos.
- [x] Añadir un job de CI con Python, Node y Playwright/Chromium como dependencias
  de desarrollo. Generar fixtures locales sintéticas y ejecutar la aceptación
  para ambos idiomas; registrar errores de JavaScript/CSP y exigir cero peticiones
  externas desde el HTML offline. No subir el HTML privado de `jourpass_app`.
- [x] Ejecutar las pruebas de exportación, observación, servidor local e integración
  con `python -B -m unittest discover -s tests -p 'test_memory_*.py' -v`; antes de
  cerrar la PR, ejecutar también la regresión completa y comprobar el wheel.
- [x] Registrar evidencias reales, actualizar changelog/versión e índice y preparar
  la descripción de PR contra `develop` en el informe. No se ha enviado la rama
  ni creado una PR remota; la publicación seguirá el proceso de revisión existente.

## 5. Distribución legible y navegación

**Contratos internos implementados:** las funciones de distribución recibirán los
nodos y relaciones visibles y devolverán posiciones por identificador y límites
del contenido. Mantener independientes la distribución, la cámara y la selección.
No añadir una segunda fuente de datos ni una dependencia remota de gráficos.

### Arquitectura

- [x] Añadir primero una fixture de árbol ancho y otra de árbol profundo que
  evidencien la acumulación actual. Medir posiciones y cajas de etiquetas en el
  navegador, además de guardar capturas sintéticas.
- [x] Sustituir el reparto por profundidad por una distribución de árbol que
  reserve altura por subárbol y sitúe cada padre respecto a sus hijos. Usar las
  relaciones de pertenencia disponibles; ante relaciones ausentes, mostrar el
  nodo como raíz independiente, sin inventar enlaces.
- [x] Reservar separación entre nodos y espacio horizontal para etiquetas
  acotadas. El mundo del diagrama debe crecer con el contenido: no comprimir
  todos los miembros de un nivel dentro de 560 unidades verticales.
- [x] Mostrar inicialmente proyecto y carpetas principales. Permitir expandir
  carpetas para ver subcarpetas y archivos; mostrar el número de elementos
  contenidos calculado desde los datos reales. La búsqueda abrirá la ruta del
  resultado seleccionado para que no permanezca escondido.
- [x] Conservar el estado de expansión al cambiar de pestaña o recibir una
  generación nueva; retirar únicamente identificadores que ya no existan.
  No mezclar por accidente este estado con los desplegables del árbol lateral.

### Grafo de conocimiento

- [x] Presentar un resumen por carpetas reales y permitir explorar archivos y
  declaraciones progresivamente. Los grupos son controles visuales; dibujar
  únicamente relaciones existentes entre los elementos representados. No
  presentar conexiones agregadas como dependencias verificadas.
- [x] Añadir separación por radio de nodo y margen de seguridad a la distribución.
  Reservar espacio para las etiquetas prioritarias y resolver sus colisiones.
  Mantener posiciones estables de elementos que no cambian cuando sea posible.
- [x] Mostrar etiquetas según el espacio y el nivel de detalle: priorizar carpetas,
  selección y foco; mostrar el nombre completo y la ruta en el inspector y en
  una ayuda accesible. Truncar nombres extensos visualmente sin alterar el dato.
  Buscar no debe activar todas las etiquetas simultáneamente sin comprobar espacio.
- [x] Invalidar o actualizar la distribución cuando cambien relaciones, nodos o
  parámetros relevantes. Añadir un caso con los mismos nodos y enlaces distintos
  para detectar el problema del caché actual.
- [x] Mantener un presupuesto explícito para nodos y enlaces dibujados. El límite
  actual de 500 nodos no debe silenciar resultados: mostrar los recuentos reales
  y permitir localizar los restantes mediante filtros e Inventario. Acotar también
  el cálculo de fuerzas y la cantidad de enlaces representados.

### Cámara e interacción en ambas vistas

- [x] Añadir arrastre del fondo, zoom centrado en el punto de interacción y
  «Ajustar vista / Fit view». Conservar controles operables por teclado; separar
  un clic de selección de un arrastre para evitar selecciones involuntarias.
- [x] Calcular el encuadre con los límites del contenido y el tamaño disponible.
  Reaccionar al cambio de tamaño del panel sin recalcular continuamente ni
  comprimir etiquetas hasta hacerlas ilegibles; usar el resumen por carpetas
  cuando el proyecto completo no quepa con detalle.
- [x] Conservar una cámara por vista. Seleccionar un nodo no debe restablecer el
  zoom; una actualización en vivo tampoco debe devolver al usuario al origen.
  Ajustar el encuadre al abrir por primera vez o por acción explícita.
- [x] Mantener selección, foco e inspector coherentes al expandir, contraer y
  filtrar; si se oculta el nodo enfocado al contraer, devolver el foco a su carpeta.
  Proporcionar áreas de interacción mayores que los círculos pequeños actuales.

### Mover objetos individualmente

- [x] Permitir arrastrar carpetas, archivos y declaraciones representados como
  nodos en Grafo y Arquitectura. Arrastrar el fondo mueve la cámara; arrastrar un
  nodo mueve ese objeto, sin cambiar rutas, relaciones ni archivos del proyecto.
  Mover una carpeta no mueve automáticamente todo su subárbol.
- [x] Convertir las coordenadas del puntero al espacio SVG teniendo en cuenta
  zoom y desplazamiento. Usar captura del puntero y un umbral de 5 píxeles de
  pantalla para distinguir clic de arrastre; mantener el mismo nodo bajo el
  puntero sin saltos al iniciar el gesto.
- [x] Actualizar durante el arrastre las conexiones incidentes y las etiquetas,
  como máximo una vez por fotograma. No recalcular la distribución completa ni
  activar una simulación física permanente. El resto de los nodos conserva su
  posición; al soltar, ajustar la visibilidad de etiquetas que se superpongan.
- [x] Conservar las posiciones manuales por identificador y por vista durante
  la sesión del visor, incluidos cambios de filtro, pestaña y generación. La
  distribución automática debe respetarlas; retirar las de nodos eliminados.
  No escribir estos ajustes visuales en el índice de memoria ni en el HTML firmado.
  La recarga completa vuelve a la distribución inicial en esta primera versión.
- [x] Añadir «Restablecer distribución / Reset layout» para liberar posiciones
  manuales de la vista actual. «Ajustar vista» sólo modifica el encuadre, sin
  deshacer el trabajo de organización del usuario.
- [x] Ofrecer movimiento por teclado desde el nodo enfocado: flechas desplazan
  10 píxeles de pantalla, convertidos según el zoom. `Escape` cancela un arrastre
  en curso y recupera la posición inicial. Tratar también `pointercancel` y la
  pérdida de captura sin dejar nodos bloqueados ni disparar selección accidental.

## 6. Animación útil, breve y desactivable

**Propósito:** conservar la orientación al abrir una carpeta, ajustar la cámara o
incorporar cambios de memoria y facilitar el seguimiento visual de conexiones.
El flujo animado representa relaciones del índice, no actividad de ejecución.

- [x] Mantener nodos y enlaces identificados de forma estable, actualizando sólo
  los afectados. Evitar recrear todo el SVG por cada selección: es requisito para
  conservar foco y enlazar posiciones anteriores con las nuevas.
- [x] Reutilizar `--enter` (220 ms) para transiciones de posición y cámara y
  `--fast` (140 ms) para opacidad. Usar transformaciones y opacidad; adaptar las
  líneas a las posiciones durante la transición para que sigan conectadas.
  Reutilizar la curva existente de entrada y definir una curva compartida de
  movimiento sólo donde haga falta. No añadir una biblioteca para estos efectos.
- [x] Al expandir con el puntero, incorporar los elementos desde su carpeta y
  desplazar suavemente los vecinos afectados; al contraer, retornar a ella.
  El arrastre sigue al puntero inmediatamente. Las acciones de teclado cambian
  el estado sin animación, conservando foco y respuesta inmediata.
- [x] Al cambiar de vista, evitar animar nodos de Arquitectura como si fueran los
  mismos elementos visibles del Grafo cuando no corresponda. Mantener la
  exclusión de vistas también durante la transición hacia Inventario.
- [x] Ante acciones rápidas, cancelar o redirigir la transición desde la posición
  actual. No acumular animaciones ni reiniciar recorridos completos.
- [x] Respetar «Movimiento desactivado» y `prefers-reduced-motion`: aplicar el
  estado final inmediatamente. Detener transiciones en vistas ocultas y pestañas
  en segundo plano. Una actualización sin cambios no dispara animación.
- [x] No mantener una simulación física permanente. Los nodos quedan quietos tras
  cada interacción; el movimiento de conexiones se controla de forma independiente
  de su posición y se detiene al desactivar el movimiento general.

### Trazado y flujo de conexiones

- [x] Al incorporar conexiones por expansión o cambios de memoria, mostrar un
  trazado progresivo breve de 220 ms. No volver a trazar todos los enlaces por
  seleccionar un nodo, hacer zoom o recibir una generación idéntica.
- [x] Añadir un flujo suave mediante segmentos luminosos que recorren las líneas
  en ambas vistas, sin desplazar los componentes. Activarlo con el control de
  movimiento existente: con selección, animar sólo sus conexiones visibles; sin
  selección, animar las conexiones visibles si no exceden el presupuesto.
- [x] Limitar el flujo simultáneo a 80 conexiones. Si se supera, mantener las
  líneas estáticas y mostrar «Selecciona un componente para ver sus conexiones
  animadas» en el idioma correspondiente. Si un nodo supera también ese límite,
  permitir acotar por filtros o vecinos; no escoger 80 enlaces arbitrarios como
  si fueran los únicos existentes.
- [x] Conservar la dirección únicamente cuando el tipo de relación y los datos
  la definan. En relaciones sin dirección, usar un pulso de opacidad sin flechas
  ni recorrido orientado. Mostrar tipo, origen y destino reales en el inspector,
  y aclarar en la leyenda que la animación no demuestra llamadas o ejecuciones.
- [x] Mantener una línea base visible bajo el efecto para leer las conexiones
  en cualquier instante. Separar efectos decorativos de áreas de selección,
  excluirlos del árbol accesible y evitar destellos o cambios bruscos de brillo.
- [x] Implementar el recorrido en el SVG local con CSS, por ejemplo mediante
  `stroke-dashoffset`, y usar opacidad para el pulso no dirigido. Esta animación
  de trazo requiere repintado: medir su coste con el límite anterior, sin suponer
  que tiene el mismo coste que una transformación. No añadir librerías ni red.
- [x] Al arrastrar, mantener los extremos unidos al nodo; pausar el efecto de
  sus enlaces durante el gesto y reanudarlo al soltar. No acumular trazados de
  entrada mientras el usuario está organizando el diagrama.
- [x] Con movimiento desactivado o reducido, mostrar inmediatamente las líneas
  completas, sin flujo ni pulsos. Pausar efectos al ocultar la vista, entrar en
  Inventario o pasar a una pestaña del navegador en segundo plano.

## 7. Aceptación adicional de distribución y movimiento

- [x] Probar escenarios sintéticos de 275 nodos y más de 1000, incluyendo árbol
  ancho, árbol profundo, nombres largos, nodos sin relaciones y filtros sin
  resultados. Verificar que los recuentos no confunden visibles con totales.
- [x] En Arquitectura expandida, comprobar separación mínima de hermanos y de
  etiquetas visibles. En Grafo, verificar colisiones de nodos y la política de
  etiquetas prioritarias. No exigir mostrar todos los nombres simultáneamente.
- [x] Probar expansión, contracción, búsqueda de elementos agrupados, arrastre,
  zoom, ajuste de vista y selección tras mover la cámara. Comprobar clics reales,
  foco, inspector y ruta completa de nombres truncados.
- [x] Arrastrar un nodo con distintos niveles de zoom y cámara desplazada:
  comprobar posición final, extremos de enlaces unidos y resto de nodos estable.
  Repetir tras filtrar, cambiar de vista y actualizar datos; verificar posiciones
  manuales conservadas y «Restablecer distribución» limitado a la vista actual.
- [x] Probar clic bajo el umbral, arrastre, `Escape`, cancelación del puntero y
  movimiento por teclado. Comprobar que arrastrar un objeto no desplaza la cámara,
  no cambia relaciones y no modifica los archivos ni hashes de la publicación.
- [x] Repetir con ambos idiomas, ambos temas y los tamaños de pantalla de la
  sección 4. La navegación del diagrama debe quedar dentro de su panel.
- [x] Comparar posiciones antes/durante/después de una transición y comprobar
  que termina. Repetir con acciones rápidas, movimiento desactivado y preferencia
  de movimiento reducido: sin animaciones pendientes ni pérdida de foco.
- [x] Verificar trazado de enlaces nuevos, flujo en ambas vistas y ausencia de
  flechas o recorridos dirigidos para relaciones sin dirección. Probar 80 y 81
  conexiones visibles, selección de un nodo con muchos vecinos, filtros y
  navegación rápida sin efectos duplicados ni enlaces visualmente desconectados.
- [x] Verificar pausa de conexiones durante el arrastre y en segundo plano;
  con movimiento desactivado o reducido no debe quedar ningún flujo o pulso.
  El movimiento de las líneas nunca debe interceptar clics ni alterar sus datos.
- [x] Publicar una generación con un archivo nuevo, otra con una eliminación y
  otra sólo con cambios de relaciones. Conservar cámara y selección válida y
  actualizar posiciones, inspector y recuentos según corresponda.
- [x] Medir tiempo de distribución e interacción sobre las fixtures y registrar
  entorno y resultados, incluyendo el flujo con 80 conexiones. Sin flujo animado,
  verificar que no quede un bucle de render activo en reposo; con flujo, comprobar
  que sólo permanezcan activos los efectos visibles dentro del presupuesto.
  Si el escenario denso bloquea la interfaz, reducir detalle o repartir el cálculo
  en trabajo acotado antes de aprobar; no ocultar el problema ampliando los tiempos
  de espera de las pruebas.
- [x] Repetir la regresión de Inventario después de añadir cámara y movimiento.
  Exigir funcionamiento offline, cero solicitudes externas y ausencia de errores
  de JavaScript/CSP. Mantener vigentes las pruebas de publicación y hashes.

## 8. Actualización de informes existentes

Pendiente de publicación y de ejecutar sobre el proyecto del usuario; no forma
parte de los cambios locales en esta rama. La actualización en vivo sí se ha
validado con fixtures sintéticas.

- [ ] Tras publicar el parche, actualizar el runtime de Harness que atiende al
  proyecto en su ámbito real; reiniciar el observador/servidor si sigue ejecutando
  la revisión anterior.
- [ ] Regenerar mediante `/aikya-memory --refresh` y reabrir el informe. El HTML
  integra CSS y JavaScript: actualizar el paquete o recargar un archivo antiguo
  sin regenerarlo no garantiza que cambie su presentación.
- [ ] Verificar el nuevo par HTML/reporte y la vista Inventario, conservando el
  índice y las notas existentes. No forzar sobrescritura de un informe personalizado.
- [ ] Repetir el caso con una publicación en vivo: al llegar una generación nueva,
  Inventario conserva su modo y el grafo sigue oculto.

## Resultados y ajustes de implementación

- Regresión completa: 630 pruebas, sin fallos, dos omisiones por dependencias del
  entorno cubiertas en ejecuciones separadas. Tras los últimos ajustes de
  presentación, 49 pruebas de Memory, 6 pruebas de distribución, 206 comprobaciones
  de navegador y 8 casos de instalación del wheel finalizaron correctamente.
- Para más de 150 nodos se utiliza colocación espacial acotada con posiciones
  previas y prioridad de anclajes manuales. La prueba de 500 nodos pasó de unos
  815 ms con fuerzas cuadráticas a 10,28 ms en la ejecución registrada.
- El presupuesto de 80 conexiones incluye también el trazado inicial y se calcula
  antes del límite de 3000 enlaces dibujados. Sólo `contains` representa dirección;
  las demás relaciones utilizan pulso sin recorrido orientado.
- Las etiquetas consideran el radio real del componente incluso con zoom alto.
  Los gestos se cancelan en la vista original antes de cambiar filtros o pestañas.
- Se verifican presupuestos y fin de transiciones; no se promete una tasa de
  fotogramas ni se ha realizado un perfil de GPU en otros dispositivos.
- El job de CI está preparado; su ejecución remota requiere publicar la rama.
  El informe contiene evidencias y una propuesta de descripción de PR.

## 9. Tiempo, riesgo y reversión

**Estimación orientativa del alcance ampliado:** 16–24 horas de trabajo, más CI y
revisión visual, aproximadamente 2–3 jornadas completas. Confirmar tras reproducir
las fixtures y medir el flujo animado.

| Bloque | Tiempo estimado |
|---|---|
| Inventario y reproducción de la superposición | 1–2 h |
| Distribución de Arquitectura y expansión | 3–4 h |
| Grafo, etiquetas y navegación de cámara | 4–6 h |
| Transiciones, accesibilidad y pruebas de regresión | 4–6 h |
| Arrastre individual, posiciones manuales y regresión | 2–3 h |
| Trazado y flujo de conexiones, límites y pruebas | 2–3 h |

Los tiempos de la propuesta inicial de Inventario no incluían la redistribución
de gráficos ni su animación. Ejecutar y verificar esos bloques por separado;
la corrección de Inventario no debe depender del trabajo de animación.

**Riesgo previsto:** bajo para el contenido de memoria; medio para la interacción
del visor por los cambios de cámara, expansión, arrastre, foco y carga de animación.
La búsqueda, el Inventario
y el inspector deben seguir permitiendo acceder a todos los datos. No cambian el
índice, los comandos de desarrollo ni la persistencia. El cálculo local no requiere
tokens ni servicios adicionales; el coste técnico es CPU y memoria del navegador.

**Reversión:** revertir el parche y regenerar mediante el exportador de esa
revisión. No restaurar a mano sólo un HTML con un hash distinto de su reporte.

GENERATED BY AIKYA HARNESS
