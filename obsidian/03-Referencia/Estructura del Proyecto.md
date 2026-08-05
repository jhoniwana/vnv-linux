---
tags: [referencia, estructura]
---
# Estructura del Proyecto

```
/home/shot/vnv-linux/
├── vnv.sh                    # orquestador principal (todos los comandos)
├── setup.sh                  # setup multi-distro + wrapper
├── ui.py                     # interfaz web (Flask + SSE)
├── manifest.json             # los 53 mods del Core
├── estado.json               # estados de descarga (auto-generado)
├── BRAIN.md                  # bitácora técnica
├── README.md                 # guía para usuarios
├── MODS_LISTA.md             # links de descarga manual (histórico)
├── downloads/                # los 53 mods (1.1 GB)
├── mods/actualizados.md      # historial de cambios del manifest
├── scripts/
│   ├── login_camoufox.py     # login que pasa Turnstile
│   ├── login_nexus.py        # login manual con ventana (alternativa)
│   ├── login_selenium.py     # alternativa Selenium (no pasa Turnstile)
│   ├── actualizar.py         # metadata de la API (file_ids exactos)
│   ├── gestor_descargas.py   # descargas con estados/retries/re-login
│   ├── importar_mo2.py       # importador automático a MO2
│   ├── descargar_browser.py  # descargador masivo (v1, reemplazado por gestor)
│   ├── descargar_nexus.py    # descargas premium vía API
│   └── descargar_nexus_cookies.py  # flujo cookies (v1)
├── venv/
│   ├── camoufox-python       # wrapper (python + libs correctas)
│   └── libfix/               # pixman conda (fallback, si hace falta)
└── obsidian/                 # esta bóveda
```

## Referencias

- [[Comandos vnv.sh]]
- [[API de Nexus]]
