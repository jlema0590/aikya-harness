# Especificación: ODD y visibilidad de ejecución en Aikya

Estado: implementación autorizada; avance registrado en el plan. Fecha: 23 de octubre de 2026.
Base revisada: c419faa, versión 6.1.1. Este documento está en español por petición del usuario.

## Objetivo

Sustituir standard por odd como metodología visible y predeterminada, conservar sdd,
y mostrar el progreso real de cualquier comando público de Aikya, el modelo que
participa en cada acción y métricas de contexto, sesión y límites de cuenta.

## Alcance acordado

- /aikya-init y /aikya-analyze presentan ODD y SDD antes de la primera escritura.
  ODD es la recomendación inicial, pero la elección debe quedar confirmada.
- Los perfiles ya configurados conservan la elección; los previews permiten ver
  ambas opciones y seleccionar explícitamente otra, con las migraciones aplicables.
- Compatibilidad: aceptar standard como entrada antigua y normalizarla a odd.
- Proyectos existentes: vista previa, respaldo y actualización de activos gestionados;
  preservar decisiones técnicas, documentos personalizados y proyectos SDD.
- Cubrir los 28 comandos actuales y exigir una receta de observabilidad al registrar
  otros. Incluir bootstrap global/project antes de que exista un perfil del proyecto.
- Usar seis nombres públicos de fase en inglés, incluso con documentación viva en
  español: Explore, Plan, Implement, Validate, Security y Review. Aplicar solo las necesarias.
- Separar fase, estado y actividad. Waiting representa espera de entrada/aprobación;
  Done representa cierre de ejecución. Ninguno es una fase adicional.
- Conservar Milkeles como única fuente externa de plantillas. Las referencias de
  plataforma utilizadas para instrumentar Claude Code no son nuevas plantillas.
- Usar los datos del runtime, con fuente y fecha. Un dato ausente se representa
  como no disponible, nunca como cero ni como una medición inferida de una política.

## Qué se mide

