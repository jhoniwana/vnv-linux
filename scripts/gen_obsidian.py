#!/usr/bin/env python3
"""Genera la bóveda de Obsidian con toda la documentación del proyecto."""
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
OBS = BASE / "obsidian"

DOCS = {
"obsidian/Inicio.md": """---
tags: [inicio, vnv]
---
# ⚡ Viva New Vegas Linux — Bóveda de Documentación

Proyecto: instalador **100% automático** del Core de Viva New Vegas (53 mods) para Fallout New Vegas en Linux/Steam.

## 🧭 Navegación

- [[Visión General]] — qué es y cómo funciona
- [[Estado Actual]] — qué está hecho y qué falta
- [[Objetivos y Roadmap]] — hacia dónde va

## 📚 Guías (paso a paso)

1. [[Setup del Entorno]] — preparar la máquina (multi-distro)
2. [[Login Nexus]] — cuenta y sesión automática
3. [[Descarga de Mods]] — el gestor con estados y retries
4. [[Importar a MO2]] — convertir descargas al formato MO2
5. [[Conexión Steam]] — Proton + protontricks (paso 1)
6. [[Lanzamiento del Juego]] — MO2 Run + LOOT (paso 2, teoría)

## 🛠️ Referencia

- [[Comandos vnv.sh]] — todos los comandos
- [[Estructura del Proyecto]] — archivos y scripts
- [[API de Nexus]] — endpoints y límites
- [[Manifest y Mods]] — los 53 mods del Core

## 🐛 Troubleshooting

- [[Problemas Comunes]] — fallos típicos y soluciones
- [[Descargas - Troubleshooting]] — desafíos de Cloudflare y sesión

## 📅 Bitácora

- [[Cronología]] — línea de tiempo del desarrollo
""",

"obsidian/01-Proyecto/Visión General.md": """---
tags: [proyecto, vnv]
---
# Visión General

Instalador que lleva al usuario de **cero a jugar** con Viva New Vegas Core en Linux, sin tocar la terminal:

```
./vnv.sh ui  →  navegador con wizard de 6 pasos
```

## Pipeline

1. **Setup del entorno** — Python + Camoufox + librerías (Debian/Ubuntu/Arch/Fedora/openSUSE)
2. **Cuenta Nexus** — login automático (Camoufox pasa el Turnstile de Cloudflare)
3. **Descargas** — 53 mods con gestor de estados, reintentos y auto-recuperación
4. **Conectar Steam** — prefix de Proton (appid 22380) + protontricks
5. **Instalar** — MO2-LINT, importar mods, INI tweaks, LOOT
6. **Jugar** — lanzar FNV con todo cargado

## Principios

- **Sin terminal** para el usuario final: todo desde la [[Comandos vnv.sh|UI web]]
- **Auto-recuperación**: si algo falla (captcha, sesión, red), reintenta solo
- **Multi-distro**: detecta el sistema y se adapta (con fallback de librerías sin sudo)
- **Legal**: los mods se descargan con la sesión del propio usuario (gratis, sin redistribuir)

## Conceptos clave

- [[Conexión Steam]] — cómo se conecta el modloader con Steam
- [[API de Nexus]] — la fuente de los mods
""",

"obsidian/01-Proyecto/Estado Actual.md": """---
tags: [proyecto, estado]
---
# Estado Actual

## ✅ Completado (probado en vivo)

| Componente | Estado |
|---|---|
| Manifest con 53 mods (file_id correctos) | ✅ |
| Login Nexus automático (Camoufox pasa Turnstile) | ✅ |
| Descarga FREE de los 53 mods (1.1 GB) | ✅ verificados, 0 HTML |
| Verificación exacta vs API (MAIN más reciente) | ✅ 13 file_ids corregidos |
| Gestor de descargas (estados + retries + re-login) | ✅ |
| Setup multi-distro + wrapper de librerías | ✅ |
| UI web (wizard 6 pasos, logs en vivo SSE) | ✅ |
| Importador automático a MO2 (53/53) | ✅ |
| Comando `steam` (diagnóstico Proton) | ✅ |

## 🟡 Pendiente (requiere hardware real con el juego)

- Probar `install` completo en máquina con Steam + FNV (MO2-LINT, Wine, LOOT)
- Primer lanzamiento del juego con los mods
- Probar el setup en Debian real (solo probado en Arch)

## 📦 Entregables

- Repo: `<BASE>/`
- 53 mods en `downloads/` (1.1 GB)
- Bitácora técnica: [[Cronología]] y `BRAIN.md`
- Esta bóveda de Obsidian
""",

"obsidian/01-Proyecto/Objetivos y Roadmap.md": """---
tags: [proyecto, roadmap]
---
# Objetivos y Roadmap

## Objetivo final

**Un solo comando → jugar**: `./vnv.sh ui` y el wizard lleva de la mano hasta lanzar Fallout New Vegas con Viva New Vegas Core.

## Roadmap

- [x] Manifest 53 mods con file_ids exactos
- [x] Login automático (Camoufox headless)
- [x] Descarga FREE completa + verificación
- [x] Gestor robusto (estados, retries, re-login)
- [x] Setup multi-distro
- [x] UI web sin terminal
- [x] Importador MO2 automático
- [x] Diagnóstico Steam/Proton (`vnv.sh steam`)
- [ ] Probar `install` real (MO2-LINT en máquina con el juego)
- [ ] LOOT + primer lanzamiento validado
- [ ] Probar en Debian
- [ ] Publicar repo en GitHub

## Ideas futuras

- Soporte de VNV Extended (Wabbajack vía Jackify)
- Colecciones de otros juegos (Fallout 4, Skyrim) con el mismo framework
- Instalador de la UI como app (Electron/Tauri) o .desktop
""",

"obsidian/02-Guías/Setup del Entorno.md": """---
tags: [guia, setup, multi-distro]
---
# Setup del Entorno

> Prepara la máquina en cualquier distro Linux. Se ejecuta solo desde la UI (paso 1) o con `./vnv.sh setup`.

## Qué hace `setup.sh`

1. **Detecta la distro** (`/etc/os-release`)
2. **Dependencias del sistema**: muestra (o instala con sudo si está disponible) los paquetes para GTK3, NSS, cairo, pixman, protontricks...
   - Debian/Ubuntu: `apt install ... protontricks`
   - Arch: `pacman -S ... protontricks`
   - Fedora: `dnf install ... protontricks`
3. **Venv + Camoufox + Flask**
4. **Smoke test**: ¿Camoufox arranca con las libs del sistema?
   - Si falla (libs rotas, típico de Arch con update parcial): **fallback automático** → micromamba user-space (sin sudo) con pixman → wrapper `venv/camoufox-python` que resuelve las librerías
5. **Verifica la sesión de Nexus** (cookies)

## El wrapper `venv/camoufox-python`

Es el intérprete de Python del proyecto: exporta el `LD_LIBRARY_PATH` correcto (limpia el contaminado) y ejecuta el python del venv. **Todos los scripts usan el wrapper.**

## Requisitos mínimos

- Python 3.10+
- ~4 GB de disco
- Steam con Fallout New Vegas

## Referencias

- [[Login Nexus]] — siguiente paso
- [[Problemas Comunes]] — si algo falla
""",

"obsidian/02-Guías/Login Nexus.md": """---
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
""",

"obsidian/02-Guías/Descarga de Mods.md": """---
tags: [guia, descargas, nexus]
---
# Descarga de Mods

El gestor `gestor_descargas.py` descarga los 53 mods del Core con **estados, reintentos y auto-recuperación**.

## El descubrimiento clave

La API de Nexus da links de descarga **solo a Premium**. El botón "Manual download" de la web:

- Está en el **shadow DOM** de un web component (`<mod-download-modal>`) — invisible para dumps DOM normales
- El endpoint real (encontrado leyendo el bundle JS de Nexus): **`/Download/?id={file_id}&game_id=130&source=ModPage`**

Esa página muestra "Your file will be served via CDN" + botón **Download** — y funciona para **cuentas gratis**.

## Dos formatos de página

| Texto | Comportamiento |
|---|---|
| "Your download should automatically begin within a few seconds" | **Auto-descarga** (no hay botón) |
| "Your file will be served via CDN" | **Botón Download** (hay que clickearlo) |

El gestor maneja ambos: espera 12s la auto-descarga → si no, clickea el botón exacto (anclado al texto "served via CDN").

## Robustez del gestor

- **Estados persistidos** en `estado.json`: `pendiente → descargando → ok/fallo`
- **3 intentos** por mod con backoff (15s/30s)
- **Espera de challenges** de Cloudflare (hasta 60s)
- **Detección de sesión expirada** → re-login automático → reintenta
- **Verificación de integridad** (`file` no-HTML, tamaño mínimo)
- Rate limits humanos (8-15s entre mods)

## Comandos

```bash
./vnv.sh download          # descarga lo pendiente
./vnv.sh estado            # verifica los 53 archivos
./venv/camoufox-python scripts/gestor_descargas.py --solo-fallidos
./venv/camoufox-python scripts/gestor_descargas.py --forzar --solo 57174
```

## Referencias

- [[Login Nexus]] — la sesión que hace posible la descarga
- [[Descargas - Troubleshooting]] — problemas resueltos
- [[Importar a MO2]] — siguiente paso
""",

"obsidian/02-Guías/Importar a MO2.md": """---
tags: [guia, mo2, importar]
---
# Importar a MO2

Convierte los archivos descargados al formato que Mod Organizer 2 entiende — **automáticamente**.

## Formato de MO2

```
~/.local/share/modorganizer2/
├── mods/<NombreMod>/            ← mod descomprimido
├── profiles/Default/
│   ├── modlist.txt              ← orden de mods (activos con +)
│   └── loadorder.txt            ← orden de plugins (lo genera LOOT)
└── downloads/                   ← archivos originales (referencia)
```

## Qué hace `importar_mo2.py`

1. Para cada archivo en `downloads/`: descomprime en `mods/<NombreMod>/`
   - `.7z`/`.rar` → 7z del sistema
   - `.zip` → stdlib de Python (seguro contra path traversal)
2. **Limpia basura**: `__MACOSX`, `.DS_Store`, `Thumbs.db`
3. **Aplana** la carpeta raíz única (muchos mods vienen envueltos)
4. **Borra carpetas vacías**
5. Escribe `modlist.txt` con el orden del manifest (setup → utilities → bugfix → finish), todos activos

## Probado

**53/53 mods importados** con estructura correcta:
- UIO → `nvse/plugins/ui_organizer.dll` + `uio/settings.ini`
- FaceGen (.rar) y MAC-10 (zip grande) también OK

## Comandos

```bash
./venv/camoufox-python scripts/importar_mo2.py              # detecta MO2
./venv/camoufox-python scripts/importar_mo2.py --dir ~/mo2  # directorio custom
```

## Referencias

- [[Descarga de Mods]] — de dónde vienen los archivos
- [[Conexión Steam]] — dónde vive MO2 en el flujo
""",

"obsidian/02-Guías/Conexión Steam.md": """---
tags: [guia, steam, proton, mo2]
---
# Conexión Steam ↔ MO2

Cómo se conecta el modloader con Steam (paso 1 del flujo de instalación).

## Realidad: no hay modloader nativo

- **MO2/Vortex**: apps .NET de Windows → corren con **Wine/Proton**
- **NexusMods.App** (oficial): nativa Linux pero **NO soporta FNV** (solo FO4, Cyberpunk, etc.)
- Conclusión: **MO2 vía Proton es el estándar**

## El mecanismo

```
Steam (FNV, appid 22380)
   │  forzar Proton (Steam Play)
   ▼
Prefix de Proton del juego (steamapps/compatdata/22380/pfx)
   │  protontricks: MO2 corre DENTRO de ese prefix
   ▼
MO2 → botón Run → FalloutNV.exe con los mods montados (VFS)
```

- **Protontricks** = la pieza clave: ejecuta programas en el prefix de Proton de un juego
- **MO2-LINT** automatiza: `mo2-installer install --game fallout-new-vegas`
- **VFS de MO2**: los mods se montan virtualmente — el directorio del juego NO se modifica

## Comando

```bash
./vnv.sh steam          # diagnostica Steam, FNV, prefix, protontricks
./vnv.sh steam --si     # además lanza FNV con Proton para crear el prefix (no-interactivo)
```

## Si el prefix no existe

1. Steam → FNV → Propiedades → Compatibilidad → forzar Proton
2. Jugar una vez (crea el prefix) — o correr `./vnv.sh steam --si`

## Referencias

- [[Lanzamiento del Juego]] — qué hacer después
- [[Problemas Comunes]]
""",

"obsidian/02-Guías/Lanzamiento del Juego.md": """---
tags: [guia, lanzamiento, mo2, teoria]
---
# Lanzamiento del Juego

> ⚠️ **Teoría** — este paso requiere hardware real con Steam + FNV. No probado aún.

## Secuencia completa

1. `mo2-installer install --game fallout-new-vegas` → MO2 en el prefix del juego
2. `mo2-installer run --game fallout-new-vegas` → abre MO2 con el entorno Wine del juego
3. El perfil "Default" ya tiene los 53 mods importados ([[Importar a MO2]])
4. **LOOT** (primera vez): botón Sort en MO2 → ordena plugins → escribe `loadorder.txt`
5. **Run** en MO2 → lanza `FalloutNV.exe` con el VFS (mods montados virtualmente)
6. NVTF aplica heap + 4GB + vsync desde `Data/NVSE/Plugins/nvtf.ini` (lo escribe `tweaks_ini`)
7. FNV en Proton: **fullscreen-only** — la guía VNV recomienda fullscreen + NVTF

## Troubleshooting

| Problema | Solución |
|---|---|
| Crash al inicio | Verificar `nvtf.ini` (EnableHeapReplacement) y NVTF activo en el modlist |
| Sin mods cargados | Lanzar DESDE MO2 (no desde Steam directo); perfil Default activo |
| Pantalla negra | Fullscreen; probar Proton GE |
| LOOT no ordena | Correr LOOT desde MO2; reinstalar con `mo2-installer install` |

## Referencias

- [[Conexión Steam]] — paso previo
- [[Problemas Comunes]]
""",

"obsidian/03-Referencia/Comandos vnv.sh.md": """---
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
""",

"obsidian/03-Referencia/Estructura del Proyecto.md": """---
tags: [referencia, estructura]
---
# Estructura del Proyecto

```
<BASE>/
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
""",

"obsidian/03-Referencia/API de Nexus.md": """---
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
""",

"obsidian/03-Referencia/Manifest y Mods.md": """---
tags: [referencia, mods]
---
# Manifest y Mods

El Core de Viva New Vegas = **53 mods** de Nexus (todos descargados y verificados).

## Estructura del manifest

```json
{
  "mod_id": 57174,
  "seccion": "utilities",
  "nombre": "UIO - User Interface Organizer",
  "file_id": 1000080073,
  "version": "2.30"
}
```

## Secciones

- **setup** — herramientas (steam-library-setup-tool, GitHub)
- **utilities** — NVSE, JIP LN, NVTF, xNVSE, UIO...
- **bugfix** — YUP, Stewie Tweaks (66347), mesh fixes...
- **finish** — Stewie Tweaks INIs (GitHub: ModdingLinked/Stewie-Tweaks-INIs)

## Datos importantes

- El file_id correcto = **MAIN más reciente** por `uploaded_timestamp` (bug corregido: antes elegía el primero → 13 mods con versión vieja)
- **FNV 4GB Patcher**: usar el archivo **"FNV4GB for Proton"** (versión Linux/Wine)
- **JIP LN**: el plugin (v57.30) ≠ el INI (v56.24) — la guía necesita el PLUGIN
- Stewie Tweaks: mod 66347 (el 90824 está hidden por el autor)

## Referencias

- [[Descarga de Mods]]
- [[Estado Actual]]
""",

"obsidian/04-Troubleshooting/Problemas Comunes.md": """---
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
""",

"obsidian/04-Troubleshooting/Descargas - Troubleshooting.md": """---
tags: [troubleshooting, descargas]
---
# Descargas — Troubleshooting

## Errores encontrados y resueltos

### 1. "Manual download" no automatizable (2026)
**Síntoma**: las filas de archivos no tienen botón de descarga en el DOM.
**Causa**: está en el shadow DOM de `<mod-download-modal>` (web component).
**Solución**: endpoint `/Download/?id={fid}&game_id=130` descubierto en el bundle JS.

### 2. El descargador bajaba versiones viejas
**Síntoma**: 44 desviaciones de versión; JIP LN bajó el INI en vez del plugin.
**Causa**: `actualizar.py` elegía el PRIMER archivo MAIN, no el más reciente.
**Solución**: `max(mains, key=uploaded_timestamp)` → 13 file_ids corregidos.

### 3. Sesión expirada no detectada
**Síntoma**: el re-login no se disparaba.
**Causa**: buscaba "Sign in" pero Nexus usa **"Log in"** para no-autenticados.
**Solución**: detectar ambos + ausencia de "served via CDN".

### 4. Page.goto timeouts masivos (Cloudflare)
**Síntoma**: 25 mods fallaron con timeouts tras descargas rápidas.
**Causa**: rate limiting de Cloudflare.
**Solución**: espera de challenge (hasta 60s) + 3 intentos con backoff + ritmo 8-15s.

### 5. Manifest duplicado (66347 ×2)
**Causa**: al reemplazar 90824→66347 sin notar que ya existía.
**Solución**: deduplicación → 53 mods únicos.

## Monitoreo

```bash
./venv/camoufox-python scripts/gestor_descargas.py --verificar   # integridad
cat estado.json                                                   # estados por mod
tail /tmp/descarga.log                                           # log de una corrida
```

> ⚠️ No lanzar dos instancias al mismo archivo de log (se pisan).

## Referencias

- [[Descarga de Mods]]
- [[Problemas Comunes]]
""",

"obsidian/05-Bitácora/Cronología.md": """---
tags: [bitacora]
---
# Cronología

## 5 agosto 2026 — Día grande

- **Descarga FREE resuelta**: endpoint `/Download/` descubierto (tras insistencia del usuario con "Manual download")
- 53/53 mods descargados y verificados (1.1 GB)
- **Verificación exacta**: bug de file_ids corregido (13 mods), MAIN más reciente
- **Gestor robusto**: estados, retries, re-login automático (probado: sesión borrada → se recuperó solo)
- **Setup multi-distro** + wrapper de librerías (smoke test + fallback micromamba)
- **UI web**: wizard 6 pasos con SSE en vivo — sin terminal
- **Importador MO2 automático**: 53/53 importados
- **Conexión Steam**: comando `steam` + protontricks + teoría del lanzamiento
- **Bóveda de Obsidian** creada

## Descubrimientos clave (5 ago)

| Descubrimiento | Impacto |
|---|---|
| Camoufox pasa el Turnstile headless | Login automático ✅ |
| Cookie real = `nexusmods_session` (no `sid`) | Descargas ✅ |
| Endpoint `/Download/?id=...` gratis | 53 mods sin Premium ✅ |
| "Log in" ≠ "Sign in" | Re-login automático ✅ |
| MAIN más reciente por timestamp | File_ids exactos ✅ |

## Fase previa (2-4 agosto)

- Exploración: Playwright, Selenium UC, LightPanda (ninguno pasó el Turnstile)
- Xvfb/conda: callejón sin salida (libs rotas) → resuelto con wrapper
- Login "estilo Wabbajack" (ventana real) documentado como alternativa

## Ver también

- [[Estado Actual]]
- [[Objetivos y Roadmap]]
""",
}

def main():
    n = 0
    for ruta, contenido in DOCS.items():
        p = BASE / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido.strip() + "\n")
        n += 1
    print(f"✅ Bóveda de Obsidian generada: {n} archivos en {OBS}")


if __name__ == "__main__":
    main()
