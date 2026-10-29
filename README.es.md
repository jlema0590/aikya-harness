# Aikya Harness

[English](README.md) | [Español](README.es.md)

**Un flujo de ingeniería. Múltiples agentes de IA. Calidad consistente.**

![Aikya Harness](docs/images/aikya-harness.png)

Aikya Harness es un entorno de ingeniería para Claude Code que combina incorporación
segura de proyectos, generación de estructuras de aplicaciones, planificación de
infraestructura como código, subagentes especializados, Agent Skills, controles de
calidad, observabilidad y documentación viva.

Incluye soporte para backends Java, .NET, Node.js, Next.js y Python; frontends React,
Vue, Angular y Astro; aplicaciones Android, iOS, Flutter y React Native; y repositorios
independientes de infraestructura y DevOps.

**Todas las interacciones se inician desde Claude Code.** Aikya gestiona internamente
sus scripts de Python y solicita aprobación antes de escribir archivos, descargar
recursos de terceros, instalar SDK o realizar operaciones externas.

## 1. Inicio rápido

Instala **Harness + Flow + Usage** globalmente con un comando. BoxBot es opcional.
Requiere Python 3.10–3.13 con `venv`/pip y Claude Code nativo 2.1.308+ para Mods.

> El instalador unificado y las URLs cortas estarán disponibles con la release
> que incluya este cambio. Las URLs de Pages requieren un despliegue correcto
> antes de utilizarlas; el instalador publicado anterior no admite las nuevas
> opciones de Mods.

**Linux / macOS**:

```sh
curl -fsSL https://jlema0590.github.io/aikya-harness/install.sh | sh
```

**Windows PowerShell 5.1 / 7**:

```powershell
irm https://jlema0590.github.io/aikya-harness/install.ps1.txt | iex
```

Para revisar el script o indicar opciones, descarga `install.sh` o `install.ps1`
de la release publicada. Por ejemplo:

```sh
sh ./install.sh --scope project --target /ruta/absoluta/al/proyecto
sh ./install.sh --mods all       # Incluir BoxBot
sh ./install.sh --mods none      # Sólo Harness; no requiere Claude
sh ./install.sh --dry-run        # Sin red, escrituras ni llamadas a Claude
```

```powershell
.\install.ps1 -Scope project -Target 'C:\work\proyecto'
.\install.ps1 -Mods all
.\install.ps1 -Mods none
.\install.ps1 -DryRun
```

| Opción | Comportamiento |
|---|---|
| Predeterminado / `--scope global` | Registro de Harness por usuario y scope `user` de Mods. |
| `--scope project --target <ruta>` | Registro de Harness y Mods para ese directorio de proyecto existente. |
| `--mods recommended` | Flow + Usage. |
| `--mods all` | Plugins oficiales del catálogo verificado, incluido BoxBot. |
| `--mods none` | Instalar/actualizar sólo Harness; conservar Mods sin cambios. |
| `--mod <id>` repetible | Selección explícita; incompatible con `--mods`. |
| `--version X.Y.Z` / `--mods-version X.Y.Z` | Fijar versiones independientes de Harness / Mods para esa operación. |
| `--no-path` | Conservar el PATH del usuario sin cambios. |

Equivalentes PowerShell: `-Mods`, `-Mod`, `-ModsVersion` y `-NoPath`.
Este scope es independiente de `/aikya-analyze --scope <ruta-relativa>`, que elige
la carpeta a analizar. Instalar no inicializa el proyecto ni selecciona ODD/SDD.

El instalador resuelve cada última release estable una vez, verifica SHA-256 y el
catálogo local, y conserva las fuentes versionadas del marketplace. Utiliza la
CLI nativa de plugins de Claude sin clonar, instalar Git/Node, pedir permisos de
administrador ni realizar llamadas a modelos de IA. Si faltan requisitos, detiene
el conjunto solicitado antes de activarlo; `--mods none` permite instalar Harness
sin Claude.

Abre una **terminal y sesión de Claude nuevas** después de instalar. Los perfiles
Bash/Zsh admitidos y el PATH de usuario de Windows reciben una entrada gestionada;
en otros shells se muestra la carpeta para configurarla manualmente. No instala
Python/Claude ni cambia la política de ejecución.

