# Plan de implementación: ODD y visibilidad de ejecución

> **Para agentes ejecutores:** plan preparado para ejecución nativa en esta conversación, con revisión independiente acotada al finalizar. El usuario ha autorizado ejecutar el plan completo, con elección explícita ODD/SDD en ambos onboardings. Las tareas usan casillas para registrar su avance.

**Objetivo:** convertir ODD en la metodología predeterminada compatible con perfiles antiguos y mostrar fases, modelos observados y consumo disponible para cada comando Aikya.

**Arquitectura:** separar el motor ODD de la observabilidad. Ambos publican eventos al mismo registro de ejecución; los adaptadores de Claude Code aportan datos observados y la barra solo presenta snapshots. SDD mantiene su motor y aporta sus eventos sin cambiar sus aprobaciones.

**Tecnología:** Python 3.10–3.13 y biblioteca estándar, hooks y barras documentados de Claude Code. Instrucciones del producto en inglés y documentación viva en en/es. Este plan y su especificación se entregan en español por petición expresa.

**Especificación:** [requisitos y aceptación](../../../design/harness/2026-10-23-odd-observabilidad.es.md).

## Confirmación de metodología

/aikya-init y /aikya-analyze ofrecen ODD y SDD antes de escribir. La selección
puede venir de la entrevista, --methodology o un perfil ya confirmado. Sin ella,
la CLI informa NEEDS_METHODOLOGY con las dos opciones y writes=false. Un perfil
previo conserva su elección y no obliga a repetir preguntas en cada refresh.
El cambio SDD → ODD continúa requiriendo migración revisada.

## Restricciones globales

- Conservar versión 6.1.1 durante este trabajo; no publicar, etiquetar ni hacer push por el plan.
- odd y sdd serán opciones visibles; standard será alias de lectura/entrada, no una tercera opción del menú.
- Mantener únicamente Milkeles como proveedor externo de plantillas y el pie Markdown exacto.
- Las fases no conceden permisos ni sustituyen evidencias, aprobaciones o controles existentes.
- Fases y estados visibles permanecen en inglés, independientemente del idioma de la documentación viva.
- No registrar prompts, secretos, respuestas completas, código o resultados crudos de herramientas.
- No consultar endpoints privados, extraer credenciales ni leer otros proyectos para obtener cuotas.
- Los ejemplos visuales contienen cifras simuladas, no métricas de esta conversación.
- Sin reemplazar configuraciones personalizadas ni reescribir el historial documental.

## Puntos prioritarios de revisión

1. Perfil antiguo sin metodología, standard explícito o sdd: normalización correcta y migración sin pérdida.
2. Init aún sin perfil, consulta informativa o comando cancelado: estados visibles sin artefactos de implementación ficticios.
3. Concurrencia, eventos tardíos y modelo cambiado durante una fase: correlación por actor e invocación y estado no obsoleto.
4. Streaming, compactación, caché, contadores incompletos y límites caducados: no duplicar ni inventar porcentajes.
5. Runtime/barra/hooks personalizados y cuentas sin cuotas: vista previa coherente, fallback útil y preflight antes de escribir.

## Lo que verá el usuario

Ejemplo conceptual, con cifras simuladas:

```text
AIKYA · /aikya-init · ODD · Implement · Running · Sonnet [observed]
Activity: Creating approved project files
Context: 28% · Session: 91k recorded tokens · Account 5h: 34% · Account 7d: 62%
```

Detalle del mismo comando:

| Fase | Estado de ejemplo | Modelo/ejecutor |
|---|---|---|
| Explore | Done | Modelo observado del actor |
| Plan | Done | Actor que preparó el alcance autorizado |
| Implement | Running | Modelo observado o Python local, según la acción |
| Validate | Pending | Comprobaciones locales y actor coordinador separados |
| Security | Pending | Ejecutor de los controles de seguridad pertinentes al bootstrap |
| Review | Skipped | No se ha invocado un revisor para este ejemplo |

## Simplificación de fases y presentación

Mantener seis fases públicas: **Explore → Plan → Implement → Validate → Security → Review**.
Son categorías de trabajo de Aikya, no estados nativos que Claude Code certifique.
No todas se ejecutan en cada comando y el flujo puede volver a una fase anterior.
Explore cubre lectura e investigación; Implement incluye el cambio autorizado;
Validate reúne pruebas y otras comprobaciones funcionales/estructurales.
Security comprueba los riesgos y controles de seguridad afectados. Review inspecciona el candidato
vigente con actor y resultado identificados, cuando resulte necesario.

