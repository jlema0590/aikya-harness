# Opciones de integración de SDD y plan de ejecución

Fecha: 21 de octubre de 2026.

## Recomendación

Trabajar en una rama nueva desde el `develop` actual y reutilizar de forma selectiva el motor SDD, los escenarios de prueba y las pruebas revisadas. Adaptar la instalación y los comandos a las interfaces actuales de `develop`.

No recomiendo fusionar íntegramente la rama histórica, sustituir el instalador actual por el antiguo ni escribir otro motor únicamente para evitar conflictos de Git.

Una implementación nueva reduce el acoplamiento heredado, pero puede introducir errores en la máquina de estados, las migraciones y las aprobaciones. Ninguna opción garantiza que no haya regresiones. La rama aislada protege `develop` durante el trabajo; las pruebas de compatibilidad, la activación explícita y los criterios de aceptación protegen el comportamiento al integrarlo.

## Estado actual

- Rama local creada: `feat/sdd-integration-v2`.
- Base: `origin/develop`, commit `3e35e7f84558dc2a6b3c8033c52e17c978bf284c`.
- En la rama nueva todavía no se han modificado fuentes, creado commits, subido cambios, implementado SDD ni realizado fusiones.
- La rama SDD original permanece intacta en `68cb4e3b1dada6e1a0d2c4c9005cab1de44bde28`.
- Validación anterior: `develop` pasa 223 pruebas; SDD pasa 146 y presenta un error; la simulación de fusión produce 19 archivos en conflicto.
- Alcance y evidencias: [análisis de las ramas, en inglés](../../../../../../sdd-branch-audit/ASSESSMENT.md).
- Tareas técnicas detalladas de la opción de reutilización: [plan de implementación, en inglés](2026-10-21-sdd-develop-integration.md).

## Comparativa con los mismos criterios de aceptación

| Aspecto | A — Integración selectiva de SDD existente, recomendada | B — Implementación nueva de SDD sobre develop |
|---|---|---|
| Punto de partida | `develop` actual, reutilizando el comportamiento aislado de SDD y sus escenarios de prueba. | `develop` actual; la rama antigua se utiliza únicamente como referencia de requisitos. |
| Motor | Conservar el código útil del ciclo de trabajo y la trazabilidad; corregir la validación del estado. | Diseñar e implementar de nuevo el ciclo de trabajo, el esquema y la persistencia. |
| Integraciones | Adaptar instalador, seis comandos, controles de generadores y documentación a las API actuales. | Escribir desde el principio esas mismas integraciones y reglas de compatibilidad. |
| Pruebas | Mantener las pruebas actuales, ampliar las de SDD y corregir la prueba defectuosa de enlaces simbólicos. | Mantener las pruebas actuales y crear las del motor; utilizar los escenarios antiguos como comprobaciones de aceptación independientes. |
| Conflictos | Evitar la fusión completa y resolver expresamente las diferencias de comportamiento. | No hay conflictos de la fusión histórica, pero también hay que modificar el instalador y los generadores actuales. |
| Riesgo principal | Arrastrar supuestos antiguos a las integraciones actuales. | Omitir casos límite y protecciones ya identificados en la rama anterior. |
| Problemas de auditoría | Corregir aprobaciones ligadas al alcance, referencias persistidas y criterios de finalización. | Diseñar y demostrar nuevamente esos mismos controles. |
| Migración | Preservar perfiles estándar, activación explícita e instalaciones repetidas. | Cumplir la misma compatibilidad y decidir cómo importar o migrar los registros SDD existentes. |
| Esfuerzo con margen de incertidumbre | **28–44 horas de ingeniería**. | **52–80 horas de ingeniería**. |
| Calendario, con unas 7 horas efectivas al día | **Aproximadamente 4–6 jornadas**. | **Aproximadamente 8–12 jornadas**. |
| Coste orientativo a 75 €/h | **2.100–3.300 €**. | **3.900–6.000 €**. |

Las estimaciones tienen una confianza media-baja. Suponen una persona familiarizada con el repositorio e incluyen aproximadamente un 20 % de margen de incertidumbre, con redondeo. El calendario no incluye esperas por aprobaciones, límites del proveedor o disponibilidad de CI. La estimación desde cero es un juicio de ingeniería, no una medición de una implementación realizada: incluye decisiones, persistencia, migración y aceptación que la reutilización ya aporta parcialmente.