Para añadir BoxBot después de registrar el marketplace:

```sh
claude plugin install aikya-boxbot@aikya-mods --scope user
```

Para un proyecto, ejecutar desde su carpeta con `--scope project`. Los plugins
instalados directamente con Claude conservan su propiedad externa; una selección
explícita en el gestor puede incorporarlos a las actualizaciones si su fuente
verificada coincide, conservándolos al desinstalar. Las fuentes ajenas de
marketplace requieren revisión antes de reemplazarse.

**Las actualizaciones son explícitas**, sin procesos en segundo plano:

```sh
aikya-manage update --scope global
aikya-manage update --scope project --target /ruta/absoluta/al/proyecto
aikya-manage doctor
aikya-manage uninstall --scope global
# Conservar Mods al retirar Harness:
aikya-manage uninstall --scope global --keep-mods
```

Actualizar conserva los IDs registrados: actualiza BoxBot sólo si está gestionado,
sin añadirlo ni incorporar futuros plugins automáticamente. Una instalación
heredada de sólo Harness sigue igual hasta seleccionar Mods explícitamente.
Conserva archivos personalizados y plugins externos. Si falla una operación de
plugins, devuelve error, `doctor` muestra el estado parcial y se puede reintentar.
Las fuentes compartidas o modificadas requieren revisión. Las fuentes persistentes
se conservan de forma prudente.

Sin conexión, deja el script de Harness, bootstrap, wheel y `SHA256SUMS` en un
directorio; guarda `release.json`, ZIP del bundle y `SHA256SUMS` de Mods en el
subdirectorio `mods/`. Utiliza `--offline-dir <ruta>` y `--mods-version X.Y.Z`
(PowerShell `-OfflineDir` / `-ModsVersion`). El script fija su versión de Harness
sin conexión; las llamadas directas al gestor también requieren `--version`.
La gestión conjunta requiere Harness 7.1.0 o superior. Sólo se pueden elegir
versiones anteriores para registros de sólo Harness sin Mods gestionados.
`--mods none` permite omitir el bundle. Los proyectos inicializados conservan sus
intérpretes referenciados. En Windows, el bootstrap independiente permite completar
la retirada si el ejecutable de gestión está en uso.

Instalar Flow no lo conecta automáticamente con la evidencia de ejecución.
Utiliza `/aikya-flow connect <cache-root>` en la sesión actual; `doctor` indica que
no ha comprobado esa conexión de sesión. Flow y Usage conservan tu statusLine.

**Contribuidores:** crea un entorno virtual, instala `build`, `setuptools>=77` y
`wheel`, y ejecuta `python -m pip install --no-build-isolation --no-deps -e .`.
Utiliza `aikya`, `aikya-setup` o `python -m aikya`; se retiran los lanzadores Python
de raíz. La apariencia en la sesión nativa y la ejecución autenticada del modelo
se validan por separado de la aceptación del instalador.

## 2. Incorporación de proyectos

| Punto de partida | Comando | Funcionamiento |
|---|---|---|
| **Proyecto nuevo** | **`/aikya-init`** | Entrevista, decisiones técnicas e inicialización aprobada. |
| **Repositorio existente** | **`/aikya-analyze`** | Detección de tecnologías mediante evidencias del repositorio y vista previa de la incorporación. |

### Proyectos nuevos → `/aikya-init`

```text
/aikya-init
```

Utiliza un directorio de proyecto vacío. El comando selecciona siempre `mode=new`
y te guía por las decisiones necesarias. Si detecta código existente, utiliza `/aikya-analyze`.

| Tipo de proyecto | Opciones que se definen durante la incorporación |
|---|---|
| `development` | Tecnologías, estructura del repositorio, arquitectura, pruebas y soporte opcional de infraestructura o plataforma. |
| `infrastructure` | Terraform/OpenTofu, Ansible, proveedor, entornos y restricciones. |
| `devops` | Docker, imagen o código fuente, chart de Helm existente, Kubernetes y YAML/Kustomize. |

La entrevista también pregunta el idioma de la documentación viva. Revisa el plan
de archivos antes de aprobar los cambios. Después, comprueba los requisitos y
planifica la generación de la estructura:

```text
/aikya-doctor
/aikya-scaffold plan
```