Security registra permisos, autenticación/autorización, secretos, cambios de
dependencias y configuración sensible de infraestructura según el cambio. Sus
riesgos se identifican desde Explore/Plan; la comprobación final se realiza sobre
el candidato actual, habitualmente tras Validate y antes de Review. Reutilizar los
controles existentes y disponibles; añadir la fase no implica instalar escáneres,
consultar servicios o generar un informe de auditoría vacío.

Separar la fase de su estado: **Pending, Running, Waiting, Done, Failed, Skipped,
Blocked, Interrupted**. Waiting puede indicar una pregunta, una aprobación o una
dependencia. Su motivo se muestra en la actividad. Done cierra una fase/ejecución,
sin añadir Close, Complete o Deploy a la lista de fases obligatorias.

- **Compact, predeterminado:** comando, fase, estado y modelo; actividad breve cuando
  aporte información y segunda línea de consumo según el ancho disponible.
- **Details:** historial, fases omitidas/pendientes, actores, fuentes y evidencias;
  ampliar la consulta de estado existente sin añadir otro comando público.
- Plan no exige un archivo para cambios pequeños; basta una decisión de alcance
  breve y observable. El expediente persistente se reserva al trabajo sustancial.
- Review no obliga a lanzar un agente adicional en cada consulta o comando pequeño.
  La espera de aprobación es Waiting y no una revisión independiente completada.
- Security es exigible para cambios en acceso, secretos, permisos, dependencias o
  infraestructura sensible; cuando no aplica, usar Skipped con motivo. Registrar
  cobertura y hallazgos reales; un control requerido sin ejecutar permanece Blocked
  o parcial, nunca Done. Done no certifica ausencia de vulnerabilidades.
- Un fallo puede llevar de Validate a Implement o de Review a Explore; conservar
  la evidencia del fallo y marcar obsoletos los resultados afectados por el cambio.
- Un hallazgo de Security puede volver a Plan/Implement; repetir los controles
  afectados después de corregir y conservar la evidencia previa como historial.
- Añadir una actividad útil, por ejemplo Reading project structure, Writing tests
  o Running unit tests. Testing/Debugging no requieren nuevas fases públicas.
- Usar un contador de tareas solo si hay un worklist real; no convertir la posición
  en una secuencia de fases en un porcentaje aparente de avance.

Ejemplos de recetas proporcionales:

| Uso | Receta orientativa |
|---|---|
| /aikya-init | Explore → Plan → Implement → Validate → Security para los permisos/configuración generados; Review cuando proceda |
| Feature sustancial | Explore → Plan → Implement → Validate → Security → Review, con aplicabilidad registrada e iteraciones |
| Bug pequeño | Explore → Implement → Validate; Plan breve integrado, Security según impacto y Review condicional |
| /aikya-architecture-review | Explore → Review; incluir Security si hay límites de confianza o controles afectados; sin Implement no autorizado |
| /aikya-tokens | Explore → Validate; Security/Implement omitidas con motivo, resultado final Done |

La barra real se ajustará al ancho. Valores sin fuente se mostrarán N/D; un valor
caduco mostrará su antigüedad. Las fases completadas indican ejecución observada,
no una certificación semántica del resultado. Una revisión independiente solo se
marca completada si hubo revisor y resultado referidos al candidato vigente.