Los costes representan presupuestos ilustrativos de trabajo, no una oferta cerrada ni una factura de API. Excluyen impuestos, suscripciones y consumo de modelos o API. La tarifa de 75 €/h es un supuesto de cálculo; no se presupone una tarifa de mercado ni ahorro de tokens. Para calcular el consumo de IA hace falta conocer el proveedor, el modelo y los registros reales de tokens.

Una fusión directa aceptando archivos completos de una de las ramas no es un atajo recomendable. La estimación anterior de 4–8 horas para resolver conflictos únicamente no cumple el alcance de aceptación de ninguna de estas dos opciones.

## Alcance y límites comunes

- Elección explícita de `methodology=standard|sdd`; `standard` sigue siendo el valor predeterminado.
- Los tipos de proyecto siguen siendo `development`, `infrastructure` y `devops`.
- Mantener `/aikya-init` para proyectos nuevos y `/aikya-analyze` para repositorios existentes.
- Conservar las protecciones de archivos gestionados, las interfaces del instalador y la política de idiomas actuales.
- Añadir los seis comandos SDD sin eliminar analyze/models/tokens: el catálogo combinado previsto tiene 27 comandos.
- Exigir una especificación y tarea activas para modificar archivos mediante SDD; sus aprobaciones nunca autorizan implícitamente operaciones remotas.
- Validar los requisitos persistidos, el grafo de dependencias, la cobertura y los valores reales de aprobación.
- Distinguir borradores estructuralmente válidos, evidencias registradas y condiciones de finalización.
- Mantener el motor y las instrucciones de ingeniería en inglés; la documentación viva utiliza el idioma en/es configurado.
- Admitir instalaciones nuevas y actualizaciones sin perder archivos ni controles personalizados.
- Excluir despliegues cloud reales, instalación de SDK, publicación de releases y ampliaciones del producto a múltiples plataformas.
- El alcance inicial es un flujo local con un único escritor. Si se requieren transacciones concurrentes y una vinculación más fuerte entre evidencias y commits, añadir aproximadamente 8–16 horas. Los registros iniciales no deben presentarse como auditorías inmutables o autenticadas.

## Plan A — Reutilizar SDD de forma selectiva

### Fase A1: Base y contratos — incluida en el bloque de adaptación del motor de 4–6 horas

- [x] Crear `feat/sdd-integration-v2` desde el `develop` actual.
- [ ] Fijar las revisiones y comprobaciones iniciales al comenzar la implementación; revisar el alcance si cambia `develop`.
- [ ] Preservar las API actuales de instalación, adopción y documentación, el registro de comandos y los permisos públicos.
- [ ] Trasladar `sdd_engine.py`, `examples/sdd/` y las pruebas SDD útiles como un cambio coherente.

### Fase A2: Motor, estado y contexto de aprobación — 6–10 horas

- [ ] Añadir pruebas de regresión que fallen ante referencias o ciclos inválidos, aprobaciones falsas y una especificación histórica aprobada frente a otra actual pendiente.
- [ ] Implementar un validador de estado común para carga, validación estructural, consulta de estado y operaciones de modificación.
- [ ] Vincular los generadores y la implementación a una especificación y tarea activas explícitas; conservar el consentimiento independiente para generar archivos.
- [ ] Separar validez del borrador y condiciones de finalización, así como evidencias declaradas y comprobaciones ejecutadas de forma independiente.

### Fase A3: Instalación actual y adaptadores de comandos — 6–10 horas

- [ ] Ampliar los actuales `install.py` y `aikya_setup.py`; conservar las utilidades de análisis, modelos y tokens del entorno de ejecución.
- [ ] Activar SDD explícitamente y preservar esa elección durante analyze/refresh y las reinstalaciones.
- [ ] Adaptar los seis comandos nuevos y los comandos de desarrollo afectados, evitando redirecciones circulares.
- [ ] Generar la documentación viva SDD mediante las plantillas en/es actuales; preservar controles personalizados, copias de seguridad y correspondencia entre vista previa y cambios reales.

### Fase A4: Validación integrada — 4–6 horas

- [ ] Corregir la prueba de enlaces simbólicos sin debilitar la comprobación de seguridad de rutas.
- [ ] Ejecutar las pruebas completas actuales y de SDD, y las comprobaciones de catálogo, metadatos y perfiles de ejemplo.
- [ ] Validar las versiones de Python soportadas en CI y los escenarios nuevo/existente, global/project y standard/SDD.
- [ ] Ejecutar la aceptación del ciclo completo para desarrollo, infraestructura y DevOps sobre proyectos de prueba seguros y revisados.

### Fase A5: Documentación y revisión — 3–4 horas

