#!/usr/bin/env python3
"""Generates the Obsidian vault with all the project documentation."""
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
OBS = BASE / "obsidian"

DOCS = {
"obsidian/Inicio.md": """---
tags: [inicio, vnv]
---
# ⚡ Viva New Vegas Linux — Documentation Vault

Project: **100% automatic** installer of the Viva New Vegas Core (53 mods) for Fallout New Vegas on Linux/Steam.

## 🧭 Navigation

- [[Visión General]] — what it is and how it works
- [[Estado Actual]] — what is done and what is missing
- [[Objetivos y Roadmap]] — where it is going

## 📚 Guides (step by step)

1. [[Setup del Entorno]] — prepare the machine (multi-distro)
2. [[Login Nexus]] — automatic account and session
3. [[Descarga de Mods]] — the manager with states and retries
4. [[Importar a MO2]] — convert downloads to the MO2 format
5. [[Conexión Steam]] — Proton + protontricks (step 1)
6. [[Lanzamiento del Juego]] — MO2 Run + LOOT (step 2, theory)

## 🛠️ Reference

- [[Comandos vnv.sh]] — all the commands
- [[Estructura del Proyecto]] — files and scripts
- [[API de Nexus]] — endpoints and limits
- [[Manifest y Mods]] — the 53 Core mods

## 🐛 Troubleshooting

- [[Problemas Comunes]] — typical failures and solutions
- [[Descargas - Troubleshooting]] — Cloudflare and session challenges

## 📅 Log

- [[Cronología]] — development timeline
""",

"obsidian/01-Proyecto/Visión General.md": """---
tags: [proyecto, vnv]
---
# Visión General

Installer that takes the user from **zero to playing** with Viva New Vegas Core on Linux, without touching the terminal:

```
./vnv.sh ui  →  browser with a 6-step wizard
```

## Pipeline

1. **Environment setup** — Python + Camoufox + libraries (Debian/Ubuntu/Arch/Fedora/openSUSE)
2. **Nexus account** — automatic login (Camoufox passes the Cloudflare Turnstile)
3. **Downloads** — 53 mods with a state manager, retries and self-recovery
4. **Connect Steam** — Proton prefix (appid 22380) + protontricks
5. **Install** — MO2-LINT, import mods, INI tweaks, LOOT
6. **Play** — launch FNV with everything loaded

## Principles

- **No terminal** for the end user: everything from the [[Comandos vnv.sh|web UI]]
- **Self-recovery**: if something fails (captcha, session, network), it retries on its own
- **Multi-distro**: detects the system and adapts (with a no-sudo library fallback)
- **Legal**: the mods are downloaded with the user's own session (free, no redistribution)

## Key concepts

- [[Conexión Steam]] — how the modloader connects with Steam
- [[API de Nexus]] — the source of the mods
""",

"obsidian/01-Proyecto/Estado Actual.md": """---
tags: [proyecto, estado]
---
# Estado Actual

## ✅ Done (tested live)

| Component | Status |
|---|---|
| Manifest with 53 mods (correct file_ids) | ✅ |
| Automatic Nexus login (Camoufox passes Turnstile) | ✅ |
| FREE download of the 53 mods (1.1 GB) | ✅ verified, 0 HTML |
| Exact verification vs API (newest MAIN) | ✅ 13 file_ids fixed |
| Download manager (states + retries + re-login) | ✅ |
| Multi-distro setup + library wrapper | ✅ |
| Web UI (6-step wizard, live SSE logs) | ✅ |
| Automatic MO2 importer (53/53) | ✅ |
| `steam` command (Proton diagnostics) | ✅ |

## 🟡 Pending (requires real hardware with the game)

- Test a full `install` on a machine with Steam + FNV (MO2-LINT, Wine, LOOT)
- First game launch with the mods
- Test the setup on real Debian (only tested on Arch)

## 📦 Deliverables

- Repo: `<BASE>/`
- 53 mods in `downloads/` (1.1 GB)
- Technical log: [[Cronología]] and `BRAIN.md`
- This Obsidian vault
""",

"obsidian/01-Proyecto/Objetivos y Roadmap.md": """---
tags: [proyecto, roadmap]
---
# Objetivos y Roadmap

## Final goal

**One single command → play**: `./vnv.sh ui` and the wizard guides by hand until launching Fallout New Vegas with Viva New Vegas Core.

## Roadmap

- [x] Manifest with 53 mods and exact file_ids
- [x] Automatic login (Camoufox headless)
- [x] Complete FREE download + verification
- [x] Robust manager (states, retries, re-login)
- [x] Multi-distro setup
- [x] Web UI without terminal
- [x] Automatic MO2 importer
- [x] Steam/Proton diagnostics (`vnv.sh steam`)
- [ ] Test a real `install` (MO2-LINT on a machine with the game)
- [ ] LOOT + validated first launch
- [ ] Test on Debian
- [ ] Publish the repo on GitHub

## Future ideas

- VNV Extended support (Wabbajack via Jackify)
- Collections of other games (Fallout 4, Skyrim) with the same framework
- Installer of the UI as an app (Electron/Tauri) or .desktop
""",

"obsidian/02-Guías/Setup del Entorno.md": """---
tags: [guia, setup, multi-distro]
---
# Setup del Entorno

> Prepares the machine on any Linux distro. It runs only from the UI (step 1) or with `./vnv.sh setup`.

## What `setup.sh` does

1. **Detects the distro** (`/etc/os-release`)
2. **System dependencies**: shows (or installs with sudo if available) the packages for GTK3, NSS, cairo, pixman, protontricks...
   - Debian/Ubuntu: `apt install ... protontricks`
   - Arch: `pacman -S ... protontricks`
   - Fedora: `dnf install ... protontricks`
3. **Venv + Camoufox + Flask**
4. **Smoke test**: does Camoufox start with the system libs?
   - If it fails (broken libs, typical of Arch with a partial update): **automatic fallback** → micromamba user-space (no sudo) with pixman → `venv/camoufox-python` wrapper that resolves the libraries
5. **Verifies the Nexus session** (cookies)

## The `venv/camoufox-python` wrapper

It is the project's Python interpreter: it exports the correct `LD_LIBRARY_PATH` (cleans the contaminated one) and runs the venv python. **All scripts use the wrapper.**

## Minimum requirements

- Python 3.10+
- ~4 GB of disk
- Steam with Fallout New Vegas

## References

- [[Login Nexus]] — next step
- [[Problemas Comunes]] — if something fails
""",

"obsidian/02-Guías/Login Nexus.md": """---
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
""",

"obsidian/02-Guías/Descarga de Mods.md": """---
tags: [guia, descargas, nexus]
---
# Descarga de Mods

The `gestor_descargas.py` manager downloads the 53 Core mods with **states, retries and self-recovery**.

## The key discovery

The Nexus API gives download links **only to Premium**. The "Manual download" button of the site:

- Is in the **shadow DOM** of a web component (`<mod-download-modal>`) — invisible to normal DOM dumps
- The real endpoint (found by reading the Nexus JS bundle): **`/Download/?id={file_id}&game_id=130&source=ModPage`**

That page shows "Your file will be served via CDN" + a **Download** button — and it works for **free accounts**.

## Two page formats

| Text | Behavior |
|---|---|
| "Your download should automatically begin within a few seconds" | **Auto-download** (no button) |
| "Your file will be served via CDN" | **Download button** (it must be clicked) |

The manager handles both: waits 12s for the auto-download → if not, clicks the exact button (anchored to the "served via CDN" text).

## Manager robustness

- **Persisted states** in `estado.json`: `pending → downloading → ok/fail`
- **3 attempts** per mod with backoff (15s/30s)
- **Challenge waits** for Cloudflare (up to 60s)
- **Expired session detection** → automatic re-login → retry
- **Integrity verification** (`file` not-HTML, minimum size)
- Human rate limits (8-15s between mods)

## Commands

```bash
./vnv.sh download          # downloads what is pending
./vnv.sh estado            # verifies the 53 files
./venv/camoufox-python scripts/gestor_descargas.py --solo-fallidos
./venv/camoufox-python scripts/gestor_descargas.py --forzar --solo 57174
```

## References

- [[Login Nexus]] — the session that makes the download possible
- [[Descargas - Troubleshooting]] — solved problems
- [[Importar a MO2]] — next step
""",

"obsidian/02-Guías/Importar a MO2.md": """---
tags: [guia, mo2, importar]
---
# Importar a MO2

Converts the downloaded files to the format Mod Organizer 2 understands — **automatically**.

## MO2 format

```
~/.local/share/modorganizer2/
├── mods/<ModName>/          ← extracted mod
├── profiles/Default/
│   ├── modlist.txt          ← mod order (active with +)
│   └── loadorder.txt        ← plugin order (generated by LOOT)
└── downloads/               ← original files (reference)
```

## What `importar_mo2.py` does

1. For each file in `downloads/`: extracts it into `mods/<ModName>/`
   - `.7z`/`.rar` → system 7z
   - `.zip` → Python stdlib (safe against path traversal)
2. **Cleans junk**: `__MACOSX`, `.DS_Store`, `Thumbs.db`
3. **Flattens** the single root folder (many mods come wrapped)
4. **Deletes empty folders**
5. Writes `modlist.txt` with the manifest order (setup → utilities → bugfix → finish), all active

## Tested

**53/53 mods imported** with the correct structure:
- UIO → `nvse/plugins/ui_organizer.dll` + `uio/settings.ini`
- FaceGen (.rar) and MAC-10 (large zip) also OK

## Commands

```bash
./venv/camoufox-python scripts/importar_mo2.py              # detects MO2
./venv/camoufox-python scripts/importar_mo2.py --dir ~/mo2  # custom directory
```

## References

- [[Descarga de Mods]] — where the files come from
- [[Conexión Steam]] — where MO2 lives in the flow
""",

"obsidian/02-Guías/Conexión Steam.md": """---
tags: [guia, steam, proton, mo2]
---
# Conexión Steam ↔ MO2

How the modloader connects with Steam (step 1 of the install flow).

## Reality: there is no native modloader

- **MO2/Vortex**: Windows .NET apps → run with **Wine/Proton**
- **NexusMods.App** (official): native Linux but does **NOT support FNV** (only FO4, Cyberpunk, etc.)
- Conclusion: **MO2 via Proton is the standard**

## The mechanism

```
Steam (FNV, appid 22380)
   │  force Proton (Steam Play)
   ▼
Game Proton prefix (steamapps/compatdata/22380/pfx)
   │  protontricks: MO2 runs INSIDE that prefix
   ▼
MO2 → Run button → FalloutNV.exe with the mods mounted (VFS)
```

- **Protontricks** = the key piece: runs programs in the Proton prefix of a game
- **MO2-LINT** automates: `mo2-installer install --game fallout-new-vegas`
- **MO2 VFS**: the mods are mounted virtually — the game directory is NOT modified

## Command

```bash
./vnv.sh steam          # diagnoses Steam, FNV, prefix, protontricks
./vnv.sh steam --si     # also launches FNV with Proton to create the prefix (non-interactive)
```

## If the prefix does not exist

1. Steam → FNV → Properties → Compatibility → force Proton
2. Play once (creates the prefix) — or run `./vnv.sh steam --si`

## References

- [[Lanzamiento del Juego]] — what to do next
- [[Problemas Comunes]]
""",

"obsidian/02-Guías/Lanzamiento del Juego.md": """---
tags: [guia, lanzamiento, mo2, teoria]
---
# Lanzamiento del Juego

> ⚠️ **Theory** — this step requires real hardware with Steam + FNV. Not tested yet.

## Complete sequence

1. `mo2-installer install --game fallout-new-vegas` → MO2 in the game prefix
2. `mo2-installer run --game fallout-new-vegas` → opens MO2 with the game's Wine environment
3. The "Default" profile already has the 53 mods imported ([[Importar a MO2]])
4. **LOOT** (first time): Sort button in MO2 → orders plugins → writes `loadorder.txt`
5. **Run** in MO2 → launches `FalloutNV.exe` with the VFS (mods mounted virtually)
6. NVTF applies heap + 4GB + vsync from `Data/NVSE/Plugins/nvtf.ini` (written by `tweaks_ini`)
7. FNV on Proton: **fullscreen-only** — the VNV guide recommends fullscreen + NVTF

## Troubleshooting

| Problem | Solution |
|---|---|
| Crash on start | Check `nvtf.ini` (EnableHeapReplacement) and NVTF active in the modlist |
| No mods loaded | Launch FROM MO2 (not directly from Steam); Default profile active |
| Black screen | Fullscreen; try Proton GE |
| LOOT does not sort | Run LOOT from MO2; reinstall with `mo2-installer install` |

## References

- [[Conexión Steam]] — previous step
- [[Problemas Comunes]]
""",

"obsidian/03-Referencia/Comandos vnv.sh.md": """---
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
""",

"obsidian/03-Referencia/Estructura del Proyecto.md": """---
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
""",

"obsidian/03-Referencia/API de Nexus.md": """---
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
""",

"obsidian/03-Referencia/Manifest y Mods.md": """---
tags: [referencia, mods]
---
# Manifest y Mods

The Viva New Vegas Core = **53 mods** from Nexus (all downloaded and verified).

## Manifest structure

```json
{
  "mod_id": 57174,
  "seccion": "utilities",
  "nombre": "UIO - User Interface Organizer",
  "file_id": 1000080073,
  "version": "2.30"
}
```

## Sections

- **setup** — tools (steam-library-setup-tool, GitHub)
- **utilities** — NVSE, JIP LN, NVTF, xNVSE, UIO...
- **bugfix** — YUP, Stewie Tweaks (66347), mesh fixes...
- **finish** — Stewie Tweaks INIs (GitHub: ModdingLinked/Stewie-Tweaks-INIs)

## Important data

- The correct file_id = **newest MAIN** by `uploaded_timestamp` (bug fixed: it used to pick the first one → 13 mods with an old version)
- **FNV 4GB Patcher**: use the **"FNV4GB for Proton"** file (Linux/Wine version)
- **JIP LN**: the plugin (v57.30) ≠ the INI (v56.24) — the guide needs the PLUGIN
- Stewie Tweaks: mod 66347 (90824 is hidden by the author)

## References

- [[Descarga de Mods]]
- [[Estado Actual]]
""",

"obsidian/04-Troubleshooting/Problemas Comunes.md": """---
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
""",

"obsidian/04-Troubleshooting/Descargas - Troubleshooting.md": """---
tags: [troubleshooting, descargas]
---
# Descargas — Troubleshooting

## Errors found and solved

### 1. "Manual download" not automatable (2026)
**Symptom**: the file rows have no download button in the DOM.
**Cause**: it is in the shadow DOM of `<mod-download-modal>` (web component).
**Solution**: `/Download/?id={fid}&game_id=130` endpoint discovered in the JS bundle.

### 2. The downloader fetched old versions
**Symptom**: 44 version deviations; JIP LN downloaded the INI instead of the plugin.
**Cause**: `actualizar.py` picked the FIRST MAIN file, not the newest one.
**Solution**: `max(mains, key=uploaded_timestamp)` → 13 file_ids fixed.

### 3. Expired session not detected
**Symptom**: the re-login did not trigger.
**Cause**: it searched for "Sign in" but Nexus uses **"Log in"** for non-authenticated users.
**Solution**: detect both + absence of "served via CDN".

### 4. Massive page.goto timeouts (Cloudflare)
**Symptom**: 25 mods failed with timeouts after fast downloads.
**Cause**: Cloudflare rate limiting.
**Solution**: challenge wait (up to 60s) + 3 attempts with backoff + 8-15s pace.

### 5. Duplicated manifest (66347 ×2)
**Cause**: replacing 90824→66347 without noticing it already existed.
**Solution**: deduplication → 53 unique mods.

## Monitoring

```bash
./venv/camoufox-python scripts/gestor_descargas.py --verificar   # integrity
cat estado.json                                                   # states per mod
tail /tmp/descarga.log                                           # log of a run
```

> ⚠️ Do not launch two instances writing to the same log file (they overwrite each other).

## References

- [[Descarga de Mods]]
- [[Problemas Comunes]]
""",

"obsidian/05-Bitácora/Cronología.md": """---
tags: [bitacora]
---
# Cronología

## 5 August 2026 — Big day

- **FREE download solved**: `/Download/` endpoint discovered (after the user insisted on "Manual download")
- 53/53 mods downloaded and verified (1.1 GB)
- **Exact verification**: file_ids bug fixed (13 mods), newest MAIN
- **Robust manager**: states, retries, automatic re-login (tested: session deleted → it recovered by itself)
- **Multi-distro setup** + library wrapper (smoke test + micromamba fallback)
- **Web UI**: 6-step wizard with live SSE — no terminal
- **Automatic MO2 importer**: 53/53 imported
- **Steam connection**: `steam` command + protontricks + launch theory
- **Obsidian vault** created

## Key discoveries (5 Aug)

| Discovery | Impact |
|---|---|
| Camoufox passes the Turnstile headless | Automatic login ✅ |
| The real cookie is `nexusmods_session` (not `sid`) | Downloads ✅ |
| Free `/Download/?id=...` endpoint | 53 mods without Premium ✅ |
| "Log in" ≠ "Sign in" | Automatic re-login ✅ |
| Newest MAIN by timestamp | Exact file_ids ✅ |

## Previous phase (2-4 August)

- Exploration: Playwright, Selenium UC, LightPanda (none passed the Turnstile)
- Xvfb/conda: dead end (broken libs) → solved with the wrapper
- "Wabbajack-style" login (real window) documented as an alternative

## See also

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
    print(f"✅ Obsidian vault generated: {n} files in {OBS}")


if __name__ == "__main__":
    main()
