# Plan de implementación: instalación unificada de Harness y Mods

**Objetivo:** instalar Aikya Harness y los mods oficiales seleccionados con un
único comando por sistema operativo, sin clonar repositorios.

**Arquitectura:** ampliar el bootstrap Python existente como coordinador de
componentes. Reutilizar sus descargas, integridad, entornos y recibos; obtener el
bundle publicado de Mods y registrarlo mediante la CLI nativa de Claude. GitHub
Pages servirá entradas cortas generadas desde una release verificada.

**Tecnologías:** Python 3.10–3.13, shell POSIX, PowerShell 5.1/7, GitHub Releases,
GitHub Pages y la CLI de Claude Code. Referencia de CLI comprobada: 2.1.308.

**Especificación:** petición del usuario de integrar la instalación de
`jlema0590/aikya-mods` en Harness y reducirla a un comando corto. Este documento
define el contrato propuesto; su implementación se revisará después del plan.

**Rama:** `feat/unified-installation-mods`, creada desde `origin/develop`,
commit `0b9a392257671167f7af4f4a217190c254207ee9`, que incluye la PR de memoria.

## 1. Evidencia verificada

Revisión del 26 de octubre de 2026:

| Elemento | Estado observado | Consecuencia |
|---|---|---|
| Harness | Release pública `v7.0.1`, con wheel, bootstrap, instaladores y SHA256SUMS | Ampliar este instalador; conservar sus garantías y enlaces existentes |
| Mods publicado | Última release pública `v0.0.10`; bundle ZIP, `release.json` y SHA256SUMS | Consumir assets reales; no asumir los nuevos instaladores por OS |
| Checkout local de Mods | Rama `feature/marketplace-flow-usage`, commit `7e19ce0`; VERSION `0.0.14` | Sus mejoras no equivalen a una release publicada |
| Instaladores de Mods en v0.0.10 | Usan Git si no reciben una fuente local | No encadenar su descarga/ejecución sin argumentos |
| Mods presentes en el catálogo | `aikya-flow`, `aikya-usage`, `aikya-boxbot` | Proponer Flow + Usage por defecto; BoxBot opcional |
| CLI instalada | `claude` 2.1.308; marketplace add, plugin install y list admiten JSON | Usar esta interfaz, sin editar registros internos de plugins |
| GitHub Pages de Harness | Consulta API devuelve 404; no hay homepage configurada | La URL corta es una propuesta pendiente de publicación |
| Gestión actual | `--scope` obligatorio; PATH requiere una acción posterior | Simplificar valores predeterminados y activación para la siguiente terminal |

El catálogo publicado de v0.0.10 contiene BoxBot 0.3.0, Flow 0.1.0 y Usage 0.1.0.
No anunciar las versiones locales más nuevas como instalables hasta publicarlas.
Antes del despliegue se volverá a resolver la última release de cada repositorio.

## 2. Experiencia propuesta

**Comandos objetivo, todavía no publicados ni utilizables como nueva instalación:**

Linux/macOS:

```sh
curl -fsSL https://jlema0590.github.io/aikya-harness/install.sh | sh
```

Windows PowerShell:

```powershell
irm https://jlema0590.github.io/aikya-harness/install.ps1.txt | iex
```

La entrada Windows se ofrece también como texto para ejecutar su contenido;
la publicación debe verificar MIME, codificación y ejecución real con PowerShell
5.1 y 7 antes de anunciar el comando. El asset descargable `install.ps1` se
conserva para inspección, argumentos avanzados y uso sin tubería.

La instalación predeterminada será **Harness + Flow + Usage**, ámbito global,
últimas releases estables compatibles. No habrá preguntas obligatorias ni una
selección distinta porque stdin sea una tubería. BoxBot se añade con selección
explícita o con la opción de todos los mods.

Requisitos previos: Python admitido con venv/pip y Claude Code con soporte de
Mods. Si falta Claude o una capacidad necesaria, la instalación del conjunto
fallará en preflight antes de escribir. `--mods none` permitirá instalar sólo
Harness. No se iniciará sesión, llamará a modelos ni instalará Python/Claude
mediante gestores del sistema como parte de este alcance.

Tras instalar, se abrirá una nueva terminal/sesión de Claude para cargar PATH y
plugins. El usuario no tendrá que clonar, descargar ZIP manualmente, registrar
un marketplace o instalar cada mod mediante comandos separados.

### Opciones avanzadas del instalador/gestor

