# Plan: skills elegidas por el usuario, sin integraciones preseleccionadas

**Estado:** propuesta solicitada por el desarrollador; este documento no retira todavía código ni modifica los README.

**Objetivo:** eliminar de las superficies activas de Aikya las recomendaciones, catálogos y automatismos ligados a proveedores concretos. Conservar `/aikya-install-skill` para instalar únicamente la skill elegida expresamente por el usuario, así como los comandos de planificación e inventario.

**Arquitectura:** reutilizar el importador genérico existente; desacoplarlo de la lista de integraciones predefinidas y del onboarding. No construir otro instalador ni vincular el visor de memoria a una herramienta ajena.

## 1. Qué existe y qué hay que cambiar

La inspección del repositorio confirma que no hace falta empezar de cero:

- `src/aikya/catalogs/external.py` ya tiene `install_github_skill()` e `install_custom()`, con `--repo`, `--skill-path`, `--name`, `--ref`, `--commit` y autorización explícita. Copia una carpeta validada sin ejecutar sus scripts.
- Ese mismo módulo incluye `SOURCES`, `INSTALLERS`, `enabled_names()`, `planned_commands()` e `install_all()`, que vinculan el flujo a tres integraciones concretas. `install` sin selección recorre ese conjunto. La ruta genérica todavía incorpora `SOURCES` al registro aunque no se hayan elegido esas fuentes.
- `installation/facade.py` propone ese plan durante onboarding y puede ejecutar `install_all()` con `--external install`. La CLI `plan` del módulo externo tampoco utiliza actualmente una selección genérica para producir su vista previa.
- `catalogs/skills.py` contiene una lista `BUILTIN` con nombres concretos. El inventario debe depender de registros y archivos reales, no de esa lista.
- Los README en/es, instrucciones de comandos, textos documentales y algunas reglas de instalación contienen referencias específicas. Deben revisarse conjuntamente para que la siguiente generación no las vuelva a introducir.

Los nombres concretos y las rutas actuales son evidencia del estado anterior, no recomendaciones para el producto nuevo. Las atribuciones, licencias, registros históricos y documentos del usuario no se borran para ocultar esa historia.

## 2. Comportamiento final

| Acción | Resultado esperado |
|---|---|
| Instalar Aikya, `/aikya-init` o `/aikya-analyze` | Ninguna skill ajena seleccionada, recomendada ni instalada por defecto |
| `/aikya-skills-plan` sin selección | Solicitar repositorio, ruta y nombre; no proponer un catálogo cerrado ni clonar |
| `/aikya-install-skill` sin selección | Estado `NEEDS_SELECTION`, sin cambios ni descargas |
| `/aikya-install-skill` con selección revisada y autorización | Reutilizar el importador genérico; verificar fuente, commit cuando se aporte, carpeta y contrato `SKILL.md` |
| `/aikya-skills-status` | Mostrar lo realmente instalado/registrado, sea cual sea su nombre; no anunciar integraciones ausentes como pendientes |
| Actualizar un proyecto que ya tiene skills | Conservarlas y conservar sus registros; no desinstalar, reclasificar como propias ni invocarlas automáticamente |
| `/aikya-memory` | Funcionar con datos propios; ninguna instalación, recomendación o dependencia de esas skills |

Se mantienen los nombres de los comandos públicos. El único aumento del catálogo sigue siendo `/aikya-memory`, de 27 a 28; este desacoplamiento no elimina ni añade comandos.

Los README sustituirán la tabla de integraciones concretas por una explicación breve de la selección del usuario y de `/aikya-install-skill`. Las instrucciones internas y los documentos nuevos usarán un flujo genérico. El inventario puede mostrar el nombre real de una skill ya elegida: eso describe el proyecto del usuario, no vuelve a recomendarla.

## 3. Compatibilidad y qué se puede romper

