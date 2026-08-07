---
tags: [referencia, comandos]
---
# Comandos vnv.sh

```bash
./vnv.sh ui               # 🖥️ Web interface (wizard, no terminal) — THE main command
./vnv.sh setup            # prepares the environment (venv, Camoufox, libs, protontricks)
./vnv.sh login            # automatic login to Nexus (Camoufox)
./vnv.sh config-cookies   # paste the cookie manually (fallback)
./vnv.sh credenciales     # save email+pass for automatic re-login (600)
./vnv.sh config           # save the Nexus API key
./vnv.sh download         # download mods (manager with states)
./vnv.sh update           # alias of download
./vnv.sh estado           # verify files vs manifest
./vnv.sh steam            # diagnose/connect Steam + Proton (--si non-interactive)
./vnv.sh install          # MO2 + import mods + INIs + LOOT
./vnv.sh run              # launch the game via MO2
```

## Internal scripts (venv/camoufox-python)

```bash
./venv/camoufox-python scripts/actualizar.py          # API metadata
./venv/camoufox-python scripts/gestor_descargas.py    # downloads (--solo-fallidos, --verificar, --forzar, --solo, --seccion)
./venv/camoufox-python scripts/importar_mo2.py        # import to MO2 (--dir, --solo)
./venv/camoufox-python scripts/login_camoufox.py      # login (NEXUS_USER/NEXUS_PASS)
```

## Config

- `~/.config/vnv-linux/` — api_key, nexus_session, cf_clearance, credenciales (all 600)
- `manifest.json` — the 53 mods
- `estado.json` — download states
- `downloads/` — the files