| Opción propuesta | Efecto |
|---|---|
| Sin opciones | Global, Harness + Flow + Usage |
| `--scope project --target <ruta>` | Registro del proyecto; se conserva esa ruta como cwd de las operaciones de plugins |
| `--mods recommended` | Flow + Usage |
| `--mods all` | Mods oficiales disponibles del catálogo compatible verificado |
| `--mods none` | Sólo Harness; no instalar ni eliminar mods por esta operación |
| `--mod aikya-flow` repetible | Selección explícita; incompatible con otra selección de grupo |
| `--version X.Y.Z` | Fijar Harness |
| `--mods-version X.Y.Z` | Fijar el bundle de Mods, independientemente de Harness |
| `--dry-run` | Mostrar componentes, ámbitos y destinos sin red, escrituras o llamadas a Claude |
| `--offline-dir <ruta>` | Consumir artefactos verificados ya disponibles; ambas versiones deben quedar fijadas |
| `--no-path` | Omitir la gestión de PATH y mostrar la ruta del ejecutable |
| `uninstall --keep-mods` | Retirar Harness conservando los mods y sus fuentes referenciadas |

PowerShell tendrá opciones equivalentes (`-Scope`, `-Target`, `-Mods`, etc.).
Mapeo: Harness `global` → Mods `user`; Harness `project` → Mods `project`.
El ámbito `local` propio de Mods sigue siendo independiente; no crear un tercer
ámbito de Harness ni mezclarlo con el directorio de análisis `--scope`.

## 3. Restricciones globales

- Mantener los 28 comandos del harness; los mods son plugins de Claude, no Agent
  Skills adicionales ni una nueva vía de instalar skills externas.
- Descargar sólo releases estables publicadas, resolver cada versión una vez y
  fijarla para todos sus assets; nunca usar `main` como fallback.
- Mantener SHA-256, límites de descarga, validación de metadatos y extracción
  segura. No debilitar comprobaciones para admitir una release incompatible.
- No añadir Bash, Git o Node como requisitos del instalador de Harness. Python
  puede leer/verificar el ZIP de Mods en los tres sistemas.
- Conservar fuentes de marketplace en un directorio persistente por versión;
  Claude no debe quedar apuntando a archivos temporales eliminados.
- No sobrescribir configuración personalizada, plugins previos, políticas,
  hooks, fuentes modificadas ni la documentación de los proyectos.
- No aceptar automáticamente comandos arbitrarios declarados por marketplaces.
  Admitir fuentes locales del bundle verificado y detenerse si la CLI exige una
  aprobación adicional no incluida en ese contrato.
- Tratar errores entre componentes como instalación parcial recuperable; no
  prometer una transacción atómica entre Harness y la CLI de plugins.
- Mantener los recibos antiguos legibles. Una actualización sin selección nueva
  conserva la selección registrada; no incorpora mods a instalaciones antiguas
  sin una elección explícita.
- Inglés para código, mensajes y documentación de ingeniería; README bilingüe.
  Planes/informes en `aikya/docs/`; Markdown con el pie obligatorio.
- No modificar releases existentes ni elegir una nueva versión sin revisar el
  alcance final y su changelog. Este trabajo prepara una próxima release.

## 4. Riesgos que deben cubrir las pruebas

1. Cambio de `latest` entre descargas, versión local sin publicar o catálogo
   incompatible: no mezclar assets ni configurar Claude antes de verificar.
2. Mods/marketplace ya instalados por el usuario: detectar propiedad, evitar
   duplicados y preservar su origen/configuración en actualización/desinstalación.
3. Fallo de la segunda instalación de plugin, interrupción o ejecución paralela:
   registrar resultados parciales, conservar fuentes referenciadas y reanudar.
4. Windows PowerShell 5.1/7, CRLF, rutas con espacios/Unicode y arranque lento:
   verificar bytes, argumentos y readiness; no depender de sleeps fijos.
5. Scope project desde otra carpeta, tuberías y terminales no interactivas:
   mantener destino, selección, stdin y configuración del usuario correctos.

## 5. Archivos e interfaces

| Archivo de Harness | Responsabilidad prevista |
|---|---|
| `src/aikya/installation/bootstrap/mods.py` (nuevo) | Resolver/verificar el bundle, extraerlo de forma segura y conservar la fuente versionada |
| `src/aikya/installation/bootstrap/claude_plugins.py` (nuevo) | Adaptador de la CLI nativa: preflight, inventario JSON, registro e instalación sin shell interpolado |
| `src/aikya/installation/bootstrap/components.py` (nuevo) | Selecciones, ámbitos, planificación y estados parciales/propiedad por componente |
| `src/aikya/installation/bootstrap/user_path.py` (nuevo) | Bloque gestionado de PATH, recibo y retirada conservadora |
| `src/aikya/installation/bootstrap/{cli,download,state,launchers}.py` | Integrar opciones y ciclo de vida, reutilizando primitivas existentes |
| `scripts/install/install.{sh,ps1}.tmpl` | Entradas con valores predeterminados equivalentes y paso de opciones |
| `scripts/ci/build_installers.py` | Construir los assets, sin copias manuales divergentes |
| `scripts/ci/build_install_pages.py` (nuevo) | Preparar Pages sólo desde un tag publicado y assets comprobados |
| `.github/workflows/install-pages.yml` (nuevo), `release.yml` | Publicar/reintentar las entradas cortas tras una release correcta |
| `tests/test_unified_installer.py`, `test_mods_distribution.py`, `test_user_path.py`, `test_install_pages.py` (nuevos) | Contratos y regresiones de los cinco riesgos anteriores |
| `scripts/ci/installer_smoke.py`, `package_smoke.py`, `installers.yml` | Pruebas desde artefactos finales y entornos aislados |
| `README.md`, `README.es.md`, `CHANGELOG.md`, `aikya/docs/indice.md` | Uso sencillo, límites, auditoría y versión aprobada |

