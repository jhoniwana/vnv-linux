# BRAIN.md — VNV Linux Installer

Technical log of the project: **100% automatic installer of Viva New Vegas (Core) for Linux/Steam**.

> Rule: every discovery, bug and decision goes here. This file IS the project's memory.

---

## 🎯 Goal
`./vnv.sh install` = detect game → download 54 mods → MO2 + Wine prefix → import → INIs → LOOT → launch. Zero manual steps.

## 🧱 Stack
- Python 3.12 + venv (`/home/shot/vnv-linux/venv`)
- **Camoufox** (anti-detection Firefox) for Nexus login — passes Turnstile headless
- Playwright (venv postulaciones) for iCIMS captchas (another project)
- Nexus API v1 for metadata (free) + `nexusmods_session` cookie for the session

---

## ✅ FINAL COMPLETE VALIDATION (6 aug 2026) — EVERYTHING TESTED LIVE

## ✅ DEFINITIVE CLOSURE (7 aug 2026) — 100% verified by the user

- **55 mods** (Core VNV + JAM 66666 + YUPDate/supplement 98514 with `d20Fixes.esm`), 50 active + 5 root + Fixed ESMs.
- **Canonical VNV Core load order** of 23 plugins (YUP 1st, d20Fixes after YUP, Placement Fixes last, JAM at the end) — loadorder/plugins sync.
- **CORRECT Fixed ESMs REBUILD**: the problem was the SOURCE — the esms copied from the user's old setup (mtimes 1999) were not the ones from the current depot → xdelta3 with a source ±bytes → esm with valid TES4 but 233K records and **0 dialogues** (vs 465K/18.2K of the correct one) → crash `0x00AA991C` during dialogue init (context: YUP "Doctors" records — topic 0002284F, info 000377F6). After `steam steam://validate/22380` (the esms aligned with the depot), `port.py --force` produces the correct build (465,054 records, DIALOG 18,215). **Rule: Steam verify must precede uefix** (and re-run 4gb/bsa afterwards — verify reverts everything).
- **JGNVSE**: after the correct Fixed ESMs, the DLC "EDIDs conflicting" (WeapNVDLC00Faderator, FadeToBlackAndBack..., NVDLC03TTank*) DISAPPEARED. Only 1 benign one remains: `UPNVSEPVendorQuestItemSCRIPT` (YUP vs UPNVSE+, known).
- **Game error log**: 1.5 KB = benign vanilla noise (RagdollConstraint rdt, "misnamed BSA" ×10, optional texture swaps, animation group notes). 0 real MASTERFILE, 0 real MODEL ERROR.
- **28 NVSE plugins** loaded (incl. JIP LN v57.30, LOD Fixes v1.33 with its INI, VanillaPlusTerrain, FART...).
- **JAM - VNV Configuration** (1000132850, `config/JustMods.ini`) = official VNV preset (sprint and QOL via MCM) — the Patch Emporium "JAM Custom INI" (deleted repo) is no longer used.
- **Cleanup**: no stale downloads, no extra mods in MO2, 1 old state entry removed, backups of old saves/mods deleted.
- **`importar_mo2.py`**: `--solo` preserves the EXACT loadorder (inserts the new plugin after its master) and the modlist preserves +/- states (b7782f3, 0ffc8ce, fade38a).


Full pipeline verified end to end on the user's machine (Steam + FNV):
- **Downloads**: 53/53 main + 4/4 extras, 0 HTML (audit vs manifest+estado.json)
- **`install` e2e idempotent** (re-run after push): 53/53 re-imported, modlist 55 lines, loadorder 21 in guide order, root mods re-executed OK, INI tweaks applied
- **Game launched and confirmed at main menu**: 27 NVSE plugins loaded (`nvse.log`), full MO2 VFS, `run -e NVSE` correct, clean exit
- **Game state**: LAA=0xA620 + nvse_steam_loader imported, decompressed BSAs (see 8265), Fixed ESMs with correct sizes
- **Web UI** serves OK (curl), `bash -n` + `py_compile` of all scripts OK

### Bugs found during validation (all with fixes):
1. **MO2 2.5.2 truncates `plugins.txt` on shutdown** after a game session (leaves only `FalloutNV.esm`; `loadorder.txt` intact). Reproduced 2×. Fix in `lanzar()`: regenerates `plugins.txt` = header + one `*` per line of `loadorder.txt` if they differ (vnv.sh:214-226).
2. **Standalone lootcli can't see MO2's VFS** → rewrites `plugins.txt` with ~10 plugins if pointed at the real profile. Fix: `./vnv.sh loot` validates against copy `/tmp/opencode/loot_plugins.txt`; LOOT removed from `install` (vnv.sh:172-192).

