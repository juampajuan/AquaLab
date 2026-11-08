# Research: Datos de demo

Decisiones técnicas de SCRUM-78. Formato: decisión, motivo y alternativas descartadas.

## R1 – Cargar con los servicios reales

- **Decisión**: la demo se arma llamando a `muestras.servicios.registrar_muestra`,
  `estudios.servicios.crear_estudio`, `cargar_mediciones`, `validar_resultados` e
  `informes.servicios.emitir_informe`, con el técnico o el bioquímico demo como usuario.
- **Motivo**: FR-007 pide las mismas reglas que una persona: N° PI e INF sin huecos, resultados
  calculados por `calculo.recalcular` (Cloruro es `x*10`), `Validacion` con los límites del vertido,
  copia del informe con firma. Reusar los servicios evita duplicar esas reglas y hace que la demo
  falle si una regla cambia.
- **Alternativas**: crear filas con el ORM directamente (rápido, pero puede generar estados que la
  app nunca produce, como Finalizado sin `Validacion`); fixtures JSON (se desactualizan con cada
  migración y no calculan resultados).

## R2 – Correr las fechas hacia atrás

- **Decisión**: después de cada paso, actualizar con `QuerySet.update()` las fechas de las filas
  recién creadas: `Muestra.fecha_registro`, `Estudio.fecha_creacion`, `Medicion.fecha_carga`,
  `Resultado.fecha_calculo`, `Validacion.fecha_validacion`, `Informe.fecha_emision`; también
  `Origen.fecha_alta` y `Usuario.date_joined` al comienzo de la demo.
- **Motivo**: esos campos son `auto_now_add`/`auto_now` y quedarían todos con la fecha de hoy, sin
  nada que mostrar por mes o semana (8.3). `update()` no aplica `auto_now` y no pasa por
  `Informe.save()`, que rechaza cambios sobre un informe existente (CLAUDE.md, US 7.3). Solo se
  tocan filas creadas por la demo, dentro de la misma transacción. La fecha de emisión no está en
  `Informe.contenido` (la copia guarda fechas de muestreo e ingreso), así que la copia sigue fiel.
- **Alternativas**: congelar el reloj con una librería (dependencia nueva, solo para tests);
  parámetro de fecha en cada servicio (cambia código de producción por una necesidad de demo).

## R3 – Cálculo de fechas

- **Decisión**: para el mes `k` (0 = actual, 5 = hace 5 meses) el muestreo es el día
  `dia_base(origen)` del mes; ingreso = muestreo + 0–1 días; creación del estudio = ingreso;
  carga = ingreso + 2–5 días; validación = carga + 1–3 días; emisión = validación + 0–6 días
  (desplazamientos fijos del guion, así el tiempo de respuesta varía entre ~3 días y ~3 semanas).
  Cada fecha se recorta a `ahora` y nunca es anterior a la del paso previo. En el mes actual, si
  hoy es muy temprano en el mes, los pasos se comprimen hacia hoy.
- **Motivo**: FR-008 (orden coherente, nunca futuro) y SC-002 (todos los meses con muestras). Las
  horas se fijan (por ejemplo 10:00 hora local) para que las semanas no dependan de la hora en que
  se corre.
- **Alternativas**: fechas absolutas (la demo envejece y «este mes» queda vacío); fechas al azar
  (contradice FR-001a).

## R4 – Valores siempre iguales

- **Decisión**: un guion fijo en `estudios/demo.py`: por origen, la serie mensual de valores de cada
  prueba (texto decimal, como `"7.4"`), y los casos especiales (fuera de norma, «< LD», Presente,
  desvío). Las claves de idempotencia (`clave_borrador`, `clave`) se derivan con `uuid5` del
  origen y el mes.
- **Motivo**: FR-001a/SC-007 y tests con valores exactos. Un guion legible deja ver dónde está cada
  caso para la presentación.
- **Alternativas**: `random.Random(semilla)` (reproducible pero no se ve dónde cae cada caso).

## R5 – Detectar la demo y los conflictos

- **Decisión**: la demo «ya está cargada» si existe algún `Cliente` con correo que termina en
  `@demo.aqualab` → aviso y salida sin cambios. Si no hay clientes demo pero existe un usuario con
  un correo demo, o un tipo con nombre demo y otras pruebas → `CommandError` sin cambios. Todo se
  revisa dentro de la transacción, después de `pg_advisory_xact_lock(7_800_001)`.
