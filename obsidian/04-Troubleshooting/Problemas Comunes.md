---
tags: [troubleshooting]
---
# Problemas Comunes

## Setup / Camoufox

| Problema | Solución |
|---|---|
| Camoufox no arranca (`libcairo... undefined symbol`) | Correr `./vnv.sh setup` → el fallback micromamba+pixman lo resuelve (libs del sistema rotas) |
| pip install falla | Verificar `python3-venv` instalado y red |
| Sin sudo | El setup muestra los comandos exactos para tu distro |

## Login / Sesión

| Problema | Solución |
|---|---|
| Turnstile bloquea | Usar Camoufox (no Playwright/Selenium); el login automático lo pasa |
| Sesión expirada a mitad de descarga | El gestor detecta "Log in" → re-loguea solo (necesita `./vnv.sh credenciales`) |
| Cookie vieja | Correr `./vnv.sh login` de nuevo |

## Descargas

| Problema | Solución |
|---|---|
| Cloudflare "Just a moment..." | El gestor espera hasta 60s y reintenta |
| Archivo descargado es HTML | El gestor lo detecta (`file`) y lo borra → reintenta |
| Mod 90824 | Está hidden por el autor — la guía actual usa el 66347 |

## Instalación / Juego

| Problema | Solución |
|---|---|
| No encuentra el juego | Editar `STEAM_LIBRARIES` en vnv.sh (ruta de tu Steam) |
| Prefix de Proton no existe | FNV → Propiedades → Compatibilidad → forzar Proton → jugar una vez |
| Crash al inicio | Verificar nvtf.ini y NVTF activo |
| Sin mods cargados | Lanzar desde MO2, perfil Default activo |

## Referencias

- [[Descargas - Troubleshooting]]
- [[Lanzamiento del Juego]]