Interfaces a introducir:

- `plan_components(scope, target, selection, previous_receipt) -> ComponentPlan`:
  sin efectos; selección explícita para cada componente y propietarios previos.
- `prepare_mods(version, destination, offline_dir=None) -> VerifiedModsBundle`:
  tag, ruta persistente, huellas y catálogo validados.
- `install_plugins(bundle, selected, scope, target) -> ModsResult`: comandos argv
  acotados; resultados por plugin e instalación parcial explícita.
- `ensure_user_path(bin_dir, enabled=True) -> PathChanges`: cambios gestionados
  rastreables; no intentar modificar el entorno del shell padre Unix.

## 6. Tareas de implementación

### Tarea A — Contrato de releases y bundle verificado · 4–6 h

- [ ] Añadir primero fixtures reales de v0.0.10 y del formato nuevo cuando esté
  publicado. Probar cambio de latest, hash incorrecto, ZIP truncado, traversal,
  symlinks, duplicados, catálogo/versiones inconsistentes y nombres de plugins.
- [ ] Observar los fallos con `python -B -m unittest discover -s tests -p
  test_mods_distribution.py -v`; implementar `prepare_mods()` reutilizando el
  transporte HTTPS y parser de checksums actuales, sin ejecutar instaladores.
- [ ] Repetir las pruebas; exigir cero configuración de Claude si no se confirma
  la integridad. Guardar un commit independiente.

### Tarea B — Coordinador de instalación, propiedad y recuperación · 10–14 h

- [ ] Probar antes de implementar selección recomendada/todos/ninguno/individual,
  mapeo de scopes y errores de CLI; `--dry-run` no invoca red ni Claude.
- [ ] Implementar `plan_components()` e `install_plugins()`. Usar `claude plugin
  marketplace add <fuente> --scope <scope> --json` y `claude plugin install
  <id>@aikya-mods --scope <scope> --json`, con cwd del destino cuando corresponda.
- [ ] Leer inventario con la API JSON disponible; validar capacidades antes de
  efectos. Probar archivos/rutas especiales y wrappers nativos en Windows.
- [ ] Preparar y verificar ambas distribuciones antes de activar cambios. Mantener
  recibos por componente con versión, scope, fuente, propietario y resultado.
- [ ] Fallar antes de escribir si falta Claude para el conjunto solicitado.
  Si falla una operación posterior, devolver estado parcial y código distinto de
  éxito total; `doctor` lo muestra y el reintento conserva lo ya verificado.
- [ ] Actualizar sólo los componentes seleccionados/registrados. Desinstalar sólo
  mods gestionados en su ámbito, conservar instalaciones previas y fuentes con
  referencias; admitir conservar Mods al retirar Harness.
- [ ] Ejecutar `test_unified_installer.py`, contratos existentes de instalación y
  recuperación; validar repetición, interrupción, fallo del segundo plugin y dos
  ejecuciones simultáneas. Guardar commit.

### Tarea C — Entradas simples y PATH · 6–10 h

- [ ] Probar scripts sin opciones y sin TTY: global + Flow + Usage en ambos OS,
  sin consumir stdin para menús. Mantener los parámetros avanzados existentes.
- [ ] Eliminar la obligatoriedad de escribir el scope para la instalación nueva;
  respetar selección explícita y no añadir mods a una actualización heredada.
- [ ] Gestionar sólo un bloque/entrada de PATH identificable: perfiles admitidos
  de Bash/Zsh y PATH de usuario Windows. Conservar contenido ajeno y permitir
  `--no-path`; para otros shells informar del destino sin escribir sintaxis errónea.
- [ ] Probar reinstalación, perfil editado/symlink, desinstalación y rutas Unicode;
  no duplicar entradas ni exigir sudo o cambiar la ExecutionPolicy guardada.
