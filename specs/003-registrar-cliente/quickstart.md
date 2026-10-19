# Quickstart: validar "Registrar cliente"

**Feature**: `003-registrar-cliente` | **Plan**: [plan.md](./plan.md)

Guía para comprobar de punta a punta que la US 2.1 (SCRUM-43) funciona. Detalle de pantallas y
mensajes en [contracts/registro-cliente-ui.md](./contracts/registro-cliente-ui.md); del modelo y
validaciones en [data-model.md](./data-model.md).

## Prerrequisitos

- Docker y Docker Compose instalados y corriendo (`web` + `db`).
- Archivo `.env` creado a partir de `.env.example`.
- Un usuario activo en la base (por ejemplo, el superusuario creado con `createsuperuser`).

## Levantar el entorno

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser   # si todavía no tenés un usuario activo
```

## Tests automatizados y formato

```bash
docker compose exec web pytest clientes
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
```

**Esperado**: todos los tests en verde (al menos uno por cada escenario de aceptación 1–8) y `ruff`
sin errores.

## Validación manual

App en `http://localhost:8000`.

| # | Pasos | Resultado esperado | Escenario / Requisito |
|---|---|---|---|
| 1 |Sin iniciar sesión, abrir `/clientes/registrar/` | Redirige a la pantalla de inicio de sesión | FR-001 |
| 2 | Iniciar sesión con un usuario activo e ir a `/clientes/registrar/` | Se muestra el formulario "Registrar cliente" | FR-001 |
| 3 | Enviar el formulario vacío | Error `"Debés ingresar al menos el nombre o la razón social del cliente."` y `"Este campo es obligatorio."` en tipo de documento, número de documento y correo electrónico; no avanza | Esc. 3, FR-003, FR-004, FR-005 |
| 4 | Ingresar DNI `123` (menos de 7 dígitos) o DNI `123456789` (más de 8 dígitos) | Error `"El DNI debe tener 7 u 8 dígitos numéricos."`; los demás datos válidos ingresados se conservan | Esc. 8, FR-009, FR-016 |
| 5 | Ingresar CUIT `20-12345678-0` (dígito verificador inválido; el correcto para `2012345678` es `6`) | Error `"El CUIT debe tener 11 dígitos y un dígito verificador válido."`; no avanza a confirmación | Esc. 8, FR-016 |
| 6 | Ingresar correo `cliente@` y teléfono `abc` | Errores de formato en correo electrónico y teléfono; no avanza | Esc. 5, FR-006 |
| 7 | Completar Razón social `  Aguas del Sur S.A.  `, Tipo `CUIT`, Número `20-12345678-6`, Correo `  Contacto@AguasSur.com `, Teléfono `+54 11 4567-8901`, Domicilio `Av. Paseo Colón 850` → **Continuar** | Pantalla de revisión con `"Aguas del Sur S.A."`, `"CUIT"`, `"20123456786"`, `"contacto@aguassur.com"`, `"+54 11 4567-8901"`, `"Av. Paseo Colón 850"` | FR-010, Edge cases 1–3 |
| 8 | En la revisión, hacer clic en **"Volver y editar"** | Vuelve al formulario con todos los datos precargados; en la base todavía no existe el cliente | Esc. 6, FR-011 |
| 9 | Hacer clic en **Continuar** y luego en **"Cancelar"** | Mensaje `"Registro de cliente cancelado."`; formulario limpio; el cliente no fue creado | Esc. 6, FR-011, SC-002 |
| 10 | Volver a cargar los datos del paso 7 (o una persona con Nombre `Juan Pérez`, DNI `30.123.456`, sin teléfono ni domicilio), **Continuar** y **"Confirmar"** | Redirige a `/clientes/<id>/` con el mensaje `"Cliente registrado correctamente."` y muestra todos los datos registrados en la ficha del cliente | Esc. 1, Esc. 2, FR-013, SC-001, SC-004 |
| 11 | Volver atrás en el navegador a la pantalla de confirmación y volver a enviar **"Confirmar"** | No se crea un segundo cliente; muestra la ficha del mismo cliente | Esc. 7, FR-012 |
| 12 | Intentar registrar otro cliente con Tipo `CUIT` y Número `20.123.456.786` (o ` 20 12345678 6 `) | Error `"Ya existe un cliente registrado con este tipo y número de documento."`; se rechaza el alta | Esc. 4, FR-007, SC-003 |

## Limpieza

```bash
docker compose down        # agregar -v si se quiere borrar también la base de datos local
```