Claude Code documenta entradas de modelo, contexto y límites para su barra de estado,
y filas de subagentes con modelo resuelto cuando está disponible. Los límites son
opcionales y dependen de la cuenta. [Contrato oficial de la barra](https://code.claude.com/docs/en/statusline).

| Dato | Contrato de Aikya propuesto |
|---|---|
| Fase | Transición explícita de una operación; observaciones de herramientas se etiquetan como actividad, sin certificar una fase completa. |
| Estado | Pending, Running, Waiting, Done, Failed, Skipped, Blocked o Interrupted; no se marca éxito por finalizar una conversación. |
| Modelo por acción | Modelo observado del actor principal/subagente; política configurada se muestra aparte. Un proceso local Python no tiene modelo. |
| Contexto % | Ocupación de la ventana del modelo, distinta del consumo acumulado de sesión. |
| Tokens de sesión | Contadores disponibles de mensajes de la sesión y sus subagentes atribuibles; separar entrada, salida y caché, con cobertura parcial explícita. |
| Límite 5h % | Porcentaje de la ventana de cuenta reportado por el proveedor; no pertenece exclusivamente a este comando ni a este proyecto. |
| Límite 7d % | Porcentaje de cuenta y reinicio reportados por el proveedor; no se calcula sumando tokens locales. |
| Tokens últimos 7 días | Agregado opcional del proyecto y rutas autorizadas, con intervalo y cobertura; separado del límite de cuenta. |
| Presupuesto local % | Solo si existe un presupuesto explícito con unidad y denominador; nunca sustituye al límite oficial. |

No se deduce el modelo real a partir de inherit, Opus recomendado o el nombre de un
agente. No se atribuye un porcentaje de cuenta a una fase. No se suman porcentajes
entre modelos, comandos o sesiones. Si la correlación no permite repartir los tokens
entre acciones, se informa únicamente el agregado conocido de sesión/actor.

Los hooks documentan eventos de herramientas y subagentes; sus datos no prueban por
sí solos que una revisión o una prueba haya sido satisfactoria.
[Contrato oficial de hooks](https://code.claude.com/docs/en/hooks).

## Reglas ODD propias de Aikya

1. Explorar y resolver decisiones necesarias antes de escribir código.
2. Clasificar por comprensión, riesgo y capacidad de reanudar desde la petición y el
   diff; no imponer un número de archivos como único criterio.
3. Cambio pequeño: trabajo proporcional y bitácora REQ vigente; sin crear un paquete
   persistente de tareas innecesario.
4. Trabajo sustancial: expediente de feature con alcance revisado, aceptación,
   tareas, dependencias, resultados, evidencias y siguiente paso antes de modificar
   código. Reutilizar spec.md y las referencias Milkeles de especificación/tareas.
5. El estado estructurado y la proyección Markdown deben compartir revisión; comprobar
   cambios externos y contenido personalizado antes de reanudar o guardar.
6. SDD conserva sus tres aprobaciones y su motor. No convertir un proyecto SDD a ODD
   al resolver un valor predeterminado o refrescar su perfil.
7. No guardar prompts completos, secretos, mensajes del asistente ni salidas de
   herramientas en la telemetría. Registrar únicamente metadatos permitidos.

## Presentación y límites

| Fase pública | Código interno | Pregunta que responde |
|---|---|---|
| Explore | explore | ¿Qué existe y qué debemos entender? |
| Plan | plan | ¿Qué cambio y aceptación se proponen? |
| Implement | implement | ¿Qué cambio autorizado se está realizando? |
| Validate | validate | ¿Qué comprobaciones se están ejecutando? |
| Security | security | ¿Qué riesgos y controles de seguridad del cambio se están comprobando? |
| Review | review | ¿Qué candidato y consecuencias se están revisando? |

Una actividad concreta, como Reading project structure o Running unit tests, aporta
detalle dentro de una fase. Testing y Debugging no son fases nuevas: las pruebas
corresponden a Validate y la corrección de sus fallos puede volver a Explore o
Implement. El orden admite iteraciones y fases omitidas según la receta.

Security concentra la comprobación explícita de permisos, autenticación/autorización,
tratamiento de secretos, cambios de dependencias y configuración de infraestructura
cuando estén afectados. Explore y Plan identifican los riesgos antes de implementar;
la fase Security registra sus comprobaciones y resultados sobre el candidato vigente,
habitualmente después de Validate y antes de Review.

La receta exige Security cuando el cambio afecta controles de acceso, secretos,
permisos, dependencias o configuración sensible de infraestructura. En otros casos
puede ser Skipped con motivo registrado. Distinguir controles ejecutados, hallazgos
y cobertura no disponible. Done no significa ausencia de vulnerabilidades ni una
auditoría/certificación. Si falta un control exigido, informar Blocked o el resultado
parcial correspondiente; nunca darlo por ejecutado. No instalar escáneres ni consultar
servicios externos automáticamente. No leer archivos de secretos ni guardar sus valores.

Plan puede ser una decisión breve en memoria para trabajo pequeño. Review es
condicional al alcance y riesgo, con actor explícito y evidencia; no provoca una
delegación automática. La aprobación humana se muestra como Waiting, sin atribuirle
una revisión independiente completada. Done es resultado de la ejecución local y
no equivale a publicación o despliegue.

Primera superficie: Claude Code. La barra presenta comando, fase, actor, modelo y
métricas disponibles; un resumen de acciones amplía lo que no cabe en una línea.
No se promete modificar la interfaz de Codex, ChatGPT u otros clientes.

La vista Compact muestra la fase/estado actuales y una actividad breve, con uso en
una segunda línea si cabe. Details amplía historial, actores, fuentes y evidencias.
Las etiquetas públicas de fase/estado permanecen en inglés en ambas vistas.
El contador de tareas se muestra solo cuando existe una lista real; no se calcula
un porcentaje de avance dividiendo fases completadas entre seis.

Primera entrega funcional: ODD con continuidad, fases, modelos observados, contexto
y cuotas oficiales disponibles, con sus fallbacks y protección de configuraciones.
Las estadísticas históricas locales de siete días, presupuestos propios y reparto
de tokens por fase se dejan como ampliación posterior. No bloquean la cobertura de
comandos ni la visualización de la cuota oficial semanal cuando esté disponible.

La telemetría efímera usa caché local por proyecto, worktree, sesión e invocación;
no crea informes vivos durante consultas de solo lectura. Al cerrar cambios
autorizados, el resumen útil se integra en el REQ correspondiente bajo aikya/docs/.
Los datos cambiantes de uso de cuenta no se versionan en Git.

Una barra personalizada existente se conserva. La instalación presenta su conflicto
y una propuesta de integración; nunca ejecuta o concatena comandos arbitrarios para
combinar barras. Los fallos de visualización no desactivan los gates de Aikya.

## Aceptación

- AC-01: odd es el valor por defecto y standard funciona como alias antiguo; sdd e
  identificadores desconocidos mantienen su tratamiento explícito y validado.
- AC-02: migrar un perfil gestionado conserva las otras decisiones y genera respaldo;
  un conflicto personalizado se detecta antes de cualquier escritura parcial.
- AC-03: los 28 comandos tienen receta; una consulta no crea código, expediente de
  feature ni documentación viva. /aikya-init funciona desde registro global y project.
- AC-04: fases y estados se muestran en inglés. Una fase no ejecutada figura como
  Skipped/Pending en Details; Validate fallida mantiene Failed. Review completada
  exige revisión real y evidencia vinculada. Las vueltas a Explore/Implement
  conservan el fallo anterior e invalidan los resultados posteriores afectados.
- AC-05: se distinguen modelo configurado y observado, actor y ejecución local sin
  modelo; una falta de datos no hereda el modelo principal a un subagente.
- AC-06: contexto, sesión, límite 5h y límite 7d están etiquetados por separado; las
  métricas opcionales ausentes/expiradas/parciales tienen representación honesta.
- AC-07: streaming, repeticiones, compactación y subagentes no duplican el consumo;
  semanal local y semanal de cuenta conservan ámbitos distintos.
- AC-08: sesiones y worktrees simultáneos quedan aislados; la interrupción no produce
  éxito ni reanudación automática con evidencia obsoleta.
- AC-09: mostrar la barra no hace llamadas a modelos, redes, OAuth ni almacenes de
  credenciales; su ruta frecuente lee un snapshot acotado, no todos los historiales.
- AC-10: se conservan permisos, hooks, barra personalizada, locale, historial y gates;
  la auditoría Markdown mantiene el pie GENERATED BY AIKYA HARNESS.
- AC-11: Compact permite identificar fase, estado y actividad sin mostrar todas las
  fases futuras. Done/Waiting no son fases; no se inventa un porcentaje de avance.
- AC-12: Security tiene identidad propia, actor/ejecutor, controles, resultados y
  evidencias del candidato vigente. Un hallazgo conserva su estado y seguimiento;
  un control exigido no ejecutado no produce Done. Skipped requiere motivo según
  la receta y los cambios reales. Corregir el candidato invalida los resultados
  de seguridad afectados y exige repetir las comprobaciones pertinentes.

- AC-13: ambos onboardings ofrecen odd/sdd. Sin elección ni perfil previo válido,
  init/analyze devuelven NEEDS_METHODOLOGY sin escrituras. La elección explícita se
  conserva entre vista previa y adopción, y una elección SDD existente no se pierde.

## Observaciones de la validación previa

La CLI local responde con versión 2.1.308. Esta comprobación no verifica acceso a
modelos, autenticación, porcentajes de cuenta ni payloads reales de una sesión activa.
Aikya dispone de política de modelos y token_report.py, pero actualmente carece de
una máquina común de fases, barra propia y filtros temporales de consumo.

GENERATED BY AIKYA HARNESS