- [ ] En ejecución PowerShell mediante `iex`, restaurar las preferencias del
  llamador y devolver el control sin cerrar su terminal.
- [ ] Ejecutar `test_user_path.py`, pruebas de entrypoints e instalación limpia;
  no declarar disponible el comando Unix en el shell padre antes de reabrirlo.

### Tarea D — URL corta por GitHub Pages · 4–6 h

- [ ] Construir Pages desde `install.sh` e `install.ps1` de un tag ya publicado y
  comprobado contra SHA256SUMS; conservar exactamente los bytes del script.
  Publicar los nombres `install.sh` e `install.ps1.txt`, una página mínima de ayuda
  y metadatos de procedencia. No copiar código de una rama móvil.
- [ ] Crear workflow reutilizable/manual. Invocarlo desde `release.yml` después
  del job `publish`, con permisos de Pages restringidos y entorno `github-pages`.
  No depender sólo de `release: published`: publicaciones con GITHUB_TOKEN no
  disparan automáticamente ese segundo workflow.
- [ ] Habilitar Pages por Actions como paso de despliegue revisado. Probar que un
  fallo de publicación conserva la entrada anterior y permite reintentar el tag.
- [ ] Ejecutar `test_install_pages.py`; después del despliegue comprobar HTTPS,
  cabeceras/codificación, huellas y los comandos cortos reales en los tres OS.
  Anunciar las nuevas URLs sólo después de esa comprobación.

### Tarea E — Aceptación completa y documentación · 8–12 h

- [ ] Ejecutar una release fixture por HTTPS simulado y los assets finales con
  configuración de Claude aislada; no usar los plugins/credenciales del usuario.
- [ ] Cubrir Linux, macOS y Windows; PowerShell 5.1/7; global/project; recomendado,
  todos, ninguno e individual; primera instalación, repetición, update, parcial,
  reparación, retirada y offline. La instalación debe fallar si intenta ejecutar Git.
- [ ] Validar con CLI real de Claude registro, instalación y lectura del catálogo;
  esto no exige prompts/modelos. La apariencia de los mods se comprueba en una
  sesión de Claude con soporte nativo, separada del ensayo de instalación.
- [ ] Ejecutar la suite completa del repositorio y la batería de los 28 comandos;
  verificar memoria, HTML, ODD/SDD y archivos generados bajo `aikya/docs/`.
- [ ] Revisar convivencia de Flow/Usage con la observabilidad y statusLine actuales:
  no crear otra barra propia ni sobrescribir preferencias para aparentar integración.
- [ ] Actualizar README en/es, changelog e informe de validación con resultados
  observados. Abrir PR contra develop y separar aprobación de código de release
  y despliegue de Pages.

## 7. Conexión de Flow con la evidencia del harness

Instalar Flow no demuestra que esté conectado a la caché de ejecución. Actualmente
`/aikya-flow connect <cache-root>` establece una conexión en memoria de la sesión;
sin ella, las fases muestran **No evidence**. El formato compatible existe en
`src/aikya/core/state.py`; no es la base SQLite del índice de código.

La primera entrega conserva ese contrato y muestra el estado de conexión en el
resumen/doctor. Automatizar la conexión persistente requiere una ampliación
coordinada de Mods y Harness; estimación separada **6–10 h**. De aprobarse, debe
vincular exclusivamente el proyecto/sesión, respetar `AIKYA_EXECUTION_CACHE`,
conservar validación de identidad/evidencia y no leer memorias privadas globales.
No introducir un segundo motor de fases ni copiar eventos entre dos cachés.

## 8. Esfuerzo y salida de esta fase

**Instalación unificada + comandos cortos + pruebas: 32–48 h**, aproximadamente
4–6 jornadas de trabajo efectivo; tiempos de cola de CI/publicación aparte.
La conexión automática de Flow, si se añade, supone 6–10 h adicionales.

El riesgo principal está en mezclar versiones publicadas/locales, propiedad de
plugins y fallos parciales de la CLI. No se ha identificado una necesidad de
reescribir el instalador ni fusionar todo el repositorio de Mods dentro de Harness.
La aceptación nativa y desde paquetes finales deberá confirmar la compatibilidad.

En esta fase se crea la rama y este plan; no se cambian instaladores, se instalan
mods en el equipo, se publican releases ni se habilita Pages.

## Referencias

- [Harness y sus releases](https://github.com/jlema0590/aikya-harness/releases).
- [Mods y sus releases](https://github.com/jlema0590/aikya-mods/releases).
- [Contrato local de la última release observada de Mods](https://github.com/jlema0590/aikya-mods/tree/v0.0.10).
- [URL de sitios de proyecto en GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
- [Workflows de Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
- [Eventos creados con GITHUB_TOKEN](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

GENERATED BY AIKYA HARNESS