| Riesgo identificado | Efecto de una retirada directa | Tratamiento propuesto |
|---|---|---|
| `install_all()` y selección implícita | Seguir instalando el conjunto anterior o fallar después de crear el proyecto | Eliminar la selección implícita; comprobar decisiones antes de cualquier escritura |
| `--external install` del onboarding antiguo | Automatizaciones que esperaban instalar el conjunto predefinido cambian de comportamiento | Rechazarlo en preflight con explicación para usar la instalación explícita; `skip`/`plan` se aceptan como compatibilidad neutral, sin nombres predeterminados |
| `--only <preset>` y llamadas a instaladores específicos | Scripts privados que dependen de esos atajos dejan de funcionar | Documentar la sustitución por `--repo`, `--skill-path`, `--name` y, cuando corresponda, `--commit`; no conservar un alias que siga ejecutando el instalador del proveedor |
| Skills instaladas y lock de versiones previas | Borrado accidental de datos, pérdida de procedencia o modificación de archivos del usuario | Leer el esquema anterior y preservar sus entradas y archivos; el nuevo registro solo añade la fuente realmente solicitada |
| Clasificación por `BUILTIN` | Confundir una skill existente con una propia de Aikya o con una recomendación pendiente | Clasificar desde inventario/lock/procedencia real; sin procedencia suficiente, mostrar local/no verificada |
| Documentos y runtimes copiados | Reaparición de recomendaciones antiguas después de actualizar/inicializar | Actualizar plantillas y migraciones gestionadas; preservar personalizaciones y contratos de runtime |
| Índice de código y visor | Dependencia accidental de una herramienta concreta | Exportación e índice propios sin llamar al gestor de skills |

**Valoración:** no se ha encontrado un impedimento crítico en la lectura del código. Sí hay cambios de comportamiento reales en los atajos predefinidos: eliminarlos sin transición puede romper automatizaciones. La ruta genérica ya existe y permite una migración incremental. Confirmar la valoración con las pruebas antes de afirmar compatibilidad completa.

La importación de una skill no garantiza que sus herramientas opcionales estén instaladas. Sus dependencias se informan y requieren una acción elegida por el usuario; no se convierten en nuevas instalaciones automáticas del harness.

## 4. Tareas de implementación

### S1: congelar y comprobar el flujo genérico existente

**Archivos:** `tests/test_v4.py`, `tests/test_v52.py`, nuevos fixtures genéricos bajo `tests/fixtures/user-skills/`; pruebas nuevas `tests/test_user_selected_skills.py`.

- [ ] Probar primero `install_custom()` y `install_github_skill()` con repositorios locales simulados y procesos Git controlados; ninguna descarga real ni ejecución de scripts del contenido importado.
- [ ] Cubrir selección incompleta, falta de autorización, nombre reservado `aikya-`, commit distinto al aprobado, ruta no contenida, symlink y destino personalizado; conservar las protecciones existentes.
- [ ] Añadir una prueba que falle cuando `install` sin selección produce cambios y otra cuando la vista previa genérica ignora los parámetros solicitados.
- [ ] Ejecutar las pruebas y guardar un commit verificable de contratos.

### S2: separar la elección del usuario de los presets

**Archivos:** `catalogs/external.py`, `catalogs/skills.py`, `installation/facade.py`, `installation/pipeline.py`, `cli/main.py` y contratos de importación/runtime afectados.

**Interfaces:** conservar las firmas públicas de `install_custom()` e `install_github_skill()`. El resultado sin selección añade `status='NEEDS_SELECTION'` y `writes=False`; no crea lock ni inventario. La vista previa genérica devuelve repositorio, ruta, nombre, ref/commit suministrados y destinos, sin red ni modificaciones.

- [ ] Retirar las listas preseleccionadas y los instaladores específicos. Reutilizar la validación de la solicitud genérica para `plan` e `install`, sin duplicar el copiado seguro.
- [ ] Neutralizar `enabled_names()`/`planned_commands()` si los consumidores aún necesitan sus contratos de importación: no devuelven recomendaciones. Retirar los consumidores antes de eliminar las funciones de compatibilidad.
- [ ] Validar flags de onboarding antiguos antes de instalar; rechazar la instalación implícita y mantener la creación ordinaria del proyecto sin selección de skills.
- [ ] Generar lock e inventario solo desde selecciones y resultados reales, sin inyectar fuentes predeterminadas. Preservar registros anteriores y archivos personalizados.
- [ ] Ejecutar pruebas dirigidas y verificar que las skills de ingeniería propias de Aikya siguen disponibles; guardar commit.

### S3: documentación e instrucciones neutrales

**Archivos:** `README.md`, `README.es.md`, `resources/commands/aikya-install-skill/SKILL.md`, `resources/commands/aikya-skills-plan/SKILL.md`, `resources/commands/aikya-skills-status/SKILL.md`, `documentation/pages_es.py`, `documentation/pages_en.py`, `documentation/bootstrap.py`, `installation/infrastructure.py` y recursos derivados donde la inspección encuentre referencias activas. Las rutas de módulos/recursos indicadas aquí son relativas a `src/aikya/`.

