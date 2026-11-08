# Data Model: Datos de demo

Sin entidades ni migraciones nuevas. La demo crea filas de modelos existentes (US 1.x a 7.3) según
un guion fijo en `estudios/demo.py`.

## Usuarios demo

| Correo | Nombre | Grupos | Firma | Contraseña |
|---|---|---|---|---|
| `tecnico@demo.aqualab` | Técnico Demo | — | — | `Demo-1234` |
| `bioquimico@demo.aqualab` | Bioquímica Demo | Bioquímicos, Administradores | PNG + «MP 0000 (DEMO)» | `Demo-1234` |

Ambos activos y aprobados. Mediciones: `cargada_por` = técnico; validaciones e informes: bioquímico.

## Clientes y orígenes

Correos `@demo.aqualab` (marca de demo) y documentos de un rango ficticio (CUIT `30-7000000x-x`,
DNI `9999999x`).

| Cliente | Documento | Origen | Vertido | Tipo de estudio |
|---|---|---|---|---|
| Lácteos del Sur S.A. | CUIT | Pozo 1 | agua | Físico-químico básico |
| | | Pozo 2 (desvío) | agua | Físico-químico básico |
| | | Salida a colectora | cloacal | Vuelco a colectora |
| Municipalidad de Villa Verde | CUIT | Tanque elevado | agua | Físico-químico básico + Bacteriológico básico (meses pares) |
| | | Escuela N° 12 | agua | Bacteriológico básico |
| María González | DNI | Pozo domiciliario | agua | Físico-químico básico |
| | | Tanque domiciliario | agua | Bacteriológico básico |

7 orígenes × 6 meses = 42 muestras; con el bacteriológico extra del tanque, unos 45 estudios.

## Estado destino por mes

| Mes | Estado de los estudios |
|---|---|
| −5 a −2 | Informe generado |
| −1 | Informe generado, salvo: «Escuela N° 12» → **Finalizado sin informe** (alerta) y «Pozo domiciliario» → **En proceso estancado** (mediciones parciales; día base 5 y carga recortada a ≤ hoy − 10 días) |
| 0 (actual) | Pendiente de análisis: Tanque domiciliario, Escuela N° 12 · En proceso: Pozo 2 (desvío sin validar), Salida a colectora (mediciones parciales) · Finalizado: Pozo 1, Tanque elevado (FQ) · Informe generado: Pozo domiciliario, Tanque elevado (Bact.) |

Resultado: ≥ 2 estudios por estado (SC-003); el técnico tiene mediciones por cargar y el
bioquímico, resultados por validar y estudios listos para emitir (US2).

## Casos especiales del guion

- **Fuera de norma**: Turbidez 4,2 NTU en Pozo domiciliario (meses −4 y −2); Coliformes totales 12
  UFC/100 ml en Tanque domiciliario (mes −3); pH 10,6 en Salida a colectora (mes −2, fuera del límite
  cloacal 7,01–10) y DET-SAAM 14 mg/l en Salida a colectora (mes −3, fuera del límite cloacal 10);
  Cloruro de Pozo 2 en meses −1 y 0.
- **< LD**: SS10 0,05 ml en Salida a colectora (todos los meses; cumple con «Ausente», FR-016 de 7.2).
- **Ausente/Presente**: E. coli Presente en Tanque domiciliario (mes −3); Ausente en el resto.
- **Desvío**: ver research R9.

## Fechas (research R3)

```text
muestreo   = día base del origen en el mes k (recortado a hoy)
ingreso    = muestreo + 0..1 d
estudio    = ingreso
carga      = ingreso + 2..5 d
validación = carga + 1..3 d
emisión    = validación + 0..6 d
cada fecha ≤ ahora y ≥ la del paso anterior; hora fija 10:00 (America/Argentina/Buenos_Aires)
estancado (Pozo domiciliario, mes −1): carga ≤ ahora − 10 d
cada paso se ejecuta dentro de reloj(fecha): las filas nacen con esa fecha (research R2)
```

## Reglas de validación del comando

- Entorno: `AQUALAB_ENTORNO == "desarrollo"`, `DEBUG` y PostgreSQL.
- Ya cargada: existe `Cliente` con correo `@demo.aqualab` → sin cambios.
- Conflicto: correo de usuario demo ocupado, o tipo demo con otras pruebas → sin cambios.
- Todo en una transacción con `pg_advisory_xact_lock(7_800_001)`.
