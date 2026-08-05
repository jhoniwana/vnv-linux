---
tags: [troubleshooting, descargas]
---
# Descargas — Troubleshooting

## Errores encontrados y resueltos

### 1. "Manual download" no automatizable (2026)
**Síntoma**: las filas de archivos no tienen botón de descarga en el DOM.
**Causa**: está en el shadow DOM de `<mod-download-modal>` (web component).
**Solución**: endpoint `/Download/?id={fid}&game_id=130` descubierto en el bundle JS.

### 2. El descargador bajaba versiones viejas
**Síntoma**: 44 desviaciones de versión; JIP LN bajó el INI en vez del plugin.
**Causa**: `actualizar.py` elegía el PRIMER archivo MAIN, no el más reciente.
**Solución**: `max(mains, key=uploaded_timestamp)` → 13 file_ids corregidos.

### 3. Sesión expirada no detectada
**Síntoma**: el re-login no se disparaba.
**Causa**: buscaba "Sign in" pero Nexus usa **"Log in"** para no-autenticados.
**Solución**: detectar ambos + ausencia de "served via CDN".

### 4. Page.goto timeouts masivos (Cloudflare)
**Síntoma**: 25 mods fallaron con timeouts tras descargas rápidas.
**Causa**: rate limiting de Cloudflare.
**Solución**: espera de challenge (hasta 60s) + 3 intentos con backoff + ritmo 8-15s.

### 5. Manifest duplicado (66347 ×2)
**Causa**: al reemplazar 90824→66347 sin notar que ya existía.
**Solución**: deduplicación → 53 mods únicos.

## Monitoreo

```bash
./venv/camoufox-python scripts/gestor_descargas.py --verificar   # integridad
cat estado.json                                                   # estados por mod
tail /tmp/descarga.log                                           # log de una corrida
```

> ⚠️ No lanzar dos instancias al mismo archivo de log (se pisan).

## Referencias

- [[Descarga de Mods]]
- [[Problemas Comunes]]
