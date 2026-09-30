# Seguridad y privacidad

Este repositorio usa exclusivamente datos sintéticos. No versione datos personales,
exports de producción, credenciales, tokens, claves, hosts privados ni identificadores
reales de recursos o clientes.

Mantenga la autenticación y la configuración del workspace en perfiles locales de
Databricks CLI, variables de entorno o recursos administrados por Databricks. Antes de
publicar cambios, ejecute:

```bash
uv run --extra dev python scripts/validate_local.py
```
