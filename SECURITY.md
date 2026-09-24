# Seguridad y privacidad

Este repositorio contiene únicamente datos sintéticos. No incluya exports de producción,
credenciales, tokens, URL privadas del workspace ni identificadores reales de clientes.

## Valores públicos intencionales

- `telco_workshop`: catálogo ficticio usado como valor didáctico predeterminado.
- `red_calidad`: schema ficticio usado como valor didáctico predeterminado.
- `DATABRICKS_WAREHOUSE_ID`: nombre de variable; no se versiona ningún valor real.
- Regiones, comunas y coordenadas aproximadas: información geográfica pública usada
  para generar sitios ficticios.

## Configuración segura

Use perfiles locales de Databricks CLI, variables de entorno y recursos asociados a
Databricks Apps. Nunca guarde tokens ni IDs reales en archivos versionados.
`databricks.yml` no fija perfil, host ni workspace.

Antes de publicar cambios, ejecute:

```bash
uv run --extra dev python scripts/validate_local.py
```