La [interfaz oficial](https://code.claude.com/docs/en/statusline) permite barra local,
modelo/contexto y cuotas opcionales; la procedencia y el ámbito se preservan en el
adaptador. Su disponibilidad se comprueba por capacidad, no solo por versión.

## Orden y estimación

La primera entrega funcional reúne ODD, continuidad, fases, modelo observado,
contexto y cuotas oficiales 5h/7d disponibles. Se aplazan estadísticas históricas
locales, presupuestos locales y reparto de tokens por fase hasta verificar que
las fuentes permiten atribuirlos con calidad. Las cuotas oficiales disponibles
y los valores N/D siguen incluidos en la primera entrega.

Estimación de esfuerzo para un desarrollador familiarizado con el repositorio;
no es una fecha comprometida ni un coste de API. Se ajustará tras validar fixtures
reales sanitizados y compatibilidad del cliente.

| Entrega | Esfuerzo aproximado | Dependencia |
|---|---:|---|
| 1. Compatibilidad standard → odd | 6–10 h | Ninguna |
| 2. Estado común de ejecución, incluida Security | 8–12 h | Entrega 1 |
| 3. Motor ODD y continuidad | 10–16 h | Entregas 1–2 |
| 4. Modelos y consumo observado; ampliaciones locales separadas | 8–12 h | Entrega 2 |
| 5. Barra e instrumentación de comandos | 8–12 h | Entregas 2–4 |
| 6. Migraciones, pruebas integradas y documentación | 8–12 h | Entregas anteriores |
| Instrumentación y pruebas adicionales de Security | 4–8 h | Integradas en entregas 2, 5 y 6 |
| **Total orientativo actualizado** | **52–82 h** | Aproximadamente 7–11 jornadas de 8 h |

Entregas pequeñas y comprobables en una misma rama de trabajo. La compatibilidad
ODD y el panel comparten contexto de ejecución, pero se validan por separado para
localizar fallos. Mostrar la barra no necesita llamadas adicionales a modelos;
los agentes utilizados por el trabajo sí mantienen su consumo normal.
El rango incorpora la instrumentación básica de Security con controles ya disponibles;
no incluye desarrollar escáneres o contratar auditorías. Se reestimará el núcleo tras
separar las ampliaciones y confirmar los controles reales del proyecto.

## Entrega 1: metodología y compatibilidad

**Archivos:** crear methodology.py y tests/test_methodology_migration.py; modificar
install.py, aikya_cli.py, aikya_analyze.py, claude_templates.py,
documentation_workflows.py, doc_bootstrap.py, aikya_setup.py y skills de onboarding.

**Interfaz:** normalize_methodology(value: str | None) -> str devuelve odd para None
 o standard, conserva odd/sdd y rechaza otros valores sin modificar la entrada.
Los previews identifican la metodología antigua y la acción propuesta.

- [x] Escribir pruebas de perfiles nuevos/antiguos para desarrollo, infraestructura y DevOps; verificar odd por defecto y sdd conservado.
- [x] Ejecutar las pruebas y comprobar fallo por ausencia de la normalización.
- [x] Centralizar valores predeterminados, CLI, renderers y selección de workflows; mantener standard solo como compatibilidad.
- [x] Añadir migración de perfiles gestionados y answers con respaldo, vista previa consistente y detección de conflictos antes de escribir.
- [x] Verificar que no cambia ninguna decisión técnica fuera de methodology, ni se desactiva SDD mediante un refresh.
- [x] Ejecutar tests de migración, onboarding y SDD; guardar un commit local revisable.

No hacer una sustitución global de texto: los históricos, hashes de versiones
anteriores y fixtures de compatibilidad necesitan conservar standard.

## Entrega 2: estado común de ejecución y recetas

**Archivos:** crear execution_state.py, command_workflows.py,
execution_observer.py y tests/test_execution_state.py; conectar
request_docs.py, stop_docs.py y el registro BOOTSTRAP_COMMANDS de aikya_setup.py.

**Interfaces:** start_run(context: dict, command: str) -> dict;
record_event(context: dict, event: dict) -> dict;
read_snapshot(context: dict) -> dict;
recipe(command: str, methodology: str) -> dict.
Context incluye raíz/worktree, session_id, run_id y actor_id. Los eventos tienen
identificador estable, fase, estado, fuente y momento. Ningún valor concede permisos.

- [x] Probar dos sesiones y dos worktrees concurrentes, eventos duplicados/tardíos, escritura interrumpida y datos inválidos.
- [x] Comprobar fallos iniciales; implementar almacenamiento atómico acotado y revisión optimista para evitar pérdidas concurrentes.
- [x] Definir fases internas explore, plan, implement, validate, security y review, con etiquetas públicas Explore, Plan, Implement, Validate, Security y Review. Estado separado: pending, running, waiting, completed, failed, skipped, blocked e interrupted; completed se presenta como Done.
- [x] Probar que Waiting y Done no se añaden como fases y que los nombres se conservan en inglés con locale en/es.
- [x] Probar retornos Validate → Implement y Review → Explore, conservando fallos históricos e invalidando evidencia posterior obsoleta.
- [x] Probar Security → Implement → Security, control requerido no disponible, hallazgos y exclusión con motivo; nunca convertir ausencia de comprobación en éxito.
- [x] Registrar aplicabilidad y señales de inicio/fin por comando. La espera de respuesta/aprobación no es fallo ni éxito.
- [x] Correlacionar invocaciones confirmadas; mencionar /aikya-init en una consulta no debe iniciar una ejecución.
- [x] Separar actividad observada de fase declarada y resultado validado; Read o Bash no prueban por sí solos investigación, test o revisión satisfactoria.
- [x] Resolver caché local por proyecto/sesión/invocación, incluso antes de existir un proyecto inicializado. Consultas de solo lectura no escriben documentación viva.
- [x] Verificar recetas para los 28 comandos y aliases, cancelación y recuperación de procesos; guardar commit local.

No imponer las seis fases a todos los comandos. /aikya-tokens puede realizar
lectura, agregación y cierre sin implementación ni revisión. /aikya-init puede
esperar decisiones antes de crear archivos. El registro transitorio no usa el
prompt completo y no activa automáticamente un escritor o un subagente.

## Entrega 3: motor ODD y reanudación

**Archivos:** crear odd_engine.py y tests/test_odd_engine.py; ampliar
methodology.py, aikya_router.py, documentation_workflows.py y skills
feature/bugfix/mobile-feature/tests/implementación pertinentes.

**Interfaces:** classify_work(facts: dict) -> dict;
prepare_feature(root, feature_id, reviewed_input, approved=False) -> dict;
advance_task(root, feature_id, task_id, result, evidence, expected_revision) -> dict;
resume_feature(root, feature_id) -> dict.

- [x] Probar cambio pequeño sin expediente, trabajo sustancial con tareas previas al código y petición informativa sin modificaciones de proyecto.
- [x] Probar alcance nuevo, dependencias, evidencia retirada, diff cambiado y edición externa del expediente; comprobar fallos antes de guardar.
- [x] Implementar clasificación basada en comprensión, riesgo y continuidad, con motivo registrado; las heurísticas del router son asesoramiento.
- [x] Reutilizar features/<slug>/spec.md para objetivo/aceptación y proyección de tareas; estado versionable en el mismo expediente, state.json, sin pie Markdown.
- [x] Usar las referencias Milkeles agent-task-specification y task-plan; reutilizar normalización de rutas, protección de índices y escritura segura.
- [x] Vincular tareas a requisitos y evidencia revisada; actualizar siguiente paso tras transiciones. Reanudar solo después de reconciliar estado, documento y cambios reales.
- [x] Emitir eventos al registro común; no habilitar automáticamente revisores, modelos auxiliares, despliegues o cambios remotos.
- [x] Mantener independiente el motor SDD. Pasar de ODD a SDD requiere elección explícita y migración revisada del contexto vigente.
- [x] Ejecutar la suite de ODD, documentación y gates SDD; guardar commit local.

La reanudación local no requiere Engram. El expediente mantiene datos revisados,
no copias literales de solicitudes que puedan contener información sensible.
La bitácora REQ y el índice existentes siguen formando parte de la auditoría.

## Entrega 4: modelo real y consumo

**Archivos:** crear runtime_metrics.py y tests/test_runtime_metrics.py; ampliar
token_report.py, model_capabilities.py y skills aikya-models/aikya-tokens.

**Interfaces:** normalize_runtime_payload(payload: dict, now) -> dict;
aggregate_usage(paths, start_utc=None, end_utc=None, session_id=None) -> dict;
resolve_actor_model(configured, observed) -> dict.
Cada métrica incluye valor opcional, unidad, ámbito, fuente, observed_at y cobertura.

- [x] Probar payload vacío, valores null, cero real, tipos inválidos, alias inherit, cambio de modelo y subagente sin modelo resuelto.
- [x] Probar snapshots streaming, relectura de historiales, rotación, sesión principal con subagentes y timestamps fuera de intervalo; verificar fallo inicial de los nuevos comportamientos.
- [x] Adaptar model.id y datos de actor resuelto cuando existan; conservar configurado/observado por separado. Un ejecutor Python/Bash local se muestra sin modelo.
- [x] Usar context_window.used_percentage para contexto; no tratar los contadores de la ventana como acumulado de sesión.
- [x] Normalizar rate_limits.five_hour y seven_day, sus porcentajes y reinicios cuando existan; no derivar cuotas con precios, tokens o tipo de modelo.
- [x] Agregar tokens del intervalo/sesión desde fuentes de proyecto autorizadas; separar input/output/cache y declarar registros sin datos o correlación parcial.
- [x] Ampliación posterior: para los últimos 7 días del proyecto, usar timestamps y límites de intervalo explícitos. No presentar ese agregado como límite semanal de toda la cuenta.
- [x] Suprimir cuotas expiradas y señalar snapshots antiguos. Conservar límites por modelo separados solo si el runtime los proporciona explícitamente.
- [x] Ampliación posterior: implementar presupuestos locales solo con denominador configurado y etiqueta propia; no presentarlos como cupos contratados.
- [x] Verificar privacidad, deduplicación y ausencia de red/credenciales/modelos en el adaptador; guardar commit local.

## Entrega 5: barra y conexión con todos los comandos

**Archivos:** crear aikya_statusline.py, aikya_subagent_statusline.py,
template/.claude/hooks/execution_status.py y tests/test_execution_ui.py;
modificar skills públicas, aikya_cli.py, aikya_session.py,
template/.claude/settings.json y funciones de mezcla/preview de configuración.

**Interfaces:** render_status(snapshot: dict, metrics: dict, width: int) -> str;
render_actor_rows(payload: dict, snapshot: dict) -> list[dict].
Las funciones de presentación no ejecutan herramientas ni modifican el proyecto.

- [x] Probar salida normal/estrecha/sin color, texto de control malicioso, datos ausentes y actores en paralelo; comprobar fallos iniciales.
- [x] Implementar Compact y Details; conservar etiquetas inglesas y priorizar comando/fase/estado/modelo en pantallas estrechas. No mostrar fases futuras ni porcentajes de avance inventados en Compact.
- [x] Conectar fases explícitas al comienzo/fin de acciones reales en CLI y skills; los hooks aportan actividad y correlación, no éxito semántico.
- [x] Vincular subagentes por ID mediante eventos disponibles. Evitar asignarles el modelo principal cuando falta observación propia.
- [x] Integrar statusLine y, si existe capacidad, subagentStatusLine. Conservar una salida textual de detalle para clientes o versiones que no soporten la barra.
- [x] Distinguir aviso de cierre de revisión independiente y de aprobación humana. Rechazo de un gate o test mantiene failed/blocked con evidencia correspondiente.
- [x] Mostrar Security con actor/ejecutor observado, controles y hallazgos acotados; mantener secretos fuera de los registros y no lanzar escáneres ni subagentes por el mero hecho de mostrar la fase.
- [x] Añadir módulos a ambos runtimes global/project; cubrir init antes del perfil, aliases e invocaciones internas sin contar dos veces el comando padre.
- [x] Preservar barra y hooks personalizados. Crear propuesta de configuración visible cuando hay conflicto; no sobreescribir ni encadenar comandos arbitrarios.
- [x] Mantener el renderer local, acotado y sin llamadas LLM; usar snapshots y agregación autorizada fuera de su ruta frecuente.
- [x] Ejecutar smoke de los 28 comandos con adaptadores de prueba que no instalan herramientas ni contactan servicios; guardar commit local.

El inicio/fin de subagentes aporta metadatos del actor; la inspección de una
respuesta no sustituye su evidencia. [Hooks oficiales](https://code.claude.com/docs/en/hooks).
La visualización nunca oculta ni convierte en éxito un error del gate documental.

## Entrega 6: migraciones, validación integral y documentación

**Archivos:** ampliar install.py, aikya_setup.py, aikya_analyze.py,
docs_migration_hashes.py y CI; crear tests/test_odd_observability_integration.py,
docs/ODD.md, docs/EXECUTION_VISIBILITY.md y ejemplos sanitizados. Actualizar ambos
README, inventario y guías relevantes.

- [x] Probar instalación nueva, registro global/project y adopción existente en los tres tipos y ambos idiomas.
- [x] Probar actualizaciones desde las versiones conocidas, perfiles standard/sin campo/sdd y settings personalizados; comprobar preservación byte a byte ante conflictos.
- [x] Asegurar preflight conjunto de consumidores, datos y hooks; no actualizar la mitad del runtime si otro activo acoplado está personalizado.
- [x] Probar dry-run sin escrituras en el proyecto, hooks duplicados, doble sesión, compactación, reinicio, cancelación y rollback con respaldo.
- [x] Validar fixtures sintéticos del contrato oficial publicado; ausencia de cuotas o modelo no se considera fallo ni permiso para consultar credenciales.
- [ ] Comprobar la barra en una sesión real de Claude Code con la cuenta del desarrollador como control de activación; no se ha capturado aquí una sesión ni sus cuotas.
- [x] Ejecutar la suite completa en Python 3.10–3.13, catálogo Milkeles, metadatos de agentes, gates, presupuestos de contexto, smoke de perfiles y contratos de versión.
- [x] Revisar que los textos y logs distinguen disponible, no observado, parcial, estimado y completado; conservar locale y pie Markdown.
- [x] Verificar Security aplicable/omitida, fallida, incompleta y repetida tras corregir el candidato; conservar permisos y evitar afirmaciones de certificación o ausencia de vulnerabilidades.
- [x] Revisión independiente acotada del diff y escenarios de pérdida de datos/correlación; corregir hallazgos con reproducción y regresión.
- [x] Entregar ejemplos reales sanitizados de init, analyze, feature, consulta y SDD, con/sin cuotas y con múltiples actores; documentar fallback y límites.
- [x] Guardar commit local y evidencias de validación; publicación separada, sin push automático.

## Criterios de cierre y despliegue gradual

Primero validar compatibilidad y observabilidad sin cambiar decisiones del proyecto;
después activar el comportamiento ODD en instalaciones de prueba. La telemetría
puede desactivarse sin desactivar ODD ni SDD. Su fallo no reduce los controles de
seguridad o documentación existentes.

El registro dinámico no añade Markdown por cada refresco. Los resultados útiles
se incorporan al REQ de un cambio autorizado; las consultas y barras de uso no
crean auditorías ficticias. La exposición semanal oficial depende del runtime/cuenta:
N/D y su motivo son resultados aceptables cuando el dato no está disponible.

Para considerar terminado el alcance completo deben cumplirse AC-01 a AC-13 de la
especificación, con resultados y limitaciones documentados. El tiempo y consumo
finales se medirán durante la implementación; los rangos anteriores son estimaciones.
El núcleo puede entregarse antes de las ampliaciones locales si las métricas
correspondientes quedan identificadas como no implementadas; las cuotas oficiales,
el modelo observado y el contexto mantienen su contrato de disponibilidad desde
esa primera entrega. No presentar el núcleo como el alcance completo terminado.

## Resultado local y evidencias

Implementación local terminada y revisión independiente realizada. Consulta
[la validación](../../../validation/archive/2026-10-22/ODD_EXECUTION.md): 407 pruebas por intérprete,
48 escenarios de onboarding, seis migraciones/reinstalaciones y seis ciclos SDD.
Las dos incidencias P2 de la revisión se corrigieron con regresiones: resultados
antiguos tras cambiar el candidato y atribución del modelo al actor equivocado.
Los commits por entrega se consolidan en un único commit local revisable de este
cambio. Las estadísticas por intervalo y presupuestos locales también están
implementados con fuente explícita, aunque se habían previsto como ampliaciones.

El control pendiente es la activación dentro de una sesión real de Claude Code.
Las pruebas de contrato usan datos sintéticos sanitizados; no se han medido cuotas,
facturación ni tokens reales de la cuenta de esta conversación. La ausencia de
esas mediciones no se presenta como cero. No hay reparto de tokens por fase.

## Ejemplos de recorrido por escenario

Los [doce casos de onboarding](../../../examples/2026-10-23-onboarding-odd-sdd.es.md) muestran
ODD/SDD para proyectos nuevos/existentes de desarrollo, infraestructura y DevOps.
Distinguen fases propuestas, estados actuales del analizador/motor SDD, esperas,
fallos e interrupciones. Son recorridos explicativos con métricas simuladas; la matriz automatizada valida
los onboardings locales. El [ejemplo ODD generado](../../../../../examples/odd/development/lookup/README.md)
incluye tareas, estado y dos comprobaciones reales sobre un proyecto sintético.

GENERATED BY AIKYA HARNESS