Para infraestructura o DevOps, empieza con `/aikya-infra plan`.
Los generadores, las descargas y las operaciones externas requieren las aprobaciones correspondientes.

### Proyectos existentes → `/aikya-analyze`

Empieza con una vista previa de solo lectura:

```text
/aikya-analyze --dry-run --methodology odd --docs-lang en
```

Aikya detecta las tecnologías y la arquitectura existentes sin una entrevista técnica.
Presenta los cambios gestionados por Aikya antes de incorporarlos. Los repositorios
ambiguos devuelven `PARTIAL` o `NEEDS_REVIEW` y requieren revisión antes de continuar.

| Opción | Finalidad |
|---|---|
| `--dry-run` | Mostrar la detección y los cambios previstos sin instalar. |
| `--report-only` | Devolver un informe de análisis sin escribir archivos. |
| `--focus general` | Análisis general; enfoque predeterminado. |
| `--focus security` | Centrarse en evidencias de seguridad. |
| `--focus architecture` | Centrarse en evidencias de arquitectura. |
| `--focus infrastructure` | Centrarse en evidencias de infraestructura. |
| `--focus operations` | Centrarse en evidencias operativas. |
| `--scope <relative-path>` | Limitar la detección a un componente, como un espacio de trabajo de un monorepo. |
| `--methodology odd` o `--methodology sdd` | Elegir ODD o SDD antes de la incorporación inicial. |
| `--refresh` | Actualizar únicamente los recursos de análisis cuya gestión por Aikya pueda verificarse. |
| `--docs-lang en` o `--docs-lang es` | Elegir el idioma de la documentación viva. |

Ejemplos: ejecuta cada uno por separado según lo necesites.

```text
/aikya-analyze --report-only --focus security
/aikya-analyze --dry-run --focus architecture --scope apps/api --docs-lang en
/aikya-analyze --refresh
```

La detección no compila aplicaciones, ejecuta scripts de la aplicación ni despliega
infraestructura. La incorporación conserva el código de la aplicación y las configuraciones personalizadas.

### Elegir ODD o SDD

**Tanto `/aikya-init` como `/aikya-analyze` ofrecen ODD y SDD.** ODD es la
recomendación; hay que confirmar la elección inicial antes de escribir. ODD
mantiene los cambios acotados en la auditoría de petición existente y añade tareas
y continuidad para trabajos sustanciales. SDD conserva sus aprobaciones separadas
de especificación, plan y tareas. En repositorios existentes, empieza por una vista previa:

```text
/aikya-analyze --dry-run --methodology sdd --docs-lang en
```

Revisa el plan de archivos, la actualización de generadores y la copia de seguridad
de los controles de calidad antes de aprobar la incorporación. Sin elección inicial,
la CLI devuelve `NEEDS_METHODOLOGY` sin escribir. Los perfiles confirmados conservan
su metodología; `standard` se acepta como alias antiguo de `odd`, con respaldos de
los archivos gestionados. Desactivar SDD requiere una migración revisada por separado.
Consulta la [guía de ODD](docs/ODD.md).

El flujo SDD es:

```text
/aikya-specify
/aikya-clarify
/aikya-plan
/aikya-tasks
/aikya-implement
/aikya-sdd-status
```

La especificación, el plan y las tareas requieren aprobaciones independientes.
La implementación y generación exigen **SPEC-NNN + TASK-NNN** activos, además del
consentimiento para los cambios concretos. Una especificación antigua aprobada no
autoriza otra tarea. SDD funciona en desarrollo, infraestructura y DevOps: es una
metodología, no un cuarto tipo de proyecto ni una arquitectura de aplicación sustitutiva.

Consulta [el flujo SDD, en inglés](docs/SDD.md) para esquemas, migraciones y límites de las evidencias.

### Idioma de la documentación

`en` es el idioma predeterminado; también está disponible `es` **únicamente para
los documentos Markdown de documentación viva dentro de `aikya/docs/`**.
La preferencia se almacena en `.aikya/docs-policy.json`.
La política del proyecto mantiene en inglés los agentes, skills, reglas, código y
documentación fuera de ese directorio. Cambiar el idioma de documentación existente
requiere una migración revisada por separado.

## 3. Componentes y estructura del proyecto

