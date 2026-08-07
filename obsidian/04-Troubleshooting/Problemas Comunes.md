---
tags: [troubleshooting]
---
# Problemas Comunes

## Setup / Camoufox

| Problem | Solution |
|---|---|
| Camoufox does not start (`libcairo... undefined symbol`) | Run `./vnv.sh setup` → the micromamba+pixman fallback solves it (broken system libs) |
| pip install fails | Check that `python3-venv` is installed and the network |
| No sudo | The setup shows the exact commands for your distro |

## Login / Session

| Problem | Solution |
|---|---|
| Turnstile blocks | Use Camoufox (not Playwright/Selenium); the automatic login passes it |
| Session expired mid-download | The manager detects "Log in" → re-logs in by itself (needs `./vnv.sh credenciales`) |
| Old cookie | Run `./vnv.sh login` again |

## Downloads

| Problem | Solution |
|---|---|
| Cloudflare "Just a moment..." | The manager waits up to 60s and retries |
| Downloaded file is HTML | The manager detects it (`file`) and deletes it → retries |
| Mod 90824 | It is hidden by the author — the current guide uses 66347 |

## Install / Game

| Problem | Solution |
|---|---|
| Game not found | Edit `STEAM_LIBRARIES` in vnv.sh (your Steam path) |
| Proton prefix does not exist | FNV → Properties → Compatibility → force Proton → play once |
| Crash on start | Check nvtf.ini and NVTF active |
| No mods loaded | Launch from MO2, Default profile active |

## References

- [[Descargas - Troubleshooting]]
- [[Lanzamiento del Juego]]
