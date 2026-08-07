---
tags: [referencia, nexus, api]
---
# API de Nexus

## Endpoints (v1)

| Endpoint | Use | Free |
|---|---|---|
| `GET /v1/users/validate.json` | validate API key | ✅ |
| `GET /v1/games/newvegas/mods/{id}.json` | mod metadata | ✅ |
| `GET /v1/games/newvegas/mods/{id}/files.json` | file list | ✅ |
| `GET .../files/{fid}/download_link.json` | download link | ❌ **Premium only** |

## FREE download (the discovery)

- **Do NOT use `download_link`** (403 without Premium)
- Web endpoint: **`https://www.nexusmods.com/Download/?id={file_id}&game_id=130&source=ModPage`**
  - Works with the **`nexusmods_session` cookie** (free)
  - Shows a page with "served via CDN" (button) or "should automatically begin" (auto)
- Legacy `DownloadPopUp` widget: dead (redirects to the mod page)

## Login

- Form: `users.nexusmods.com` → "Sign in" → `#user_login` + `#password` + Turnstile
- **Camoufox headless passes the Turnstile** (Playwright/Selenium do not)
- Cookies: `nexusmods_session` (session) + `cf_clearance` (Cloudflare)

## Rules

- Personal API key, free at nexusmods.com/settings/api-keys
- Rate limits: ~5s between calls (metadata)
- Downloads: human pace 8-15s between mods
- The `nexusmods_session` cookie expires → the manager re-logs in by itself

## References

- [[Login Nexus]]
- [[Descarga de Mods]]