![Componentes de Aikya: comandos, agentes, skills, plantillas, políticas de modelos y GitHub Actions](docs/images/aikya-components.png)

### Código fuente del harness

| Ruta | Finalidad |
|---|---|
| `src/aikya/resources/commands/` | Fuente de los 28 comandos públicos de Claude Code. |
| `src/aikya/resources/engineering/agents/` | Definiciones del catálogo de agentes especialistas. |
| `src/aikya/resources/engineering/skills/` | Catálogo de skills técnicas. |
| `src/aikya/resources/project_template/` | Agentes base, skills, reglas y utilidades del harness para los proyectos. |

El código Python está organizado en `src/aikya/`: núcleo, herramientas, middleware, memoria, instalación, análisis, workflows, documentación, catálogos, routing y calidad. `pyproject.toml` define el paquete; los lanzadores instalados se generan desde una sola plantilla y mantienen su compatibilidad. En la raíz solo permanece `setup.py` como archivo Python de construcción.

Todos los planes, bugs y features generados por Aikya se guardan dentro de `aikya/docs/`: `plan/`, `bugs/` y `features/`. Los planes SDD permanecen en el dossier de su especificación dentro de `aikya/docs/specs/`.

### Archivos y directorios del proyecto

| Ruta | Finalidad |
|---|---|
| `.aikya/answers.json` | Decisiones técnicas para perfiles compatibles. |
| `.aikya/docs-policy.json` | Idioma de la documentación viva. |
| `.aikya/model-policy.json` | Política opcional de modelos por rol. |
| `.aikya/analysis/` | Inventario basado en evidencias de repositorios existentes. |
| `.harness/project-profile.json` | Perfil técnico normalizado y compatible con versiones anteriores. |
| `.harness/engineering-catalog.json` | Procedencia de los agentes y skills gestionados. |
| `.claude/agents/` y `.claude/skills/` | Especialistas y capacidades seleccionados según las tecnologías reales. |
| `.claude/rules/` y `CLAUDE.md` | Contratos de ingeniería e instrucciones del proyecto. |
| `aikya/docs/` | Documentación viva y registros de cambios por petición. |
| `aikya/scripts/` y `aikya/test/` | Utilidades internas y pruebas del harness. |
| `harness.json` | Controles de calidad configurados y comportamiento de `NOT_CONFIGURED`. |

Los monorepos nuevos pueden organizar las aplicaciones bajo `apps/`, con `packages/`
y `contracts/` compartidos. Un repositorio de una sola aplicación la mantiene en la raíz.
Los proyectos existentes no se reorganizan automáticamente.

## 4. Comandos de Claude Code

| Comando | Finalidad |
|---|---|
| /aikya-init | Entrevistar e inicializar un proyecto nuevo |
| /aikya-analyze | Analizar e incorporar un repositorio existente |
| /aikya-answers | Aplicar un perfil técnico declarativo validado |
| /aikya-doctor | Diagnosticar localmente los requisitos de SDK y del entorno de ejecución |
| /aikya-project | Planificar un proyecto o módulo nuevo |
| /aikya-infra | Planificar, generar con aprobación y validar infraestructura |
| /aikya-scaffold | Planificar y ejecutar generadores de aplicaciones aprobados para proyectos nuevos |
| /aikya-feature | Implementar una funcionalidad de alcance definido con pruebas |
| /aikya-bugfix | Investigar errores y aportar evidencias de regresión |
| /aikya-arc-review | Revisar la arquitectura y proponer ADR |
| /aikya-mobile-feature | Entregar funcionalidades móviles validadas |
| /aikya-skills-status | Consultar las Agent Skills registradas |
| /aikya-skills-plan | Evaluar las fuentes de skills externas y el impacto de su instalación |
| /aikya-install-skill | Instalar skills externas revisadas con aprobación explícita y registrar la comparación real |
| /aikya-quality | Ejecutar los controles de calidad disponibles |
| /aikya-docs | Mantener documentación viva respaldada por evidencias |
| /aikya-tests | Ejecutar pruebas específicas y de regresión |
| /aikya-docs-sync | Sincronizar los documentos afectados y la trazabilidad por petición |
| /aikya-verify | Validar los cambios técnicos y sus resultados |
| /aikya-models | Revisar la política opcional de selección de modelos |
| /aikya-tokens | Consultar el consumo de tokens y los costes estimados de API |
| /aikya-memory | Explorar memoria y código locales en un grafo HTML o mantener una vista en vivo |
| /aikya-specify | Crear una especificación y criterios de aceptación |
| /aikya-clarify | Resolver dudas y registrar aprobación explícita |
| /aikya-plan | Preparar el diseño técnico y la estrategia de pruebas |
| /aikya-tasks | Definir tareas vinculadas a requisitos y dependencias |
| /aikya-implement | Implementar la especificación y tarea activas con aprobación y alcance definido |
| /aikya-sdd-status | Consultar el estado SDD, la trazabilidad y las evidencias registradas |

