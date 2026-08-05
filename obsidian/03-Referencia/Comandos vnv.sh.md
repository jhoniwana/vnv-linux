---
tags: [referencia, comandos]
---
# Comandos vnv.sh

```bash
./vnv.sh ui               # 🖥️ Interfaz web (wizard, sin terminal) — EL comando principal
./vnv.sh setup            # prepara entorno (venv, Camoufox, libs, protontricks)
./vnv.sh login            # login automático a Nexus (Camoufox)
./vnv.sh config-cookies   # pegar cookie manualmente (fallback)
./vnv.sh credenciales     # guardar email+pass para re-login automático (600)
./vnv.sh config           # guardar API key de Nexus
./vnv.sh download         # descargar mods (gestor con estados)
./vnv.sh update           # alias de download
./vnv.sh estado           # verificar archivos vs manifest
./vnv.sh steam            # diagnosticar/conectar Steam + Proton (--si no-interactivo)
./vnv.sh install          # MO2 + importar mods + INIs + LOOT
./vnv.sh run              # lanzar el juego vía MO2
```

## Scripts internos (venv/camoufox-python)

```bash
./venv/camoufox-python scripts/actualizar.py          # metadata de la API
./venv/camoufox-python scripts/gestor_descargas.py    # descargas (--solo-fallidos, --verificar, --forzar, --solo, --seccion)
./venv/camoufox-python scripts/importar_mo2.py        # importar a MO2 (--dir, --solo)
./venv/camoufox-python scripts/login_camoufox.py      # login (NEXUS_USER/NEXUS_PASS)
```

## Config

- `~/.config/vnv-linux/` — api_key, nexus_session, cf_clearance, credenciales (todo 600)
- `manifest.json` — los 53 mods
- `estado.json` — estados de descarga
- `downloads/` — los archivos
