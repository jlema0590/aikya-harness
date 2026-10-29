# Validación local de eficiencia de tokens — v7.2.0

**Resultado:** implementación local verificada en `feat/token-efficiency`.
**Base:** develop `177f032` y dependencia Memory `512dea2`.
**Recibo:** [evidencia estructurada](2026-10-29-token-efficiency.json).
**Entorno ejecutado:** macOS ARM64, Python 3.13.18. No se modificó `jourpass_app`
ni la configuración personal de Claude. No se ejecutaron modelos reales.

## Funcionalidad implementada

- Medición sin contenido: entrada, salida, creación/lectura de caché, mensajes
  distintos y cobertura. Las ventanas temporales no se presentan como factura por
  comando. Las filas no medidas conservan modelo/tokens desconocidos.
- Dart estructural real, incluidos métodos, constructores con nombre y funciones
  locales; rangos/hash actuales y cobertura por extensión en status y HTML.
- Instalación explícita de parsers binarios fijados mediante `--code-index
  none|dart|all`, con conservación de selección y comprobación en el intérprete
  administrado. Sin compilación ni instalación silenciosa.
- Paquete de contexto compartido de hasta 6.000 caracteres, búsqueda léxica de
  símbolos/rutas, JSON completo acotado y lectura de fuente actual sin duplicados.
  Un índice ajeno/corrupto se conserva y se señala; el fallback no reutiliza sus
  símbolos ni amplía el alcance explícito.
- Respuestas `--summary`, preflight documental con las mismas reglas de Stop,
  fases de inspección proporcionales y reutilización opt-in de evidencia local
  determinista vinculada a candidato, definición y entorno.
- Presupuestos acumulados del loop para Implement/Review, reanudación y replay.
  Uso vacío/desconocido no se convierte en cero; se conservan comprobaciones locales
  antes de detener otra consulta al modelo.
- Compactación nativa manual por defecto, opt-in por proyecto y continuidad por
  metadatos. «Continúa» recupera rutas previas actuales; una tarea nueva no hereda
  ese alcance. Se conservan presupuestos y checks, sin generar aprobaciones.
- Menos instrucciones repetidas y proveedores externos preseleccionados; sigue
  disponible la instalación de una skill elegida expresamente por el usuario.

## Pruebas observadas

| Área | Evidencia local |
|---|---|
| Regresión | 678 IDs cubiertos: 677 en cuatro grupos aislados y 1 caso adicional de cambio de tarea, con cinco revalidaciones de contexto |
| Omisiones del entorno principal | 2, verificadas aparte: fallback sin extras y prueba PowerShell con runtime portátil |
| Comandos | 28/28; 52 procesos, con denegaciones/fallos esperados y sin ejecución de modelos |
| Lenguajes | 29/29 extensiones: alta, edición, renombrado, borrado, scope e identidad; semántica solo donde existe parser |
| Stacks | 28 casos de perfil/selección de especialistas y 14 ejemplos existentes válidos |
| Onboarding | 48 combinaciones de tipo, ODD/SDD, en/es, global/project y nuevo/existente |
| Navegador | 180 comprobaciones: visor/interacciones en ambos idiomas y cobertura mixta Python/Dart/Swift en/es |
| Instalación | Limpia/update/offline global y proyecto, selección Dart/all, conservación, doctor y desinstalación que preserva archivos/entornos referenciados |
| Wheel | 8 casos de registro/onboarding ODD/SDD fuera del checkout; 165 módulos Python coinciden con la fuente actual |
| Calidad | Sin errores de calidad de fuente; advertencias de cohesión existentes/de revisión, sin archivos de fuente nuevos de más de 1.000 líneas |
| Metadatos y plantillas | 28 comandos, 30 agentes, 29 skills y catálogo de 120 plantillas válidos |

El cierre repitió 18 pruebas de compactación/contexto/benchmark/selección de skills
y matriz multilenguaje,
sin fallos. El control documental del diff y los pies Markdown quedaron válidos;
se completaron overview, arquitectura, política de tokens y sistema de diseño
con el comportamiento observado.