Las actualizaciones respaldan los comandos antiguos verificados y los retiran
solo cuando sus sustitutos están disponibles. Los comandos personalizados se
conservan con un aviso para su revisión.

Las skills locales del proyecto también incluyen flujos base de funcionalidades,
corrección de errores, verificación, documentación y revisión de arquitectura.
Las herramientas externas opcionales no deben invocarse automáticamente.

## 5. Documentación, auditorías e historial de Git

![Trazabilidad documental en Aikya](docs/images/documentation-traceability-en.png)

SDD añade especificaciones versionadas en `aikya/docs/specs/<project_type>/SPEC-NNN/`,
con documentos Markdown y un `state.json` legible por máquinas. Este último almacena
el estado del flujo: la documentación no se limita exclusivamente a Markdown.

Los cambios técnicos relevantes actualizan las páginas `.md` afectadas de `aikya/docs/`
y crean un registro `changes/REQ-*.md` con **Cambios**, **Evidencias** y
**Documentos actualizados**. `docs_guard` comprueba los requisitos documentales.
Al incluirlos en los commits del proyecto, estos archivos aportan un historial y
diferencias revisables para auditorías y seguimiento de versiones.
Las consultas de solo lectura no requieren registros artificiales; no deben
registrarse prompts completos, secretos ni datos privados.

Todos los documentos Markdown generados por Aikya terminan con la línea exacta
`GENERATED BY AIKYA HARNESS`, independientemente de su ubicación. Esto incluye
informes de análisis, README de infraestructura, `CLAUDE.md`, agentes y skills. `indice.md`
enumera los Markdown que existen; se omiten informes sin datos que los respalden.
La guía de inicialización y el diagnóstico de herramientas quedan en `overview.md`.

| Ruta dentro de `aikya/docs/` | Contenido |
|---|---|
| `features/<funcionalidad-en-minusculas>/` | Alcance e implementación reales |
| `architecture/architecture-overview.md` | Arquitectura principal tanto para init como para analyze |
| `plan/testing.md` | Plan de pruebas seleccionado o evidencia de pruebas observadas |
| `tools/agents.md` | Agentes realmente disponibles en el proyecto |
| `tools/token-policy.md` | Política de contexto y tokens |
| `tools/skill-comparison.md` | Resultados reales de instalación externa; se crea únicamente mediante `/aikya-install-skill` |

Los documentos gestionados anteriores se migran con copias en `.harness/backup-docs-layout/`.
Los conflictos con documentos personalizados requieren revisión. Las rutas de ejecución
`.harness/` y `aikya/scripts/harness/` conservan sus nombres.

### Memoria de código local y HTML

La inicialización e incorporación aprobadas configuran el índice incremental y su
actualización automática por proyecto. Los hooks de sesión arrancan el observador
local en proyectos configurados; se detiene al terminar la última sesión. Para
trabajar con otros editores, mantén un observador explícito activo:

```text
/aikya-memory
/aikya-memory --refresh --open
/aikya-memory --watch --open
/aikya-memory --dry-run
```

El observador detecta archivos guardados, clases nuevas, renombrados y borrados.
Actualiza SQLite en `.harness/state/code-index/` y regenera
`aikya/docs/memory/view/index.html` junto con su `report.md`. Con `--watch --open`
también refresca la página mediante un visor temporal en localhost. El archivo
exportado sigue siendo una instantánea autónoma sin internet. No instala servicios
del sistema.

