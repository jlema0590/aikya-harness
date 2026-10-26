# Plan de adopción de ideas verificadas de Gentle Shell

Propuesta posterior a la implementación del agent loop. El usuario ha solicitado
esta comparación y plan; no se implementan estas ampliaciones en el cambio actual.

**Objetivo:** mejorar revisión, visibilidad y continuidad de Aikya aprovechando
patrones verificados de Gentle Shell, conservando Claude Code y los motores ODD/SDD.
**Base:** [comparación y fuentes fijadas a 05065e7](../../../../../docs/research/GENTLE_SHELL_COMPARISON.es.md).
**Arquitectura:** módulos Python locales y adaptadores opcionales. Ninguna extensión
de Pi se copia ni pasa a ser una skill de Claude por cambiar su nombre.

## Restricciones compartidas

- Mantener la instalación base sin SDKs ni servicios externos automáticos.
- Conservar las 27 entradas públicas; priorizar opciones de comandos existentes.
- Mantener fases English, documentación de producto English y documentos vivos en
  el en/es confirmado; todo Markdown generado termina con el pie obligatorio.
- Ningún recuerdo, clasificador, estado de UI o recibo concede aprobación SDD ni
  autorización de publicación. La receta actual del loop mantiene su revisión
  hasta validar expresamente una política proporcional alternativa.
- Validar primero el smoke real del agent loop en el entorno elegido por el usuario.
  No extrapolar rendimiento/coste a partir de fixtures locales o benchmarks ajenos.

## GS-1 — Riesgo explicable y revisión proporcional

Crear review_risk.py y tests/test_review_risk.py. Consumir el diff real y rutas
cambiadas, incluyendo archivos sin seguimiento cuando pertenezcan al candidato.
Devolver una clasificación, motivos por ruta y comprobaciones requeridas como
información; los motores existentes siguen decidiendo qué gates deben cumplirse.

- [ ] Escribir pruebas de autenticación/permisos, migraciones de datos, persistencia,
  infraestructura destructiva, cambios meramente documentales y contexto desconocido.
- [ ] Implementar una tabla de reglas revisable; contexto desconocido exige revisión
  conservadora y un cambio pequeño en una zona crítica no se considera trivial.
- [ ] Ejecutar esas pruebas y una muestra de casos reales anotados manualmente.
- [ ] Proponer integración en command_workflows.py y agent_loop.py sin reducir
  automáticamente Security/Review. Solo una política posterior aprobada puede
  cambiar la aplicabilidad; registrar el motivo y comparar omisiones/falsos positivos.
- [ ] Guardar una entrega local revisable con evidencia de clasificación, sin activar
  Auto ni solicitar a un modelo que conceda permisos.

## GS-2 — Recibo del candidato y cierre condicionado

Crear review_receipts.py, tests/test_review_receipts.py y documentación English.
Extender la evidencia del loop con versión de esquema, identidad de proyecto/worktree,
huellas del candidato, configuración de checks, revisión y estado de vigencia.
El recibo es un registro verificado local; no llamarlo firma criptográfica sin
implementar identidad/clave, validación y un modelo de confianza aparte.

- [ ] Probar cambios entre verificación y cierre, evidencia alterada, HEAD/índice
  cambiados, archivos nuevos, recibos duplicados y cortes antes/después de publicar.
- [ ] Reutilizar los checkpoints recuperables del loop; separar estado autoritativo
  y proyecciones, invalidar recibos antiguos y preservar versiones personalizadas.
- [ ] Integrar lectura de recibos en /aikya-verify y /aikya-sdd-status. Registrar que
  un recibo de tarea no es verificación completa de requisitos SDD.
- [ ] Verificar dos invocaciones concurrentes y recuperación en otro checkout con
  reconciliación explícita. Entregar antes de diseñar gates de publicación.

## GS-3 — Vista única de estado y perfiles de sesión

Modificar aikya_statusline.py y añadir una vista de lectura en aikya_cli.py;
si el perfilado lo requiere, crear execution_profiles.py. Proyectar el estado ya
existente de expedientes y ejecución, sin un segundo Todo persistente que compita
con ODD/SDD. Preferir una salida CLI/JSON útil antes de una nueva interfaz TUI.

