---
tags: [referencia, estructura]
---
# Estructura del Proyecto

```
<BASE>/
├── vnv.sh                    # main orchestrator (all commands)
├── setup.sh                  # multi-distro setup + wrapper
├── ui.py                     # web interface (Flask + SSE)
├── manifest.json             # the 53 Core mods
├── estado.json               # download states (auto-generated)
├── BRAIN.md                  # technical log
├── README.md                 # guide for users
├── MODS_LISTA.md             # manual download links (historical)
├── downloads/                # the 53 mods (1.1 GB)
├── mods/actualizados.md      # manifest change history
├── scripts/
│   ├── login_camoufox.py     # login that passes Turnstile
│   ├── login_nexus.py        # manual login with a window (alternative)
│   ├── login_selenium.py     # Selenium alternative (does not pass Turnstile)
│   ├── actualizar.py         # API metadata (exact file_ids)
│   ├── gestor_descargas.py   # downloads with states/retries/re-login
│   ├── importar_mo2.py       # automatic MO2 importer
│   ├── descargar_browser.py  # massive downloader (v1, replaced by the manager)
│   ├── descargar_nexus.py    # premium downloads via API
│   └── descargar_nexus_cookies.py  # cookies flow (v1)
├── venv/
│   ├── camoufox-python       # wrapper (python + correct libs)
│   └── libfix/               # pixman conda (fallback, if needed)
└── obsidian/                 # this vault
```

## References

- [[Comandos vnv.sh]]
- [[API de Nexus]]
