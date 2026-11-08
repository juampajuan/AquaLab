# Contrato: comando `cargar_demo`

```bash
docker compose exec web python manage.py cargar_demo
```

Sin argumentos.

## Precondiciones

- `AQUALAB_ENTORNO=desarrollo` en el entorno (en `.env`) y `DEBUG=True`.
- Base PostgreSQL migrada.

## Salidas

| Caso | Código de salida | Mensaje (stdout/stderr) | Cambios |
|---|---|---|---|
| Carga correcta | 0 | Resumen: «Demo cargada.», clientes, orígenes, muestras, estudios por estado, informes y los usuarios `tecnico@demo.aqualab` / `bioquimico@demo.aqualab` con contraseña `Demo-1234`. Si importó el catálogo, lo indica. | Toda la demo |
| Demo ya cargada | 0 | «La demo ya está cargada. Para empezar de cero: docker compose down -v, up -d, migrate y cargar_demo.» | Ninguno |
| Fuera de desarrollo / sin DEBUG | 1 (`CommandError`) | «cargar_demo solo corre en desarrollo: requiere AQUALAB_ENTORNO=desarrollo y DEBUG=True.» | Ninguno |
| Motor no PostgreSQL | 1 | «La demo requiere PostgreSQL.» | Ninguno |
| Correo demo ocupado | 1 | «Ya existe el usuario <correo> y no es de la demo. No se cargó nada.» | Ninguno |
| Tipo demo distinto | 1 | «Ya existe el tipo de estudio «<nombre>» con otras pruebas. No se cargó nada.» | Ninguno |
| Falla inesperada | 1 | «No se pudo cargar la demo: <motivo>. No se guardó nada.» | Ninguno |

## Reemplazo

`cargar_demo_us51` deja de existir; `manage.py cargar_demo_us51` responde «Unknown command».