- [ ] Probar estado ausente/obsoleto, actor concurrente, cancelación, modelos
  heredados/desconocidos y consumo sin datos; no asignar el modelo principal a un hijo.
- [ ] Mostrar tarea, fase, bloqueo, candidato y evidencia vigentes con enlaces.
- [ ] Si se añaden perfiles, separar configuración por rol de observación real y
  fijar el perfil a la invocación. Cambiar el global no cambia una tarea ya iniciada.
- [ ] Mantener cuotas del proveedor, tokens observados y estimaciones económicas
  como métricas distintas. El panel no realiza inferencias ni llamadas al modelo.

## GS-4 — Jobs y monitores opcionales

Crear background_jobs.py y tests/test_background_jobs.py únicamente cuando haya
un caso de uso aprobado, como esperar una build larga o un resultado de CI.
Reutilizar las restricciones de argv, timeout y grupos de procesos del loop.

- [ ] Probar notificación duplicada/tardía, cancelación del árbol de procesos,
  reinicio del controlador, salida infinita y superación de límites de concurrencia.
- [ ] Empezar con un job por ejecución y cola acotada; resultado terminal solo una
  vez y sin convertir la salida de un comando en autorización o instrucciones.
- [ ] Separar notificación de aceptación del resultado. Un monitor de texto no
  certifica una prueba y no debe activar reintentos ni nuevos agentes por sí solo.
- [ ] Requerir autorización específica para red, procesos duraderos y despliegues;
  no iniciar servicios de fondo desde onboarding ni hooks de observación.

## GS-5 — Proveedor de memoria externo, solo si hace falta

Mantener agent_memory.py como opción local. Si hay una necesidad de equipo o
consulta externa concreta, diseñar memory_provider.py y pruebas de contrato antes
de seleccionar Engram u otro proveedor.

- [ ] Definir identidad de proyecto, procedencia, versión de esquema, disponibilidad
  y presupuesto; probar servidor ajeno, respuesta incompatible y cambios de identidad.
- [ ] Mantener la documentación local como estado de trabajo y registrar espejo
  pendiente si falla el proveedor. Reconciliar conflictos sin descartar documentos.
- [ ] No afirmar escritura atómica entre archivo/servidor, sincronización remota ni
  aislamiento private/team sin pruebas de esas capacidades en el proveedor elegido.

## Orden y estimación

| Etapa | Dependencia | Esfuerzo relativo | Evidencia para cerrar |
|---|---|---|---|
| GS-1 | Smoke real del loop | Medio | Casos de riesgo anotados y ausencia de gates omitidos sin autorización. |
| GS-2 | Contrato del candidato; puede diseñarse junto con GS-1 | Medio/alto | Carreras, alteraciones y recuperación sin cierres con evidencia obsoleta. |
| GS-3 | Esquemas estables de estado/recibos | Medio | Una proyección coherente y sin inferencias de modelo/consumo. |
| GS-4 | Caso real y ciclo de procesos validado | Alto | Árboles cancelables, límites y eventos idempotentes. |
| GS-5 | Necesidad externa demostrada | Alto y dependiente del proveedor | Compatibilidad, privacidad y conflictos verificados. |

Prioridad inicial: GS-1 y GS-2. GS-3 mejora la experiencia después. GS-4/GS-5 son
opcionales. Voz, TUI completa, historial de prompts, permisos YOLO y paralelismo de
escritura quedan fuera de esta propuesta. Los tiempos y costes se estimarán con
casos/modelos definidos y medidas propias, sin reutilizar las cifras de otro repo.

Antes de integrar cada entrega: pruebas negativas, suite Python 3.10–3.13,
instalación/migración global/project y validación de artefactos. Las pruebas con
proveedores se habilitan expresamente y se informan aparte de fixtures. Revisar
el cambio completo antes de cualquier publicación; este plan no incluye push.

GENERATED BY AIKYA HARNESS
