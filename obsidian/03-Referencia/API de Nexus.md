---
tags: [referencia, nexus, api]
---
# API de Nexus

## Endpoints (v1)

| Endpoint | Uso | Gratis |
|---|---|---|
| `GET /v1/users/validate.json` | validar API key | ✅ |
| `GET /v1/games/newvegas/mods/{id}.json` | metadata del mod | ✅ |
| `GET /v1/games/newvegas/mods/{id}/files.json` | lista de archivos | ✅ |
| `GET .../files/{fid}/download_link.json` | link de descarga | ❌ **solo Premium** |

## Descarga FREE (lo descubierto)

- **NO usar `download_link`** (403 sin Premium)
- Endpoint web: **`https://www.nexusmods.com/Download/?id={file_id}&game_id=130&source=ModPage`**
  - Funciona con la **cookie `nexusmods_session`** (gratis)
  - Muestra página con "served via CDN" (botón) o "should automatically begin" (auto)
- Widget legacy `DownloadPopUp`: muerto (redirige a la página del mod)

## Login

- Formulario: `users.nexusmods.com` → "Sign in" → `#user_login` + `#password` + Turnstile
- **Camoufox headless pasa el Turnstile** (Playwright/Selenium no)
- Cookies: `nexusmods_session` (sesión) + `cf_clearance` (Cloudflare)

## Reglas

- API key personal, gratis en nexusmods.com/settings/api-keys
- Rate limits: ~5s entre llamadas (metadata)
- Descargas: ritmo humano 8-15s entre mods
- La cookie `nexusmods_session` expira → el gestor re-loguea solo

## Referencias

- [[Login Nexus]]
- [[Descarga de Mods]]
