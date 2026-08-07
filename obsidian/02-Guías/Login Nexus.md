---
tags: [guia, login, nexus]
---
# Login Nexus

The automatic login to NexusMods is **the hardest piece of the project** — and it was solved.

## The problem

- Nexus uses **Cloudflare Turnstile** on login → blocks headless browsers
- Playwright (Chrome): ❌ blocked
- SeleniumBase UC: ❌ blocked
- **Camoufox (anti-detection Firefox) headless: ✅ PASSES**

## The solution

`login_camoufox.py` (from the UI: step 2, or `./vnv.sh login`):

1. Opens Camoufox headless
2. Navigates to `users.nexusmods.com/register` → clicks "Sign in"
3. Fills in `#user_login` + `#password` (from the UI form or `NEXUS_USER`/`NEXUS_PASS`)
4. Submit → Turnstile passes (Camoufox has a real Firefox fingerprint)
5. Saves the cookies: **`nexusmods_session`** + **`cf_clearance`** in `~/.config/vnv-linux/` (permissions 600)

## Key facts

- The session cookie is called **`nexusmods_session`** (NOT `sid` — it was renamed)
- `cf_clearance` proves you passed the Cloudflare challenge (key for downloads)
- The login is done **only once**; the cookies last for days/weeks

## Self-recovery

If the session expires mid-download, the [[Descarga de Mods|manager]] detects "Log in" on the page → re-logs in by itself with the saved credentials (`./vnv.sh credenciales`) → continues.

## Manual alternative

`./vnv.sh config-cookies`: paste the `nexusmods_session` cookie from the browser (F12 → Application → Cookies).

## References

- [[Descarga de Mods]]
- [[Descargas - Troubleshooting]]