La regresión principal tuvo 676 casos aprobados y dos omisiones de entorno; las dos
se comprobaron por separado. El recibo conserva IDs/cobertura y hashes de logs,
sin copiar prompts, código privado ni conversaciones. Durante el desarrollo, la
protección de runtime detectó cambios concurrentes de fuente; los grupos afectados
se repitieron y sus resultados finales son los recogidos aquí. La fixture Go del
smoke de todos los parsers se corrigió para utilizar saltos de línea canónicos.

## Comparación reproducible, sin equivalencias con cuota

| Fixture | Caracteres de referencia | Caracteres del candidato | Reducción local |
|---|---:|---:|---:|
| analyze | 76,547 | 590 | 99.23% |
| small_mobile_change | 12,992 | 502 | 96.14% |
| authentication_change | 13,103 | 510 | 96.11% |
| external_edit | 12,992 | 502 | 96.14% |

Analyze compara su respuesta completa con `--summary` en el mismo repositorio Maven
sintético. Los otros casos comparan el JSON de la consulta anterior —incluidos
matches/context— con el paquete nuevo sobre el mismo archivo permitido. Se verifica
la declaración esperada y la edición externa; autenticación conserva el requisito
de revisión. Estas cifras miden caracteres de herramientas/contexto, no tokens
reales, solicitudes ahorradas, calidad de una feature completa ni cuota de Claude.

La suma estática de cuerpos de los 28 comandos pasa de 126.119 a 107.758 caracteres
(14,56%). Doctor reduce un 26,18%, SDD Status un 36,54% y Feature un 4,29%. Los 28
cuerpos no se cargan juntos; el proxy no es un tokenizador ni una factura.

## Límites y validación pendiente externa

- La reducción real de tokens/cuota sigue **sin medir**. Requiere tareas aceptadas
  equivalentes, mismo modelo/effort/caché y presupuesto revisado. La prueba real del
  SDK se realizará en el otro entorno indicado por el usuario.
- Linux/Windows y Python 3.10–3.12 tienen CI nativa configurada; no se presentan como
  ejecuciones locales. Se descargaron 60 binarios fijados para preparar los assets
  de seis plataformas/24 combinaciones CPython. Descarga no equivale a ejecución.
- Linux musl ARM64 carece del core fijado; Windows ARM64 no está verificado. Se
  conserva inventario/fallback y una selección incompatible no activa el candidato.
- Kotlin, Swift y otras extensiones sin parser mantienen `file_only`; YAML/JSON,
  HTML/CSS/SCSS, Astro y manifiestos no se anuncian como formatos indexados.
  Las pruebas de perfil/parser no acreditan builds de aplicaciones.
- El payload nativo estándar no prueba la ventana efectiva de compactación. Por
  tanto, el aviso del 75% queda N/D sin telemetría fresca verificable; no se calcula
  a partir del porcentaje del modelo. La ventana solicitada de 200.000 puede tener
  overrides del host. Compactar consume tokens y no reinicia cuota.

## Aplicación posterior a publicación

Actualizar el scope e intérprete realmente usados por el proyecto. Una actualización
global no actualiza automáticamente copias de runtime de otros proyectos. Revisar
primero el registro local con la versión nueva de `aikya-setup --scope project
--target <project> --dry-run`; aplicar solo activos administrados y resolver
conflictos personalizados sin borrar archivos. Elegir explícitamente Dart/all en
el intérprete administrado y comprobar doctor/cobertura. Reiniciar sesión/observador
antiguos y regenerar mediante `/aikya-memory --refresh`. Revisar las instrucciones de
compactación en CLAUDE.md personalizado; no sobrescribirlo. Mantener el modo manual
hasta autorizar la opción nativa del proyecto. No se ha aplicado este rollout al
proyecto privado ni se ha publicado la rama.

GENERATED BY AIKYA HARNESS