El informe utiliza por defecto el tema azul marino de la versión 2 y permite
cambiar a tema claro. El panel de fuentes, el explorador central y el inspector
combinan un grafo de conocimiento, una jerarquía de arquitectura basada en rutas
y un inventario con búsqueda. Los colores distinguen carpetas, archivos,
declaraciones y documentos/notas. Conserva filtros, selección y zoom al actualizarse
y respeta el movimiento reducido. Expande carpetas progresivamente, arrastra
objetos para organizarlos o arrastra el fondo para navegar. Las flechas mueven el
nodo enfocado y Escape cancela un arrastre. **Ajustar vista** encuadra el contenido;
**Restablecer distribución** libera las posiciones manuales de la vista actual.
Las posiciones pertenecen a la página abierta y se reinician al recargarla.

El movimiento también traza las conexiones nuevas y anima sus relaciones, hasta
80 conexiones simultáneas. Selecciona un componente o filtra un grafo denso para
acotar el efecto. Las relaciones sin dirección conocida usan un pulso sin recorrido
orientado. Con movimiento desactivado o reducido, todas las conexiones permanecen
estáticas. Este flujo visual representa evidencia del índice, no ejecución medida.

Inventario mantiene una vista exclusiva con 100 fuentes por página. Se indican los
elementos agrupados y los límites de dibujo; la búsqueda y el Inventario permiten
acceder a fuentes fuera del diagrama actual. Consulta el
[ejemplo sintético interactivo](aikya/docs/examples/aikya-memory-interactive.html). La arquitectura
muestra estructura verificable; el análisis de flujos de ejecución queda pendiente.

Después de actualizar Harness, regenera los informes con `/aikya-memory --refresh`
y vuelve a abrirlos. Reinicia un observador/servidor antiguo para cargar el nuevo
visor. El HTML integra sus scripts y estilos: recargar una instantánea antigua
no la actualiza. Se mantienen los controles de propiedad de informes personalizados.

Indexar y exportar no llama a modelos ni consume tokens de API; utiliza CPU y disco
locales. Las consultas posteriores a la IA conservan su consumo habitual. Python
funciona sin dependencias adicionales; el extra opcional fijado `code-index` añade
Java, JavaScript/JSX, TypeScript/TSX, C#, Go y Dart. Los demás lenguajes mantienen el
inventario por archivo. Un cambio de fuente invalida su vigencia sin reescribir
decisiones ni aprobaciones. La adopción preserva el `.gitignore` personalizado.
Consulta la [configuración, límites y ciclo de vida](aikya/docs/architecture/local-memory.md).

### Eficiencia de contexto y sesiones largas

El contexto de código se prepara localmente, verifica la fuente actual y entrega
un paquete de hasta 6.000 caracteres, sin fragmentos duplicados. Los hooks lo
aportan a los comandos de implementación; si faltan símbolos, se indica la
limitación y se permite una lectura acotada. ODD pequeño conserva su auditoría
REQ sin exigir un expediente vacío. Seguridad y aprobaciones siguen vigentes.

```sh
aikya-manage update --code-index dart     # Dart/Flutter y núcleo fijados
aikya-manage update --code-index all      # Todos los parsers opcionales fijados
aikya context --target . --query "change signIn" --allowed-file lib/login.dart
aikya analyze --target . --dry-run --summary --methodology odd
python aikya/scripts/harness/docs_guard.py preflight --session <host-session>
```

`--code-index none` es el valor inicial; una actualización sin esa opción conserva
la selección previa. Se instalan únicamente binarios verificados del release en
el intérprete administrado. Sin binario compatible, la operación falla antes de
activar el candidato. Python funciona sin extras; Dart, Java, JS/TS, C# y Go
requieren sus parsers. Kotlin, Swift y las demás extensiones conservan inventario.
Linux Alpine ARM64 y Windows ARM64 no tienen soporte binario verificado en este
conjunto de versiones; no se compilan parsers automáticamente.

La compactación es **manual por defecto**. Dentro de Claude Code:

```text
/compact Conserva el objetivo, decisiones, archivos afectados, estado ODD/SDD, pruebas pendientes y siguiente paso. Omite logs y explicaciones repetidas.
```

