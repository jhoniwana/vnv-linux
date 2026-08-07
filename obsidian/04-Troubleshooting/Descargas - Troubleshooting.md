---
tags: [troubleshooting, descargas]
---
# Descargas — Troubleshooting

## Errors found and solved

### 1. "Manual download" not automatable (2026)
**Symptom**: the file rows have no download button in the DOM.
**Cause**: it is in the shadow DOM of `<mod-download-modal>` (web component).
**Solution**: `/Download/?id={fid}&game_id=130` endpoint discovered in the JS bundle.

### 2. The downloader fetched old versions
**Symptom**: 44 version deviations; JIP LN downloaded the INI instead of the plugin.
**Cause**: `actualizar.py` picked the FIRST MAIN file, not the newest one.
**Solution**: `max(mains, key=uploaded_timestamp)` → 13 file_ids fixed.

### 3. Expired session not detected
**Symptom**: the re-login did not trigger.
**Cause**: it searched for "Sign in" but Nexus uses **"Log in"** for non-authenticated users.
**Solution**: detect both + absence of "served via CDN".

### 4. Massive page.goto timeouts (Cloudflare)
**Symptom**: 25 mods failed with timeouts after fast downloads.
**Cause**: Cloudflare rate limiting.
**Solution**: challenge wait (up to 60s) + 3 attempts with backoff + 8-15s pace.

### 5. Duplicated manifest (66347 ×2)
**Cause**: replacing 90824→66347 without noticing it already existed.
**Solution**: deduplication → 53 unique mods.

## Monitoring

```bash
./venv/camoufox-python scripts/gestor_descargas.py --verificar   # integrity
cat estado.json                                                   # states per mod
tail /tmp/descarga.log                                           # log of a run
```

> ⚠️ Do not launch two instances writing to the same log file (they overwrite each other).

## References

- [[Descarga de Mods]]
- [[Problemas Comunes]]