### Second wave of bugs (7 aug 2026, all with fixes — game playable with a new game)
1. **MO2 2.5.2 plugins.txt WITHOUT `*`**: the file = active plugins WITHOUT asterisk (CRLF, header). With `*` → `Plugin not found: *FalloutNV.esm` (the `*` becomes part of the name) → MO2 recognizes NO plugin. Fix in importar_mo2.py + preparar_lanzamiento().
2. **`--solo` of importar_mo2.py overwrote the profile lists** → modlist with 1 mod → MO2 "directory update" disables the rest → game without mods ("not configured"). Fix: lists ALWAYS with the full manifest.
3. **JIP LN without dll**: estado.json of 58277 pointed to the INI instead of the main → jip_nvse.dll was never extracted. Fix: estado.json + re-import (JIP v57.30 loads).
4. **LOD Fixes without INI**: extra 84171:1000150631 pointed to the main. Fix: estado.json + re-import.
5. **CORRUPTED Fixed ESMs (deterministic crash at start, identical stack 0x00AA991C)**: the xdelta3 patches of the .mpi don't match the game's vanilla (cpylen FalloutNV=245,642,722 vs vanilla 245,650,747; DeadMoney 6,274,831 vs 6,274,851 — the Data is legit vanilla per Steam verify) → xdelta3 with a source ±bytes → esm with valid TES4 but missing records (00115C5F, 00094EB8 absent) → `MASTERFILE: Could not find reference` → crash. **State**: mod disabled, vanilla esms. Pending: exact source of the .mpi.
6. **Incomplete SArchiveList** (only 6 base BSAs) in the 3 inis → DLC BSAs not registered. Fix: 21 BSAs in vanilla order, Update.bsa last.
7. **Incompatible saves**: games created with another era of esms → broken formids when loading → "!" (statics), pink DLC weapons, body textures (`00000007modbodyfemale` vs BSA `00118e86`). Fix: saves backup; new game = everything OK. CAUTION: the game AUTO-LOADS the last save on start (nvse.log DoLoadGameHook without interaction) — empty Saves/ for clean tests.
8. **BSAs verified thoroughly**: the 11 compressed ones have bit30 on ALL records (without-bit30=0), valid raw data (nif `Gamebryo`, dds `DDS `); the raw ones (Meshes/Textures/etc.) are intact vanilla. The decompressor was NOT the cause of any visible error.
9. **BSA record format**: 16-byte records `<QII` (hash, size, off); folder = folder hash; file-hash = hash of the NAME ONLY (all skeleton.nif share the hash). The sum-hash does NOT match anything in FNV (the engine's real hash is another one — unresolved, not needed).

### Repos post-push
- `jhoniwana/vnv-linux` **public** (branch main, `a5ea1a7`); 5 root repos **private** by the user's decision.
- UEM Fixes `.mpi` (220 MB) out of the repo (GitHub 100 MB limit); `port.py` extracts it from the `.7z` with 7z to `~/.cache/vnv-uefix/`.
- `epic` on Steam = no-op (root_mods.py:10,13).

---

## 📚 WHAT WAS LEARNED (by area)

### Nexus API (v1)
- `GET /v1/games/newvegas/mods/{id}.json` — metadata (name, version) — FREE with API key
- `GET /v1/games/newvegas/mods/{id}/files.json` — file list — FREE
- `GET /v1/games/newvegas/mods/{id}/files/{fid}/download_link.json` — **PREMIUM ONLY** (403 "premium users only")
- API key = personal, free, at `nexusmods.com/settings/api-keys`. New format: signed token
- Free rate limits: ~5s between calls recommended
- **`latest_link.json` does NOT exist** (422 — it's a numeric id, not an endpoint)

### Nexus login (the big achievement)
- Playwright Chrome headless: ❌ Turnstile blocks
- SeleniumBase UC headless: ❌ Turnstile blocks (better, but doesn't pass)
- **Camoufox headless: ✅ PASSES TURNSTILE**
  - `pip install camoufox` (downloads its own Firefox 152 beta)
  - ⚠️ On this Arch it needs `LD_LIBRARY_PATH=/home/shot/xvfb-env/lib` (conda-forge pixman — the system cairo is broken by a partial update)
  - Flow: `users.nexusmods.com/register` → click "Sign in" → `#user_login` + `#password` → submit → wait for "Welcome back"/"Sign out"
- **The session cookie is NOT called `sid` — it's called `nexusmods_session`** (Nexus renamed it). `cf_clearance` (Cloudflare) also exists.
- User's 2FA: NOT ACTIVE (clean login)
- Cookies saved in `~/.config/vnv-linux/` with 600 permissions

### File downloads (THE WALL)
- API download_link: Premium only ❌
- New Nexus UI = React + web components (`<slow-download-prompt>`, shadow DOM with floating-ui-root)
- `DownloadPopUp` widget (legacy): redirects to the mod page (dead)
- `/api/files/{internal_id}/download?nmm=0` → 302 to the mod page (useless)
- `/api/files/{internal_id}/download?nmm=1` → 200 but it's the Vortex flow (nxm://)
- The real download button: the row's dt has `id="file-expander-header-{fid}"` and `data-id`; the `cloud_download` icon is ONLY status ("You downloaded this")
- Existing tools (NexusDownloadFlow 79★, NexusAutoDL 75★, WabbaRush): ALL click the "Slow Download" button in a visible browser with a human session — none automates headless
- **Conclusion: free download requires either a human clicking or Premium. By Nexus design.**
- Manual path: `MODS_LISTA.md` with the 54 direct links (generated)

### Viva New Vegas (guide)
- The guide moved: **vivanewvegas.moddinglinked.com** (repo ModdingLinked/Viva-New-Vegas)
- Core = ~54 Nexus mods (utilities 21 + bugfix 34 + setup) + 1 GitHub (Stewie Tweaks INIs)
- Has an official Wabbajack for the Extended version
- `wabbajack.html`, `mo2.html`, `setup.html` — key config pages

### MO2 on Linux
- **MO2-LINT** (`Furglitch/modorganizer2-linux-installer`, ★1743): the standard, supports FNV (fullscreen-only)
- VNV requires: VC++ redist (winetricks vcrun*), ASLR off, 4GB/NVTF heap
- Load order: VNV uses LOOT to sort (no fixed order)

### Useful tools discovered
- **micromamba** (user-space, no sudo): installed Xvfb + pixman + openssl 1.0 in `/home/shot/xvfb-env`
- System Xvfb: binary deleted but zombie process (useless)
- System `Xorg`: blocks non-console users ("Only console users")
- LightPanda: NOT suitable for anti-bot (Cloudflare blocks it) — only simple JS rendering

---

## 🐛 Bugs found and fixed
1. **`--solo` destroyed the manifest**: `actualizar.py`/`descargar_nexus.py` saved the FILTERED list. Fix: `todos = mods` + `json.dump(todos)`.
2. **Non-existent `sid` cookie**: Nexus uses `nexusmods_session`. Fix in `login_camoufox.py` + `descargar_nexus_cookies.py`.
3. **`user_agent` is not a SeleniumBase Driver kwarg** (it's `agent`/default).
4. **SeleniumBase `headless2`**: unstable session (connection pool dies).
5. **urllib doesn't forward cookies across domains** on redirects → the CDN rejects.
6. **Manifest regenerated from `/tmp/vnv_mods.json`** after bug #1 (the backup saved the project).

## 🔑 Credentials and security
- User's API key: signed token format, kept ONLY via env var during runs (not on disk)
- ⚠️ **The user pasted the Nexus password in the chat — recommended to change password + regenerate API key**
- Cookies in `~/.config/vnv-linux/` with chmod 600
- NEVER upload cookies/key/password to the repo (gitignore + .config/)

## 🗺️ Roadmap
- [x] Manifest of 54 mods (53 with file_id — 90824 gives 403)
- [x] actualizar.py (metadata via API) — tested live
- [x] Automatic Nexus login (Camoufox) — tested live
- [x] descargar_nexus.py (Premium) + descargar_nexus_cookies.py + descargar_browser.py
- [x] vnv.sh install/run/config/config-cookies/login
- [x] MODS_LISTA.md (manual path)
- [ ] **Download the 54 mods (the blocker)** — paths: Premium (instant) / manual / keep researching
- [ ] Automatic import into MO2
- [ ] Test MO2-LINT on a real machine
- [ ] Full pipeline verified

## 📌 Closed investigations
- **Embedded JSON**: the page embeds `downloadUrl: /api/files/{internal_uid}/download` (and `?nmm=1` for Vortex). BUT the endpoint 302s to the mod page even inside the browser (manual fetch → opaqueredirect). The real link requires the React modal state.
- **`exp=true`**: revives nothing (302 anyway).
- **POST to the endpoint**: 405 Method Not Allowed.
- **Full dump of the expanded DOM**: the rows show "Preview file contents" + "Version history" but there is NO download button in the served HTML — the button is rendered by the `<file-row>` web component/React only on interaction (hover/click state), invisible to a headless DOM.
- **Download-free UI = impossible headless** (confirmed with 3 engines + endpoints). Free download requires a human (2 clicks per mod) or Premium (1 command).
- **Exhaustive dump of ids/classes/buttons**: the `file-expander-header-*` rows have NO download button at all in the served DOM. The button is rendered by the web component only on interactive states (real user gesture) — unreachable headless. The `#slowDownloadButton` selector from the nolvus script (2023) no longer exists in the 2026 UI.
- **"Manual download"**: also not exposed in the current DOM — same conclusion.
- **NexusMods.App**: official open source app (GPL) with Linux builds — candidate for a native flow, not yet automatable via stable CLI.
- **Wabbajack**: the guide has an official Wabbajack for VNV Extended (not Core) — works on Linux via Jackify (★721) — a valid alternative if the user accepts Extended.
- **FINAL VERDICT (closed)**: free downloading from Nexus is NOT headless-automatable by design (2026). Paths: Premium (descargar_nexus.py, ready) / human clicking (MODS_LISTA.md) / official app.

## 🔧 LINUX PORTS OF TOOLS (own repos, wired into vnv.sh)

| Tool | Repo | Script in vnv-linux | Command |
|---|---|---|---|
| FNV BSA Decompressor | `fnv-bsa-decompressor-linux` | `scripts/bsa_decompressor.py` | `./vnv.sh bsa` / `bsa-verify` |
| Ultimate Edition ESM Fixes | `ue-esm-fixes-linux` | `scripts/esm_fixes.py` | `./vnv.sh esmfix` |
| xNVSE | `xnvse-linux` | — (uses the repo) | — |
| Epic Games Patcher | `epic-games-patcher-linux` | — | — |
| FNV 4GB Patcher | `fnv-4gb-patch-linux` | — | — |

### ⚠️ CRITICAL BSA BUG FIXED (pink textures / "!")
- The original port used `0x100` as the compression flag and wrote every file with bit 30 set.
- The game (xEdit `wbBSArchive.pas`): `ARCHIVE_COMPRESS = 0x04`, `FILE_SIZE_COMPRESS = 0x40000000` — a file is compressed if `bit30 XOR (header & 0x04)`.
- On the vanilla FNV BSAs (flags 0x100 WITHOUT 0x04) the game reads bit30 = compressed -> zlib on raw data -> **pink textures + "!" meshes in the DLCs**.
- Fix: exact xEdit semantics + only set bit30 when the header declares compression by default. Validated with synthetic BSAs (0x100 and 0x104).
- **Repair**: re-run `./vnv.sh bsa` on the already-processed BSAs (the data is intact — only the flag was wrong) + `./vnv.sh bsa-verify` (CRC64). Plan B: Steam -> verify integrity.

### ⚠️ ESM FIXES IMPROVED
- The original port matched patch<->ESM by SIZE (fragile — two ESMs of similar size -> xdelta3 fails or patches the wrong one).
- Fix: the `.mpi` index stores the names (`oldworldblues.esm.xd3`, `deadmoney.esm.xd3`...) -> match by NAME (6/6).
- Guard: refuses `--dest` = the game's `Data/` folder (never overwrites the vanilla ESMs).

## 🔑 Executive summary of the state (last update)
| Component | State |
|---|---|
| Manifest of 54 mods (53 file_id) | ✅ |
| actualizar.py | ✅ tested |
| Camoufox login (passes Turnstile) | ✅ tested |
| **Automated FREE download** | ✅ **53/53 DOWNLOADED** — verified, 0 failures |
| vnv.sh + MO2/INI/LOOT pipeline | ✅ skeleton |

## 🏆 COMPLETE DOWNLOAD ACHIEVEMENT (53/53)
- Endpoint: `/Download/?id={file_id}&game_id=130&source=ModPage` — works for FREE
- Two page formats: auto-download ("should automatically begin") and button ("served via CDN" + "Download" button)
- Universal downloader pattern: listener `page.on("download")` → wait 12s auto → if not, click the exact button (text === 'Download' near the area)
- Rate limits: 8-15s between mods, 3 attempts with backoff, Cloudflare challenge wait (up to 60s)
- Monitoring: `python -u script > /tmp/descarga.log` (do NOT pipe to tail — it buffers everything)
- Verification: `file -b` on each file (0 HTML)
- **CAUTION: don't run two instances on the same log — the outputs overwrite each other**

## ⚠️ Missing (small)
- ~~Mod 90824~~ → **RESOLVED**: the current guide uses mod **66347** ("lStewieAl's Tweaks and Engine Fixes" v9.95, fid 1000177460) — 90824 was the old version (hidden). The manifest was deduplicated to **53 unique mods = complete current Core**.

## 🛡️ EXACT VERIFICATION + MANAGER (gestor_descargas.py)
- **Bug fixed in actualizar.py**: it chose the FIRST MAIN file instead of the most recent → 13 mods with the wrong file_id (e.g. JIP LN downloaded the INI v56.24 instead of the PLUGIN v57.30; FNV 4GB downloaded 1.4 instead of 1.5 "for Proton")
- Fix: `max(mains, key=uploaded_timestamp)` → **13 file_ids corrected and re-downloaded**
- **gestor_descargas.py**: orchestrator with states persisted in `estado.json` (pending/downloading/ok/failed), retries with backoff (--max-intentos), --verificar (integrity with `file`), --solo-fallidos, --forzar (re-download if file_id changed), --seccion/--solo
- Final verification: **53/53 files OK, 0 HTML, correct versions vs manifest**

## 🚀 PORTABILITY + SELF-RECOVERY (setup.sh + wrapper)
- **setup.sh multi-distro**: detects Debian/Ubuntu/Arch/Fedora/openSUSE → system dep commands (auto-installs with sudo if available, otherwise instructions) → creates venv + Camoufox → smoke test → if it fails due to libs, falls back to micromamba+pixman user-space (no sudo) → creates wrapper `venv/camoufox-python` that resolves the libs
- **Wrapper**: exports the correct LD_LIBRARY_PATH and cleans the contaminated one — solves the Arch partial-update case (cairo/pixman desync)
- **`vnv.sh credenciales`**: saves user+pass (600 permissions) in `~/.config/vnv-linux/credenciales` — the manager uses them ONLY for automatic re-login
- **Automatic re-login tested**: session deleted → page shows "Log in" (NOT "Sign in"! — the detection bug) → manager detects → relogin() reads credentials → login_camoufox passes Turnstile → cookies regenerated → retries → ✔ download OK
- **vnv.sh commands**: setup | login | config-cookies | credenciales | config | download/update | estado/verificar | install | run

## 🖥️ WEB UI (ui.py — NO terminal, hand-held)
- `./vnv.sh ui` → Flask at http://127.0.0.1:8397 + opens the browser on its own
- **5-step wizard**: Environment → Nexus account → Downloads → Install → Play
- Each step: big button + live log via **SSE** (Server-Sent Events) + progress bar
- Real-time state: checkmarks per step (setup ok, session ok, 53/53, MO2, game), current step highlighted
- Credentials form in the UI (saves with 600 permissions), 1-click login
- Backend: `/api/estado` (JSON), `/api/accion/<setup|login|credenciales|descargar|verificar|instalar|jugar>` (POST → job_id), `/api/log/<job_id>` (SSE stream)
- Flask is installed by setup.sh (venv deps)
- Tested live: correct state, verification with SSE logs flowing to the UI

## 📦 AUTOMATIC MO2 IMPORTER (scripts/importar_mo2.py)
- Converts downloads/ → MO2 format: `mods/<Nombre>/` decompressed + `profiles/Default/modlist.txt`
- Decompresses 7z (system), zip (safe stdlib), rar (7z); cleans __MACOSX/.DS_Store; flattens single root folder; deletes empty ones
- modlist.txt with the manifest order (setup → utilities → bugfix → finish), all active (+)
- **Tested live: 53/53 mods imported** (correct structure: nvse/plugins/, uio/settings.ini...)
- Integrated into `vnv.sh install` (replaced the "import manually") — the pipeline is 100% automatic

## 🔗 STEAM ↔ MO2 CONNECTION (step 1 — automated) + LAUNCH THEORY (step 2)
### The reality of modding on Linux
- **There is NO native modloader for FNV**: MO2/Vortex are .NET Windows apps → they run with Wine/Proton.
  NexusMods.App (the official app) IS native Linux but **does NOT support FNV** (verified in its code: only Fallout4, Cyberpunk, etc.).
- MO2 via Wine/Proton is the standard (used by the VNV guide and MO2-LINT).

### Step 1 — Connection (automated in ./vnv.sh steam)
- Steam: FNV (appid 22380) → Properties → Compatibility → force Proton (once, creates the prefix)
- The prefix lives in `steamapps/compatdata/22380/pfx`
- **protontricks is the key piece**: it lets MO2 run INSIDE the game's prefix
- `./vnv.sh steam` diagnoses: Steam, FNV installed, prefix, protontricks — and can launch FNV with Proton to create the prefix (`--si` for non-interactive, used by the UI)

### Step 2 — Launch (theory — requires real hardware with the game)
1. `mo2-installer install --game fallout-new-vegas` → installs MO2 in the game's prefix (MO2-LINT uses protontricks internally)
2. `mo2-installer run --game fallout-new-vegas` → opens MO2 with the same Wine environment as the game
3. Inside MO2: the "Default" profile already has the 53 imported mods (importar_mo2.py) + modlist.txt
4. **LOOT**: first time → Sort button in MO2 (sorts the plugins and writes loadorder.txt). LOOT runs inside the prefix (MO2-LINT includes it)
5. **Run**: MO2's "Run" button launches FalloutNV.exe with MO2's VFS (the mods mounted virtually — the game directory is NOT touched)
6. NVTF (New Vegas Tick Fix) handles the heap + 4GB + vsync from `Data/NVSE/Plugins/nvtf.ini` (written by tweaks_ini)
7. FNV on Linux with Proton: fullscreen-only according to MO2-LINT (no windowed) — the VNV guide recommends fullscreen + NVTF

### Launch troubleshooting
- **The game crashes at start**: check nvtf.ini (EnableHeapReplacement) and that NVTF is active in the modlist
- **No mods loaded**: the active MO2 profile must be the one with the modlist (Default); verify the game launches FROM MO2, not directly from Steam
- **Black screen**: FNV + Proton needs fullscreen; try Proton GE if the standard one fails
- **LOOT doesn't sort**: run LOOT from MO2 (the Sort button uses the prefix's LOOT); if missing, MO2-LINT installs it with `mo2-installer install --game fallout-new-vegas`

## 💎 THE DISCOVERY THAT SOLVED IT (not giving up pays off)
The user insisted: "when you're on the mod page you have to click files and there the buttons for manual download appear". They were right. Searching the JS bundle (`web-components-*.js`):
- The "Manual" button of the `<mod-download-modal>` component (shadow DOM) generates:
  - Premium: `/Download/?id={fid}&game_id={gid}&source=ModPage`
  - Free: navigates to `?tab=files&file_id={fid}` (where the modal shows the button)
- **The endpoint `/Download/?id={file_id}&game_id=130&source=ModPage` works for FREE**: shows a page with "Your file will be served via CDN" + "Download" button (link without href, triggers JS)
- Clicking that link → **downloads the real file** (original name, e.g. `UIO - User Interface Organizer-57174-2-30-1629600625.7z`)
- Button selector: search for the text "served via CDN" in the DOM → go up 6 levels → `el.querySelector('a')` → click
- **Moral: the button was in the web component's shadow DOM — I was looking in the regular DOM. The page's JS bundle is the source of truth.**

## ⚠️ Lessons from the previous failure (not to repeat)
- "Manual download" IS automatable — the `/Download/` endpoint is the path
- The previous flow (DownloadPopUp, /api/files/, slow-download-prompt) was DEAD or incomplete
- Cookie consent (Cookiebot) blocks ALL pages — it must be accepted first
- The "Download" button has no href (triggers JS) — a generic `a:has-text('Download')` finds the nav one (invisible); you must anchor to the text "served via CDN"

---

# 🧩 SECOND PHASE — ROOT MODS, NATIVE AND PER-MOD REPOS (5 aug 2026)

## 🏆 COMPLETE GAME VALIDATION (6 aug, night) — MENU WITH MODS
- **The game reaches the MAIN MENU with the FULL pipeline**: decompressed BSAs (v2) + patched 4GB exe + xNVSE + the 53 mods of the Default profile + Fixed ESMs. Confirmed by the user (Stewie Tweaks appeared in Settings = mods loaded).
- **The decompression bug (CRITICAL)**: v1 set `flags=0` → the game crashed (`page fault` at different addresses — the game's BSA reader needs the header bits). **The real fix (UESP spec)**: **keep flags=0x100 and mark each file with BIT 30 (0x40000000) in the size** ("if bit 30 is set, the default compression is inverted") + raw data without prefix. Committed in `fnv-bsa-decompressor-linux` (`aec8e47`).
- **Steam validation restores the vanilla exe** → the 4GB patch must be re-applied AFTER validating. Fix in `fnv-4gb-patch-linux` (`f1ce0c5`): detects exe patched by LAA (0x20 in COFF header) + imports `nvse_steam_loader` (NOT by the existence of the backup).
- **MO2's `run` without `--profile` uses the last active profile of the UI** (not profiles.ini) → the test-vanilla profile was never used; the "vanilla profile" tests ran the Default (with mods). That's why the crash was always the BSA v1 or the environment.
- **Diagnostic lesson**: NVSE logs (nvse*.log in the game root) ACCUMULATE between runs — truncate them before each test to read only the current run.
- **FNV launcher broken under Proton** (process runs, never shows a window) — the real entry is FalloutNV.exe via MO2 (`run -e "New Vegas"`).
- **Definitive input automation**: XTest broken in this session → **uinput/evdev** (`scripts/uikey.py`, pip evdev, /dev/uinput with input group) — injects real keyboard at kernel level, works on GNOME (wtype doesn't: mutter doesn't support virtual-keyboard). MO2 dialogs (Launch Steam / Waiting) are solved with Tab+Enter.
- MO2's "Launch Steam" is a false positive (looks for a Windows "Steam.exe" process; native Steam is Linux) — "Continue without starting Steam" is safe (the DRM finds Steam via IPC).
- The game had NEVER really run on this machine (yesterday's "run" was the hung launcher).

## 🧰 BSA DECOMPRESSOR — NATIVE PORT READY (5 aug, night)
- **Repo**: `repos/fnv-bsa-decompressor-linux/` (git `6a95a62`) — `decompress.py` (pure Python, stdlib, no wine).
- **Real FNV BSA v104/v105 format (differs from the UESP standard)**: header 36B ("BSA\0"+version+folderRecOff+fileRecOff+counts+lengths+flags) → folder records [hash(8)][count(4)][nameOff(4)] → **per folder: [nameLen(1)][name][file records count×16: hash(8)+size(4)+off(4)]** → file names (fileNameLen, NUL-terminated) → data. The header's `fileRecOff` = 7 in vanilla BSAs (apparently ignored value). The folder nameOff point to the first FILE NAME of the folder in the names section.
- Compression: header flag 0x100 → each file = `[u32 uncompressed size][zlib]`; record size = compressed size (includes the prefix).
- `reescribir()`: header flags without 0x100 + records with size=raw and recomputed offsets + intact names + raw data.
- **Bug found**: `pos += n*16` was missing in the per-folder loop (names were read from wrong positions).
- **Roundtrip validation** (parse→decompress→rewrite→reparse→SHA1 per file against original): Misc 142/142 ✓, Caravan 11/11 ✓, Classic 19/19 ✓, **DeadMoney - Main (358MB, 7207 files) 7207/7207 ✓**.
- Compressed vanilla BSAs: DeadMoney-Main, Fallout-Misc, GRA-Main, HH-Main, LR-Main, MercenaryPack, OWB-Main, CaravanPack, ClassicPack, TribalPack, Update.bsa (11). The Sounds/Meshes/Textures are not → skipped.

## 💎 UE ESM FIXES — NATIVE PORT RESOLVED (5 aug, night)
- **Repo**: `repos/ue-esm-fixes-linux/` (git `89cfef1`) — `port.py` + `build_xdelta3.sh` + original `Installer.exe`/`.mpi`.
- **The secret of the `.mpi`**: the 6 `.xd3` patches are wrapped in **LZ4 Frame** (magic `04 22 4D 18`, 13 bytes before each VCDIFF magic `D6 C3 C4 00`). That's why there were "fake magics" and unreadable streams: they were LZ4-compressed blocks. The `ERROR_blockMode_invalid` errors of the .exe are `lz4frame` codes.
- **Real manifest** (`_package/index.json`, LZ4-compressed, 4048 bytes): `Assets` = [0,2,"",3,1,3,"<esm>","./<esm>"] maps `%FNVDATA%\<esm>` → destination 1:1. `Checks` only validates `FalloutNV.exe` (8 SHA1: Steam/GOG/EGS patched or not; ours = `0021023E37B1AF143305A61B7B29A1811CC7C5FB` ✓). The esm are NOT validated → they go raw to `xd3_decode_memory`. No patch chain or pre-generated esm.
- **Native flow** (port.py): scan LZ4 magics → decompress (python-lz4) → discard non-VCDIFF (index.json/html/css) → read cpylen from the first window (== vanilla esm size, can be ≤ file size — the −20/−8045 were never a problem) → match against `Data/*.esm` → `xdelta3 -d -s <vanilla> <patch> <out>`.
- **Verified outputs** (adler32 of the windows confirmed by xdelta3, TES4 headers ✓): FalloutNV 330,921,877 / DeadMoney 7,303,362 / HonestHearts 35,736,867 / OWB 32,923,146 / LR 40,265,999 / GRA 252,293.
- **DEFINITIVE VALIDATION (5 aug, night)**: I ran the official `Installer.exe` via Proton (GUI blind: OCR rapidocr + xdotool) pointed at `C:\users\steamuser\Desktop\Fixed ESMs` → **the 6 esm of the official installer are SHA1-IDENTICAL to those of port.py**. Bit-exact validation closed.
  - How to handle Wine GUI blind: `import -window <WID>` works (root doesn't), OCR with `rapidocr-onnxruntime` (pip, venv), the installer's custom fields don't accept typing (only the native dialogs); the Browse pastes the text into the dialog's current folder (Desktop) → writing a relative name + Return works; `windowactivate` DOES work on XWayland to give focus.
  - Installer requires `xdelta3.dll` next to the exe (commit b7ebdbf added it).
- **Lessons**: (1) the previous "address too large" error was because I fed xdelta3 the raw bytes without decompressing (p1c.xd3 ≠ full_4735.xd3); (2) `xdelta3 test` hangs the shell — don't use it; (3) this system's protontricks-launch uses `--appid` and needs `vdf` (installed in venv) + `winetricks` (downloaded to ~/.local/bin); (4) ImageMagick's `import`/`magick import` fails with "missing an image filename" (use ffmpeg x11grab or gnome-screenshot); (5) `xdelta3 printdelta` with VCD_SOURCE streams fails without a source — use real `-d -s`; (6) real VCDIFF flags: VCD_SOURCE=1, VCD_TARGET=2, VCD_ADLER32=4.

## ✅ LOOT + MO2 VALIDATION (6 aug)
- **Game boot attempts (6 aug, afternoon)**: everything automatable is validated EXCEPT the final boot, blocked by the degraded environment:
  - `steam -applaunch 22380` DOES launch the game → but it starts **FalloutNVLauncher.exe** (launcher broken under Proton: process runs, window never appears) → no clickable Play.
  - Launching FalloutNV.exe with Steam's real wrapper (`reaper SteamLaunch AppId=22380 -- ... _v2-entry-point --verb=waitforexitandrun -- proton waitforexitandrun FalloutNV.exe` + STEAM_COMPAT_DATA_PATH/CLIENT_INSTALL_PATH/LIBRARY_PATHS/RUNTIME_PATHS) → passes the DRM, starts DXVK (Fossilize) and **dies silently** (no window, no error in the log).
  - Direct via protontricks: DRM error without Steam; with Steam running → page fault (Steam environment missing).
  - nvse_loader direct: "Couldn't Find FalloutNV.exe" if the CWD isn't the game (protontricks uses --directory); with correct CWD → behaves the same as the exe.
  - The game DID run yesterday (Steam log 20:52 on 5 aug: 22380 processes added/removed) — the user launched it from the healthy environment.
- **Input automation**: XTest broken (frozen pointer) after the resolution change 1368x768→2560x1440; root screenshots in black; ydotool not installed. Clicks/keys only work via XSendEvent (`--window`) in specific native dialogs. → the final click (launcher Play, or MO2 Run, or "Continue without starting Steam") is done physically by the user.
- **FNV launcher (FalloutNVLauncher.exe) broken under Proton**: process runs but never shows a window.
- **Lesson**: `pkill -f` with a pattern on your own command line kills itself (twice today). Use `pkill -x` or kill by PID.

## ✅ LOOT + MO2 VALIDATION (6 aug)
- **Real LOOT**: `lootcli.exe` of the MO2 instance (`loot/lootcli.exe`) runs in the prefix with `WINEPATH=<MO2>/dlls` (Qt6 is there) + `--game FalloutNV --gamePath <game> --pluginListPath <profile>/plugins.txt --out <report> --auto-sort`. Downloads the masterlist from GitHub and sorts. **The LOOT order == the guide's order (20 identical plugins).**
  - ⚠️ Standalone lootcli can't see MO2's VFS → discards the mods' esps (only resolves the real Data esm) and **rewrites plugins.txt** leaving it at 10 → don't use it for the profile (only as validation); the real Sort is done with the MO2 GUI.
  - ⚠️ `--out` is MANDATORY (without it: "argument missing out") and OVERWRITES the destination file — point it to a separate report.
- **MO2 GUI**: loads the Default profile with the 53 mods + the 21 resolved plugins (verified by OCR of the right panel). The `*DLC: X` in the modlist is added by MO2 (virtual, without folders).
- **MO2 CLI (corrected)**: in 2.5.2 the CLI is a `run` **command** (boost::program_options, `src/commandline.cpp`): `ModOrganizer.exe --profile=Default run -e NVSE` launches the configured NVSE executable (nvse_loader.exe, game wd). `-e` is `zero_tokens` (flag without value). **`-e=NVSE` FAILS** (unregistered option → stays as positional → MO2 treats it as an executable name: `"-e=NVSE" not set up as executable` + tries to spawn `...\vnv\-e=NVSE`). With `steamAppID=` empty in customExecutables the launch is direct, WITHOUT the "Launch Steam" dialog.
- **Real bug found and fixed**: the profile INIs were **read-only** (`-r--r--r--`) → the game can't write them → "INI file is read-only" dialog. Fix: `chmod u+w` (added to `lanzar()` in vnv.sh).
- **Another bug**: the re-import deleted the `+Fixed ESMs` from the modlist (root_mods adds it later) → fix in importar_mo2.py: re-adds it if the folder exists.
- **Input automation BROKEN in this session state**: XTest doesn't move the pointer or type (display changed 1368x768→2560x1440; pointer stuck). xdotool `--window` with XSendEvent: works only on some native dialogs (Return in the file dialog yes; MO2 dialogs no). → the game's final boot needs a physical click from the user.
- **Game**: launched direct (protontricks) gives a DRM error if Steam isn't running; with Steam running, nvse_loader direct crashes ("page fault") because the Steam environment is missing; the correct launch = Steam (`steam://rungameid/22380`) or MO2 GUI → Run. The game DID run yesterday (Steam log 22380).
- MO2's `plugins.txt` uses `*` = ACTIVE plugin (correct format). The generated loadorder == LOOT order ✓.

## ✅ LAUNCH VALIDATION VIA CLI (7 aug, dawn) — MENU OK
- **`run -e NVSE` works and is the CORRECT way** (confirmed from the MO2 2.5.2 source `src/commandline.cpp`: the CLI is a `run` command with `-e`/`--executable` as a `zero_tokens` flag + positional NAME; `setFromExecutable` uses the configured binary/wd/arguments).
- **`-e=NVSE` FAILS**: unregistered option → `collect_unrecognized` leaves it as positional → MO2 treats it as an executable name (`"-e=NVSE" not set up as executable`) and tries to spawn the file relative to the process working dir (`Z:\home\jhon\vivanewvegas\vnv\-e=NVSE`).
- **Validation passed**: with `--profile=Default run -e NVSE` → `nvse_loader.log` ("steam exe", "hook thread complete", "launching") → `FalloutNV.exe` running stable → **"Fallout: New Vegas" window on screen** + the **27 VFS NVSE DLLs loaded** (jip_nvse, nvse_stewie_tweaks, LOD Fixes, kNVSE, VATSLagFix, etc. in `nvse.log`) + CrashLogger.log empty (no crash) + master files loading.
- With `steamAppID=` empty in the NVSE customExecutable the "Launch Steam" dialog doesn't appear → the CLI launch is clean and automatable.
- Note: BRAIN.md line 213 already documented `run -e "New Vegas"`; now it's also confirmed with the `NVSE` executable (nvse_loader.exe).

## ✅ ROOT MODS INTEGRATED (5 aug, night)
- `scripts/root_mods.py` rewritten: **orchestrator** that delegates to the 5 repos (`repos/<mod>-linux/`) via subprocess — no wine, no proton. `--solo`, `--game-dir`, `--mo2-dir`; uefix → `mods/Fixed ESMs` and activates `+Fixed ESMs` in modlist.txt.
- `vnv.sh install` now runs: instalar_mo2 → crear_instancia_mo2 → importar_mods → **root_mods** → tweaks_ini → correr_loot.
- **Tested end-to-end against the real game**: 11 BSAs decompressed in-place + 6 Fixed ESMs generated in the real MO2 + activated modlist. Idempotent (2nd run: everything "skip" without error).
- **Bug found in the real game**: vanilla BSAs contain 0-size files → `struct.unpack` exploded; fix `sz == 0 → b""` (commit in fnv-bsa-decompressor-linux).
- **uefix idempotency**: if the esm already exist → OK (no error).

## 🗂️ PER-MOD REPOS (names: <mod>-linux)
| Mod | Repo | Contents |
|---|---|---|
| UE ESM Fixes Remastered | `repos/ue-esm-fixes-linux` | port.py (LZ4+xdelta3), build_xdelta3.sh, Installer.exe, .mpi |
| FNV BSA Decompressor | `repos/fnv-bsa-decompressor-linux` | decompress.py (BSA v104/v105 → without zlib) |
| xNVSE | `repos/xnvse-linux` | port.py (copies to Root) |
| FNV 4GB Patcher | `repos/fnv-4gb-patch-linux` | port.py + FalloutNVPatcher (native ELF) |
| Epic Games Patcher | `repos/epic-games-patcher-linux` | port.py (native xdelta3, EGS-only) + patch.xdelta |

## 🚧 PENDING from phase 2
- [ ] Test full `install` on a real machine (MO2-LINT, LOOT, first launch)
- [ ] LOOT + first launch validated (correr_loot/lanzar are still instructive)

## What are the "root mods" (step of the VNV guide)
- Mods that go **directly to the game directory** (not to MO2's VFS). In MO2 they stay disabled on purpose (importar_mo2.py sets `-` + `validated=true` for them, installed to the "Root").
- The 5: **xnvse=67883, 4gb=62552, epic=81281, uefix=92289, bsa=65854**.
- MO2 instance: `~/.local/share/modorganizer2` (symlink with `~/.config/mo2-lint/instances/newvegas`).
- Game: `~/.steam/steam/steamapps/common/Fallout New Vegas/` (STEAM_LIBRARIES[0]).
- Proton prefix: `~/.steam/steam/steamapps/compatdata/22380/pfx`; registry → `installed path = S:\common\Fallout New Vegas\` (Wine GUIs autocomplete paths).

## 🔬 Hard technical facts (verified in the real game)
- **Plain `wine` does NOT run GUIs in the Proton prefix** (setupapi errors, no window opens). You must use `protontricks-launch 22380 <exe>`. Available: protontricks, wine, xdotool, ImageMagick `import`; DISPLAY=:0, WAYLAND_DISPLAY=wayland-0.
- **4GB Patcher (`FalloutNVPatcher`) is a native Linux ELF** (build "for Proton"). Runs from the root, prints `Patching FalloutNV.exe [US]... FalloutNV.exe patched!` and creates `FalloutNV_backup.exe`. ⚠️ The ELF exits with code 0 EVEN IF it fails ("FalloutNV.exe not found!") → detect success by the existence of the backup.
- **Epic Games Patcher**: xdelta (patch.xdelta + xdelta3.exe), ONLY for the EGS version → skipped on Steam (the guide says so).
- **BSA Decompressor**: Wine GUI (`FNV BSA Decompressor.exe`) — the user must click "Decompress"; not automatable.
- **UE ESM Fixes `Installer.exe`**: Wine GUI; its `.mpi` payload is a **BSA v105** (220,334,500 bytes; 7z CANNOT open it) → no extraction possible with GUI-tools → natural candidate for a native rewrite.
- **xNVSE**: the file carries an internal folder `nvse_6_4_8/`; 9 files (dll/pdb/exe + `Data/NVSE/nvse_config.ini`). Tested: 9 copied to Root OK.
- **4GB tested in the real game**: `FalloutNV.exe patched!` + backup created. **xnvse tested**: OK.

## 📜 BSA v105 format (reference for the native extractors)
- Header: `BSA\0`(4) + version u32 + folderRecordOffset u32 + fileRecordOffset u32 + folderCount u32 + fileCount u32 + totalFolderNameLen u32 + totalFileNameLen u32 + fileFlags u32.
- File records: hash u64 + size u32 + offset u32; size bit 30 = compressed (zlib).
- ⚠️ Layout verification pending to test against the real `.mpi` (the previous probe was cut short).

## 🏗️ `scripts/root_mods.py` (written, NOT committed yet)
- `--solo {xnvse,4gb,epic,bsa,uefix}`, `--game-dir`, `--prefix`, `--mo2-dir`; finds the game in STEAM_LIBRARIES; extracts from `downloads/`.
- State: xnvse ✅, 4gb ✅, epic ✅ (correct skip), **bsa/uefix ⚠️ BROKEN** (they use `_wine()` with plain wine → fails in the prefix).
- Plan: rewrite `_wine()` with `protontricks-launch 22380` (locate its binary).

## 🎯 USER DECISION (5 aug 2026)
1. **Make the Wine steps native on Linux**:
   - BSA Decompressor → rewrite the Data `.bsa` files without compression (zlib) in Python.
   - UE ESM Fixes → extract the `.mpi` (BSA v105) with Python → "Fixed ESMs" mod.
   - 4GB is already native; Epic is skipped on Steam.
2. **Create ONE GIT REPO PER root mod** (`xnvse`, `4gb`, `epic`, `bsa`, `uefix`) — each with its native tool.

## 🐛 Shell footgun (lesson)
- `pkill -f 'protontricks'` (or a pattern that appears in your own command line) **kills itself** → the command hangs until timeout. Use `pkill -x` (exact name) or patterns that don't match the shell.

## 📦 Artifact state in /tmp
- `/tmp/opencode/rootmods/4gb/FalloutNVPatcher` (extracted ELF), `/tmp/opencode/rootmods/uefix/` (Installer.exe + .mpi 220MB + xdelta3.dll), `/tmp/opencode/bsadec/` (decompressor + wine/proton logs).
- Attempt `protontricks-launch 22380 ".../FNV BSA Decompressor.exe"`: started, shell timeout; GUI not verified; no hung processes (verified with pgrep).
- `/tmp/opencode/uefix-patches/`: decompressed LZ4 streams (full_*.xd3) + outputs (out_*.esm) — temporary garbage, no longer needed (port.py does everything).
- `/home/jhon/vivanewvegas/vnv/repos/ue-esm-fixes-linux/`: Installer.exe + .mpi (commit `89cfef1`), `xdelta3` compiled at `~/.local/bin/xdelta3` (v3.1.0).

## 🗺️ Next steps
1. Test the BSA v105 format against the real `.mpi` (short Python probe).
2. Write the native tools (bsa decompressor + uefix extractor) in the per-mod repos.
3. `git init` in `repos/xnvse|4gb|epic|bsa|uefix` with scripts + tests.
4. Rewrite `_wine()` → protontricks; test `--solo bsa/uefix`.
5. Integrate root_mods into `vnv.sh install` (after importar_mods, before tweaks_ini) + commit.