- [ ] Actualizar ambos README y las imágenes y recuentos del catálogo según el comportamiento final.
- [ ] Acordar una versión candidata superior a 6.0.1; 6.1.0 es una propuesta, no una publicación ya aprobada.
- [ ] Revisar las diferencias finales, CI y las evidencias de comportamiento antes de fusionar.

Subtotal: 23–36 horas. Presupuesto de planificación: **28–44 horas** con margen de incertidumbre. Las fases pueden reordenarse según sus dependencias; completar la creación de la rama no implica haber iniciado ni autorizado toda la implementación.

## Plan B — Implementar SDD desde cero

### Fase B1: Contratos y diseño del motor nuevo — 8–12 horas

- [ ] Fijar la misma matriz de aceptación que en el plan A.
- [ ] Definir esquema, ciclo de trabajo, condiciones de aprobación, tratamiento de errores y compatibilidad de registros existentes antes de implementar.
- [ ] Preservar el flujo estándar y las interfaces públicas actuales del instalador.

### Fase B2: Motor nuevo e instalación — 12–18 horas

- [ ] Implementar estado persistido, especificaciones, planes, tareas, aclaraciones, dependencias y transiciones de aprobación, comenzando por pruebas que fallen.
- [ ] Añadir activación explícita, distribución del entorno de ejecución, vistas previas de instalación y actualizaciones idempotentes.
- [ ] Decidir y probar la importación de registros SDD del esquema 1, o documentar que no se admite el formato preliminar antiguo antes de que los usuarios dependan de él.

### Fase B3: Comandos y controles — 10–16 horas

- [ ] Implementar los seis adaptadores de comandos con el formato actual y exigir especificación/tarea activas en generadores e implementación.
- [ ] Preservar la separación nuevo/existente y los permisos para operaciones externas.
- [ ] Implementar por separado la validación de borradores y las condiciones de finalización.

### Fase B4: Regresión y aceptación — 8–12 horas

- [ ] Añadir pruebas independientes de máquina de estados, entradas malformadas, rutas, aprobaciones, actualizaciones y conservación de datos.
- [ ] Utilizar los escenarios SDD existentes para comparar, sin copiar sus supuestos sin revisión.
- [ ] Ejecutar los mismos controles de CI y aceptación para los tres tipos de proyecto que en el plan A.

### Fase B5: Documentación y revisión — 5–8 horas

- [ ] Documentar el nuevo esquema y la política de migración, comandos, ejemplos, README bilingüe y límites de las evidencias.
- [ ] Completar la versión candidata y la revisión humana final.

Subtotal: 43–66 horas. Presupuesto de planificación: **52–80 horas** con margen de incertidumbre.

## Criterios para fusionar cualquiera de las dos opciones

1. El comportamiento actual de `develop` continúa cubierto y pasa sus pruebas; los controles nuevos de SDD también pasan.
2. El modo estándar conserva su comportamiento y SDD solo se activa explícitamente.
3. Una especificación o tarea incorrecta, ausente o sin aprobación válida se rechaza antes de modificar archivos.
4. La edición o fusión del estado persistido no permite eludir referencias, dependencias o aprobaciones.
5. Las personalizaciones y controles del usuario se conservan durante actualizaciones y ejecuciones repetidas.
6. La política de idiomas y la vista previa coinciden con los cambios realmente aprobados.
7. Los borradores, comprobaciones fallidas o evidencias ausentes no se presentan como trabajo completado.
8. CI y la revisión humana aprueban la integración antes de modificar `develop`.

Utilizar commits pequeños y reversibles y conservar la rama original como referencia. Tras la fusión, revertir los commits de integración si fuera necesario; no reescribir el historial compartido de `develop`. Revertir el código fuente no deshace automáticamente los archivos ya generados en proyectos de usuarios: siguen siendo necesarias las copias de seguridad y las pruebas de migración.

## Cuándo elegir una reescritura

Elegir el plan B si los requisitos cambian sustancialmente: por ejemplo, un servicio transaccional multiusuario, aprobaciones autenticadas, un esquema incompatible o una API independiente del asistente con otro diseño. Esos requisitos también invalidan las estimaciones del alcance inicial de un único escritor y requieren una definición propia.

Las evidencias actuales no justifican descartar el motor existente.

## Límite de ejecución

Este documento compara opciones y registra la preparación de la rama. La implementación queda pendiente de la elección del usuario. El siguiente paso recomendado es el plan A sobre `feat/sdd-integration-v2`, empezando por pruebas de regresión que reproduzcan los problemas detectados. Esta preparación no incluye subir cambios, fusionar ramas ni publicar una versión.

GENERATED BY AIKYA HARNESS