La opción por proyecto `aikya context-policy --target . --native-auto --window
200000 --approved` solicita una ventana nativa si el host la admite y conserva
ajustes personalizados. No cambia modelo ni effort. Los hooks de compactación
conservan referencias y checks pendientes; al continuar se recupera contexto
actual, sin reiniciar presupuestos ni crear aprobaciones. El aviso del 75% exige
una ventana efectiva y una medida frescas verificables; el porcentaje del modelo
no basta y, si faltan esos datos, el estado es N/D. Compactar también puede
consumir tokens y reconstruir caché; no recupera la cuota ya utilizada.

El loop opcional admite `max_total_turns` y `max_recorded_tokens`, acumulados entre
Implement y Review y conservados al reanudar. Cuenta las cuatro categorías,
incluida caché. El uso desconocido bloquea un límite activado; los tokens se
conocen al terminar la consulta, por lo que ésta puede exceder ese presupuesto.
Son límites del loop, separados de la cuota de 5 horas/semanal de Claude.

Los informes distinguen tokens observados, proxy estático y bytes locales.
El benchmark offline no acredita ahorro real de tokens ni de cuota; el experimento
con modelos requiere tareas equivalentes y un presupuesto revisado.

## 6. Agentes de ingeniería y Agent Skills

Aikya selecciona especialistas según las tecnologías reales: arquitectura, backend,
frontend, móvil, cloud, infraestructura, CI/CD, seguridad, pruebas y revisión de código.
**Planner** y **Orchestrator** ayudan con trabajos complejos que abarcan varias tecnologías
cuando es necesario. Los revisores actúan dentro de sus permisos y los especialistas
que modifican archivos respetan el alcance aprobado. Que un agente esté instalado no demuestra que se haya ejecutado.

### Skills externas opcionales

Las skills externas son opcionales y su fuente la elige el usuario. No se recomiendan ni instalan proveedores por defecto.

Consulta la disponibilidad y el impacto de la instalación desde Claude Code:

```text
/aikya-skills-status
/aikya-skills-plan
```

Tras revisar el plan, utiliza `/aikya-install-skill` con aprobación explícita.
Antes de instalar, revisa la procedencia, licencia, herramientas, acceso a red y
versión o commit. Los hooks de instalación de terceros no deben ejecutarse de forma silenciosa.

### Recursión: vistas conceptuales del flujo de trabajo

Los siguientes diagramas explican dos niveles de mejora. Son vistas conceptuales
basadas en la revisión de tareas y el mantenimiento del harness; no representan
comandos adicionales de Aikya ni una capacidad de automodificación autónoma.

La **recursión a nivel de tarea (Task-level recursion)** mejora la implementación
dentro de una tarea a partir de los hallazgos de verificación y los criterios de aceptación.

![Recursión a nivel de tarea](docs/images/task-level-recursion.png)

La **recursión a nivel de harness (Harnessing-level recursion)** mejora los agentes,
skills, plantillas y reglas reutilizables mediante cambios revisados y validados
para tareas futuras.

![Recursión a nivel de harness](docs/images/harnessing-level-recursion.png)

El siguiente diagrama amplía el modelo conceptual: la **recursión paralela** explora
harnesses candidatos y combina mejoras a partir de evidencias de ejecución;
la **recursión secuencial** transmite el harness refinado y las evidencias acumuladas
a través de pasos sucesivos de **Proponer → Probar → Componer (Propose → Probe → Compose)**.
Son patrones explicativos, no modos de ejecución integrados verificados.

![Escalado de la recursión mediante mejoras paralelas y secuenciales](docs/images/scale-task-level-recursion.png)

## 7. Nuestro enfoque de seguridad con Aikya

El flujo documentado de Aikya se centra en cambios de alcance definido,
aprobaciones explícitas y evidencias verificables:

- Conservar los archivos, agentes, skills e instrucciones personalizados del proyecto y proteger los secretos.
- Solicitar aprobación antes de instalar SDK, descargar dependencias y realizar operaciones externas.
- Exigir autorización independiente para despliegues, Terraform apply/destroy, escrituras en clústeres remotos y migraciones destructivas.
- Informar de los resultados reales: `PASS`, `FAIL`, `SKIPPED` y `NOT_CONFIGURED`.
- Distinguir los manifiestos y planes del estado verificado de la infraestructura en funcionamiento.
- Aplicar los requisitos documentales correspondientes y mantener la trazabilidad de los cambios.
- Revisar las fuentes externas opcionales antes de instalarlas y proteger las credenciales.

