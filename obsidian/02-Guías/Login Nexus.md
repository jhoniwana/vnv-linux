---
tags: [guia, login, nexus]
---
# Login Nexus

El login automático a NexusMods es **la pieza más difícil del proyecto** — y quedó resuelta.

## El problema

- Nexus usa **Cloudflare Turnstile** en el login → bloquea navegadores headless
- Playwright (Chrome): ❌ bloqueado
- SeleniumBase UC: ❌ bloqueado
- **Camoufox (Firefox anti-detección) headless: ✅ PASA**

## La solución

`login_camoufox.py` (desde la UI: paso 2, o `./vnv.sh login`):

1. Abre Camoufox headless
2. Navega a `users.nexusmods.com/register` → click "Sign in"
3. Completa `#user_login` + `#password` (desde el formulario de la UI o `NEXUS_USER`/`NEXUS_PASS`)
4. Submit → Turnstile pasa (Camoufox tiene fingerprint real de Firefox)
5. Guarda las cookies: **`nexusmods_session`** + **`cf_clearance`** en `~/.config/vnv-linux/` (permisos 600)

## Datos clave

- La cookie de sesión se llama **`nexusmods_session`** (NO `sid` — la renombraron)
- `cf_clearance` demuestra que pasaste el challenge de Cloudflare (clave para descargas)
- El login se hace **una sola vez**; las cookies duran días/semanas

## Auto-recuperación

Si la sesión expira a mitad de descarga, el [[Descarga de Mods|gestor]] detecta "Log in" en la página → re-loguea solo con las credenciales guardadas (`./vnv.sh credenciales`) → sigue.

## Alternativa manual

`./vnv.sh config-cookies`: pegar la cookie `nexusmods_session` desde el navegador (F12 → Application → Cookies).

## Referencias

- [[Descarga de Mods]]
- [[Descargas - Troubleshooting]]