- [ ] Sustituir tablas, recomendaciones y recetas de proveedores por selección explícita del usuario; conservar `/aikya-install-skill`, `/aikya-skills-plan` y `/aikya-skills-status`.
- [ ] Revisar reglas de ignore y textos generados sin eliminar archivos existentes ni atribuciones. Una carpeta producida por una herramienta que el usuario instaló no se borra durante esta limpieza.
- [ ] Actualizar solo documentos gestionados con origen conocido y respaldos. Señalar conflictos personalizados sin reemplazarlos; mantener el pie y `indice.md`.
- [ ] Comprobar con fixtures de instalación nueva que no se reintroducen nombres/recomendaciones de presets, en ambos idiomas y metodologías; guardar commit.

### S4: migración, pruebas adversariales y distribución

**Archivos:** pruebas de skills, `tests/test_docs_layout.py`, pruebas de instalación/actualización y distribución existentes; informe observado en `aikya/docs/validation/USER_SELECTED_SKILLS.md`.

- [ ] Probar proyecto nuevo sin skills, proyecto existente con skills anteriores, instalación personalizada, ejecución sin Git, fallos de copia y lock antiguo; verificar preservación de archivos y procedencia.
- [ ] Probar global/project, ODD/SDD y en/es; el gestor actúa sobre el proyecto seleccionado, sin escanear ni borrar otros almacenes.
- [ ] Ejecutar la batería completa y los contratos de comandos/adaptadores; actualizar referencias de runtime conocidas sin aceptar personalizaciones como si fueran generadas.
- [ ] Comprobar wheel/sdist e instalación/actualización en Windows, Linux y macOS. Verificar que el índice y el HTML funcionan sin herramientas ajenas instaladas.
- [ ] Registrar incompatibilidades intencionales de atajos en changelog/README, pruebas observadas y procedimiento de recuperación antes de la PR.

## 5. Tiempo y coste

| Trabajo | Esfuerzo orientativo |
|---|---|
| S1: contratos y alcance de consumidores | 4–6 h |
| S2: desacoplamiento y selección explícita | 4–6 h |
| S3: README, instrucciones y generación | 4–6 h |
| S4: migración y pruebas | 6–10 h |
| Cierre de distribución e informe | 2–4 h |
| **Total adicional de este cambio** | **20–32 h; 2,5–4 jornadas de 8 h** |

El coste de ingeniería es `20–32 h × tarifa horaria acordada`. Como ejemplo aritmético, con 50 €/h serían 1.000–1.600 €; esa tarifa no se ha acordado ni representa un cobro de Aikya. La retirada no introduce una cuota ni un servicio de pago. El coste del asistente no se puede presupuestar con precisión sin modelo, uso y tarifa reales.

La animación del visor añade una reserva independiente de 4–8 h a su estimación anterior, para interacción, interrupción, teclado, movimiento reducido y revisión en navegador. Las dos ampliaciones juntas son **24–40 h adicionales**, sin volver a contar la implementación del índice ni el visor ya presupuestados.

El conjunto orientativo queda en 12–20 jornadas para índice base, visor, animación y este desacoplamiento. La ampliación multilenguaje sigue siendo una entrega adicional de 4–7 jornadas. La ampliación posterior V5 de estructura/recorridos Java tiene su reserva separada en el plan del visor y no está incluida en este total. Son estimaciones de trabajo técnico, no plazos garantizados ni consumo de tokens.

## 6. Orden recomendado y recuperación

Aplicar este desacoplamiento en commits separados dentro de `feat/local-code-index`, antes de cerrar las pruebas de onboarding del índice y del visor. Reutilizar los mismos fixtures y la matriz final para evitar duplicar infraestructura de pruebas. Este orden no requiere subagentes ni trabajo delegado.

Si la migración falla, detener la actualización antes de sustituir archivos gestionados y conservar la instalación anterior. Revertir únicamente los commits de esta ampliación si fuera necesario; no eliminar skills elegidas por el usuario como mecanismo de recuperación.

El siguiente paso es revisar este alcance con sus incompatibilidades intencionales. Este documento y el ejemplo HTML no realizan todavía la retirada del producto.

GENERATED BY AIKYA HARNESS