- **Motivo**: FR-014/015 y la aclaración 3. El correo es la marca de demo elegida en la aclaración
  1; el lock evita que dos ejecuciones simultáneas carguen dos veces.
- **Alternativas**: tabla o bandera propia (modelo y migración solo para la demo).

## R6 – Solo en desarrollo

- **Decisión**: exigir `AQUALAB_ENTORNO=desarrollo` (variable de entorno, como el comando viejo),
  `settings.DEBUG` y motor PostgreSQL. Se agrega `AQUALAB_ENTORNO=desarrollo` a `.env.example`;
  quien ya tiene `.env` lo agrega a mano (el mensaje de error lo indica). `qa` ya no se acepta.
- **Motivo**: FR-002. Dos condiciones independientes reducen el riesgo de correrlo en Render
  (producción no tiene la variable y corre con `DEBUG=False`).
- **Alternativas**: un setting en `settings.py` (se versiona y podría quedar activo en producción).

## R7 – Usuarios demo y firma

- **Decisión**: `tecnico@demo.aqualab` (Técnico Demo, sin grupos) y `bioquimico@demo.aqualab`
  (Bioquímica Demo, grupos «Bioquímicos» y «Administradores»), activos, aprobados y con contraseña
  `Demo-1234` (`set_password`). `FirmaProfesional` con matrícula «MP 0000 (DEMO)» y un PNG en
  escala de grises de 600 × 200 con un trazo simple, armado con `zlib`/`struct` (≤ 64 KB, dentro de
  lo que acepta `leer_firma`). El bioquímico se vuelve a leer de la base después de asignar grupos
  para no usar una caché de permisos vieja.
- **Motivo**: FR-012; el bioquímico necesita `estudios.validar_resultados` e
  `informes.emitir_informes` (los da el grupo por migración) y firma para emitir (US 7.3).
  Administradores le muestra el panel (025).
- **Alternativas**: pedir `--usuario` como el comando viejo (no cubre dos roles); Pillow
  (dependencia nueva).

## R8 – Catálogo y tipos de estudio

- **Decisión**: si `Prueba` está vacía, `call_command("importar_catalogo_pruebas")` dentro de la
  transacción; si no, no se reimporta. Tipos demo:
  - «Físico-químico básico»: PH, TURBIDEZ, COND, CL-, DUREZA-T, NH4, FE.
  - «Bacteriológico»: COL-TOT, MESOFILAS, ECOLI, PSEUDO.
  - «Vuelco a colectora»: PH, TEMPERATURA, SS10, SSEE, DET-SAAM.

  Si existe un tipo con el mismo nombre y exactamente esas pruebas, se reutiliza; con otras
  pruebas, conflicto (R5).
- **Motivo**: FR-005/013; las pruebas elegidas tienen límites comparables en el catálogo (pH 6,4 a
  8,5; Cloruro ≤ 350; Turbidez ≤ 3; Coliformes ≤ 3; SS10 «Ausente» con LD 0,1; vertido cloacal con
  límites propios) y cubren cálculo por fórmula (CL-, DUREZA-T, NH4) y Ausente/Presente.
- **Alternativas**: un tipo con muchas pruebas (carga más lenta y gráficos con ruido).

## R9 – El desvío

- **Decisión**: en «Pozo 2» (Lácteos del Sur), Cloruro medido 11,8 / 12,1 / 12,4 / 12,0 en los
  meses −5 a −2 (resultados 118–124 mg/l, cumplen), 41,5 en el mes −1 (415 mg/l, validado y fuera de
  norma: ≈ 3,4 × el promedio de los tres anteriores) y 43,0 en el mes actual (430 mg/l, calculado y
  sin validar).
- **Motivo**: FR-011/SC-004; supera con amplitud la regla inicial de SCRUM-61 (> 30 % contra el
  promedio de los últimos 3 validados) y también un umbral más estricto. El valor actual sigue
  alejado del promedio de los últimos 3 validados (≈ 219 mg/l), así 8.2 lo marca antes de validar.
- **Alternativas**: desvío en pH (escala chica, el gráfico se nota menos).