Estos controles orientan el comportamiento de Aikya; no certifican la seguridad
de una aplicación ni sustituyen la revisión de seguridad específica de cada proyecto.

## 8. Documentación adicional

- [Historial de cambios](CHANGELOG.md)
- [Guía de contribución](CONTRIBUTING.md)
- [Política de seguridad](SECURITY.md)
- [Código de conducta](CODE_OF_CONDUCT.md)
- [Contratos de los workflows de GitHub](.github/workflows.md)


### Plantillas de Aikya para SDD

SDD compone nueve roles a partir de la [biblioteca de Aikya](src/aikya/resources/aikya-template/docs/README.md): funcionalidad, API, base de datos, especificación, diseño, tareas, evidencias, revisión y reglas de ingeniería. Aikya conserva sus criterios de aceptación, trazabilidad y aprobaciones independientes. Los documentos se crean con contenido revisado. Consulta la [guía de plantillas SDD](docs/SDD_TEMPLATES.md) y la [galería completa de ejemplos generados](examples/documentation/generated/README.es.md).

## CLAUDE.md según el proyecto

Aikya selecciona instrucciones en inglés para desarrollo, infraestructura o DevOps y añade únicamente las guías del stack, estructura y metodología registrados. Los CLAUDE.md existentes se conservan. Consulta la [selección de plantillas y ejemplos](docs/CLAUDE_TEMPLATES.md).

## Biblioteca de plantillas de documentación

Hay 120 plantillas de Aikya fijadas a un commit disponibles sin conexión; la atribución original se conserva en THIRD_PARTY_LICENSES.md. La arquitectura utiliza `aikya/docs/architecture/architecture-overview.md`; los errores reales se añaden a `aikya/docs/bugs/bugs.md`. Los documentos requieren datos revisados y autorización. Consulta la [selección, ejemplos, licencia y compatibilidad](docs/DOCUMENTATION_TEMPLATES.md).

Aikya combina sus documentos generados con las plantillas de Aikya adecuadas según el comando, la metodología y el perfil del proyecto. Las features estándar incluyen criterios de aceptación observables; las secciones opcionales de diseño y pruebas utilizan datos reales aportados. Consulta la [composición contextual de plantillas](docs/CONTEXTUAL_TEMPLATE_COMPOSITION.md).


## Fases de ejecución y consumo

Todos los comandos comparten **Explore → Plan → Implement → Validate → Security → Review**,
con aplicabilidad proporcional y estados separados en inglés. La barra local muestra
la acción, modelo o ejecutor observado, contexto y cuotas opcionales de cuenta de
5 horas y 7 días. Los datos ausentes aparecen como N/D. Los tokens registrados usan
rutas de sesión autorizadas; no permiten calcular cuotas de cuenta. Las consultas
no crean documentos del proyecto. Se conservan las barras y hooks personalizados,
con una propuesta revisable cuando hay conflicto. Consulta la
[visibilidad de ejecución](docs/EXECUTION_VISIBILITY.md) y el
[plan completo en español](aikya/docs/plan/archive/harness-development/2026-10-23-odd-observabilidad.es.md).

## Agent loop opcional

Puedes activar explícitamente la ejecución acotada en /aikya-feature,
/aikya-bugfix o /aikya-implement. El SDK opcional de Claude ejecuta la tarea y Aikya
controla archivos autorizados, gates ODD/SDD, pruebas locales, revisión de solo
lectura y límites persistentes. No se inicia durante el onboarding ni instala el
SDK automáticamente. Consulta la [guía del agent loop](docs/AGENT_LOOP.md).

La memoria opcional project/private incorpora revisión explícita, migración de
checkout y extracción acotada de propuestas pendientes de aprobación. El control
de calidad exige modularizar los archivos de código modificados de más de 1.000
líneas; las funciones Python largas y los cuerpos repetidos generan avisos de
revisión. Consulta los [controles de seguridad y calidad](docs/SECURITY_CONTROLS.md)
para conocer qué se aplica automáticamente.

GENERATED BY AIKYA HARNESS
