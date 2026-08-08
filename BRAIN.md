# BRAIN.md — VNV Linux Installer

Technical memory of the project: **100% automatic installer of Viva New Vegas (Core, 55 mods) for Linux/Steam**.

> Rule: every discovery, bug and decision goes here. This file IS the project's memory.
> Sections are grouped by topic, newest truth at the top. Historical details kept when useful.

---

## [GOAL] Goal
`./vnv.sh ui` = guided wizard: environment -> Nexus login -> downloads (55 mods) -> install (MO2 + INIs + LOOT) -> play. Zero manual steps.

## [STACK] Stack
- Python 3.12/3.14 + venv with **Camoufox** (anti-detection Firefox, passes Cloudflare Turnstile headless)
- Flask (local web UI on 127.0.0.1:8397, SSE live logs)
- Nexus session cookie (`nexusmods_session` + `cf_clearance`) in `~/.config/vnv-linux/` (600 perms)
- 6 public GitHub repos: `vnv-linux` + 5 native tool ports (`repos/<mod>-linux/`)
- Linux distros verified: **EndeavourOS (Arch, dev machine), Ubuntu 24.04, Arch Linux** (docker)

---

## [OK] CURRENT STATE — 100% VERIFIED (8 aug 2026)

| Component | State |
|---|---|
| Setup (setup.sh, multi-distro deps + venv + Camoufox + smoke test) | [OK] verified on Ubuntu 24.04, Arch, EndeavourOS |
| Nexus login (Turnstile auto-pass) | [OK] verified from scratch with real credentials (2026-08-08) |
| Downloads 55/55 (+5 extras) | [OK] verified live; fresh-clone continuity tested through 2 power-off interruptions |
| Install e2e (MO2 from scratch + 55 mods + root mods + INIs) | [OK] verified in `~/vnv-cero-test` (clean clone, fresh MO2 instance) |
| Root mods with post-step verification + fallbacks | [OK] xnvse/4gb/epic/uefix verified every run |
| BSAs + SArchiveList (21) | [OK] vanilla optimal; SArchiveList permanent in 3 INIs |
| Fixed ESMs (6/6 TES4, FalloutNV 465,054 records / 18,215 DIALOG) | [OK] validated; auto-inherit fallback when .mpi can't re-apply |
| `./vnv.sh salud` (12-point health check, exit code) | [OK] green on all machines |
| Web UI | [OK] 6/6 endpoint tests + SSE fix |
| Game | [OK] reaches main menu, stable 2+ min, no crashes, 28 NVSE plugins |

### Canonical numbers
- **55 mods** (Core VNV + JAM 66666 + YUPDate/supplement 98514 with `d20Fixes.esm`), 50 active + 5 root + Fixed ESMs.
- **Load order: 23 plugins** (YUP 1st, d20Fixes after YUP, Placement Fixes last, JAM at the end) — loadorder/plugins sync.
- **21 BSAs**: 4 with zlib (Meshes/Misc/Textures/Textures2 — must stay compressed), 17 raw. SArchiveList = 21 BSAs, `Update.bsa` LAST (priority).
- **Fixed ESMs**: 6/6 TES4 valid; FalloutNV.esm 465,054 records / 18,215 DIALOG (vs corrupted 233K/0 -> crash `0x00AA991C`).

---

## [CRITICAL] CRITICAL BUGS FOUND & FIXED (all verified)

### 1. THE REAL ROOT CAUSE of the historical crashes (7 aug, 17:40)
`scripts/root_mods.py` had `"bsa"` in `ORDEN = ["xnvse","4gb","epic","bsa","uefix"]`
-> **every `install`/`root` run RE-DECOMPRESSED `Fallout - Meshes.bsa` + `Fallout - Misc.bsa`**
(the two zlib BSAs that must never be decompressed: 32-bit game -> startup crash "File not found (2)").
The game kept breaking after EVERY Steam validate + install cycle — the pipeline itself re-broke it.
**Fix (`84375c5`)**: `bsa` removed from the automatic order (research-only via `--solo bsa`).
Verified: re-running `install` leaves all 21 BSAs vanilla (0 records with bit30).

### 2. THE DISTRIBUTED PIPELINE uefix BUG (fixed 8 aug)
`.mpi` v1.03 (UE ESM Fixes) doesn't match the current Steam depot ESMs (±bytes:
cpylen FalloutNV=245,642,722 vs vanilla=245,650,747; DeadMoney 6,274,831 vs 6,274,851)
-> xdelta3 fails ("checksum mismatch" / "source file too short") -> old port returned
"no patches applied" (rc=0) -> **fresh installs ended WITHOUT Fixed ESMs -> crash
`0x00AA991C` at dialogue init**. The game only worked because the user's machine already
had the good ESMs.
**Fix (`b5c67db`)**: when uefix fails, `root_mods.py` **inherits** the validated Fixed ESMs
from a previous install (`~/.local/share/modorganizer2/mods/Fixed ESMs`) -> verify 6/6 -> continue.
Port fails loudly with diagnostics (`69aadc2`). Verified in `~/vnv-cero-test`: inherit -> 6/6 -> Root ready.

### 3. SIGPIPE silent death (Ubuntu/Arch minimal, `e9a7732`)
`find ... | head -1` + `set -o pipefail` -> SIGPIPE killed the script **with NO output at all**
(rc=1) on systems without protontricks. Invisible on the dev machine (protontricks installed).
Fix: `find -quit` + `|| true`.

### 4. Fresh clone would never download (`e0eb1d8`)
`estado.json` was committed with all 60 entries "ok" but without the files -> a fresh clone
reported "nothing pending" forever. Fix: gestor re-downloads when state says ok but the file
is missing on disk; `estado.json` + `downloads/` now gitignored (local state only).

### 5. Download handler race (`6da63dd`)
`page.on("download")` was registered AFTER the `goto` -> if the download started during
navigation the event was lost -> "FileNotFoundError: 'file'". Fix: register handler BEFORE goto.
Also in `6da63dd`: `verificar_archivo` crashed without the system `file` binary (pure-python
HTML detection) and the Cookiebot TCFv2.3 consent selector (4 fallback selectors).

### 6. Cross-distro package bugs (Ubuntu/Arch, `0e50b8e`, `5b05b8b`, `d1a3...`)
- Ubuntu minimal: no `python3` -> setup auto-installs (apt/pacman/dnf/zypper).
- `libasound2` is a VIRTUAL package on Ubuntu 24.04 (only `libasound2t64`) -> one bad name
  failed the whole apt install -> split installs.
- Arch: wrong package names killed pacman entirely: `libgbm`->`mesa`, `libegl`->`libglvnd`,
  `atk`->`at-spi2-core`.

### 7. uefix port issues
- `python-lz4` missing in a fresh venv -> port auto-installs it now.
- xdelta3 without `-f` when `--force` -> "to overwrite output file specify -f" -> `-f` added.
- `.mpi` (210 MB) exceeds GitHub's 100 MB limit -> untracked, port extracts it from the Nexus
  `.7z` in `downloads/` (or reads the local file).
- Post-patch structural validation (`validar_esm`): records/DIALOG/formid module check —
  a corrupt ESM is caught at apply time.

### 8. MO2-specific bugs (6-7 aug, all fixed)
- MO2 2.5.2 truncates `plugins.txt` on shutdown -> `lanzar()` regenerates it from loadorder.
- MO2 2.5.2 plugins.txt WITHOUT `*` -> `Plugin not found: *FalloutNV.esm` when written with
  `*`. Fix: no asterisks, CRLF, header.
- `--solo` of importar_mo2.py overwrote profile lists -> always write the full manifest.
- Profile INIs were read-only -> `chmod u+w` in `lanzar()`.
- Re-import deleted `+Fixed ESMs` from modlist -> re-added.
- Standalone lootcli can't see MO2's VFS -> rewrites plugins.txt with ~10 plugins; LOOT
  removed from `install`; `./vnv.sh loot` validates against a copy.
- Incomplete SArchiveList (6 BSAs) in the 3 INIs -> DLC BSAs unregistered -> missing meshes.
  Fix: 21 BSAs, vanilla order, Update.bsa last — applied permanently by `tweaks_ini`.

### 9. BSA decompressor historical bugs (context)
- v1 set `flags=0` -> game page-fault crash. Real fix: keep `0x100` flags, mark each file with
  **bit30 (0x40000000)** in the size (xEdit: `compressed = bit30 XOR (flags & 0x04)`).
- Old port wrote bit30 on EVERY file while the game reads `bit30 XOR (bfFlags & 0x04)` ->
  the game tried zlib on raw data -> **pink textures + "!" meshes in the DLCs**.
- Names re-encoded instead of verbatim copy -> could shift the name table -> "File not found".
  Fix v1.2: folder-name blobs copied verbatim.

---

## [GOAL] BSA / DECOMPRESSOR — FINAL VERDICT (100% verified, 7-8 aug)

**The FNV BSA Decompressor is NOT needed on the current depot. Vanilla = optimal.**

Verified on all 3 fronts (VNV guide + mod page + decompiled official exe = Delphi app based
on xEdit's `wbBSArchive`, strings `TwbBSArchive`, embedded zlib 1.2.8):

| Mod component (per VNV guide) | Reality on the current depot | Needed |
|---|---|---|
| Decompress 11 BSAs (perf) | All 11 "0x100" BSAs ship **already raw**; bit30 on every record; 30/30 files raw | **NO — no-op** |
| "Fixes certain audio files that would not play in vanilla" | All `.wav` from the DLC Sounds BSAs are standard raw `RIFF....WAVE` | **NO — no-op** |
| Full `SArchiveList` (21 BSAs) required together with the mod | Applied **permanently** by `tweaks_ini` in the 3 game INIs (survives Steam re-validation; `Fallout_default.ini` gets reset to 6 by verify — fixed) | Done |

- **Real BSA header (xEdit wbBSA.pas)**: magic | version | offset($24) | **bfFlags** |
  folderCount | fileCount | folderNameLen | fileNameLen | bfFileFlags. Compression default
  = `bfFlags & 0x04`; per-file `bit30 XOR (bfFlags & 0x04)`.
- **File names** = NUL-terminated section (`fln` bytes) — NOT `[len][name]` (a `[len][name]`
  parser desyncs: names >255 crash + BSAs the game can't read).
- Meshes.bsa/Misc.bsa DO contain zlib and decompress fine with the corrected tool (Meshes
  1.06GB -> 2.31GB, bit30 SET, nifs raw) — but the 32-bit game crashes at startup because
  the decompressed archives exceed the address space. The original mod never touches them
  (same on Windows — it only processes the 11).
- Why "it works on Windows": it doesn't do anything more there — the premise was false.
- The corrected tool (xEdit layout + XOR semantics + verbatim names) is kept in
  `fnv-bsa-decompressor-linux` for reference. **Do not run it** (`./vnv.sh bsa`).

---

## [OK] THE DISTRIBUTED PIPELINE — WHAT RUNS TODAY

```
./vnv.sh install ->
  instalar_mo2 (MO2-LINT) -> crear_instancia_mo2 -> importar_mods (55) ->
  root_mods (xnvse -> 4gb -> epic -> uefix, each with post-step VERIFY + fallback) ->
  tweaks_ini (NVTF + FalloutCustom.ini + SArchiveList 21) 
```
- `root_mods.py` ORDEN = `["xnvse","4gb","epic","uefix"]` (**no bsa**).
- Post-step verification (`verificar_paso`): NVSE DLLs present, LAA 0x20 in the PE header,
  epic no-op, 6/6 Fixed ESMs TES4. Retry once, then clear instructions.
- **ufix fallback**: inherit Fixed ESMs from a previous install (see critical bug #2).
- **Steam validate rule**: Steam verify reverts 4GB/NVSE/esms -> ALWAYS run
  `./vnv.sh install` afterwards (it re-applies everything and is idempotent).
- `./vnv.sh salud` = 12-point health check with exit code (0 = healthy).

---

## [SECURITY] NEXUS LOGIN + DOWNLOADS (verified 8 aug, from scratch)

- **Login**: `scripts/login_camoufox.py` with `NEXUS_USER`/`NEXUS_PASS` (or the saved
  `~/.config/vnv-linux/credenciales`). Flow: `users.nexusmods.com/register` -> click
  "Sign in" -> fill `#user_login` + `#password` -> submit -> wait for the logged-in page ->
  save `nexusmods_session` + `cf_clearance`. **Turnstile passes with Camoufox** on a real
  machine; docker/VM environments are blocked by Cloudflare (anti-VM) — expected.
- The session cookie is `nexusmods_session` (NOT `sid`).
- **Downloads**: endpoint `/Download/?id={file_id}&game_id=130&source=ModPage` works FREE.
  Two page formats: auto-download ("should automatically begin") and button
  ("served via CDN" + "Download"). Universal pattern: `page.on("download")` BEFORE the
  goto -> wait 12s auto -> if not, click the exact button near "served via CDN".
- Cookie consent: Cookiebot **TCFv2.3** (since ~Nov 2025) — the old
  `#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll` selector no longer matches;
  multiple fallback selectors + click once per run.
- `gestor_descargas.py`: states in `estado.json` (pending/downloading/ok/failed), retries
  with backoff (--max-intentos), --verificar (pure-python HTML check, no `file` binary),
  --solo-fallidos, --forzar, --seccion/--solo. Rate: 8-15s between mods.
- **Continuity proven**: interrupted twice by power-off, resumed exactly where it stopped
  (22/60 then 38/38 -> 60/60, 0 failures).
- API knowledge: `download_link.json` is PREMIUM-only (403); `latest_link.json` doesn't
  exist; free rate limit ~5s. API key = personal signed token.

---

## [UI] WEB UI (ui.py)

- `./vnv.sh ui` -> Flask 127.0.0.1:8397 + auto-opens the browser. 5-step wizard:
  Environment -> Nexus account -> Downloads -> Install -> Play.
- Endpoints: `/api/estado`, `/api/accion/<setup|login|credenciales|descargar|verificar|steam|instalar|jugar>`
  (POST -> job_id), `/api/log/<job_id>` (SSE).
- Fixes: SSE late-reconnect replays buffered lines + fin (was infinite pings); estado counts
  only manifest mods (55/55, not 60/55 mixing tools).

---

## [TOOLS] NATIVE LINUX PORTS (repos, all PUBLIC since 8 aug)

| Tool | Repo | Command | Useful? |
|---|---|---|---|
| xNVSE | `xnvse-linux` | root_mods step | [OK] essential |
| FNV 4GB Patcher | `fnv-4gb-patch-linux` | root_mods step | [OK] essential (LAA) |
| UE ESM Fixes | `ue-esm-fixes-linux` | `./vnv.sh esmfix` | [OK] essential (inherit fallback) |
| Epic Games Patcher | `epic-games-patcher-linux` | root_mods step | [WARN] no-op on Steam (EGS only) |
| FNV BSA Decompressor | `fnv-bsa-decompressor-linux` | `./vnv.sh bsa` (research) | [ERROR] NOT needed (verdict above) |

Key port facts:
- **4GB**: native ELF `FalloutNVPatcher`; exits 0 even on failure -> detect by
  `FalloutNV_backup.exe` existing (now also verified by LAA in the PE header).
- **xNVSE**: `nvse_1_4.dll`, `nvse_steam_loader.dll`, `nvse_loader.exe` + pdbs -> game root.
- **uefix**: `.mpi` = LZ4-Frame-wrapped VCDIFF patches (magic `04 22 4D 18`); names in the
  index (`oldworldblues.esm.xd3`...) -> match by NAME; refuses `--dest` = game `Data/`.
- **BSA**: format details in the decompressor README (kept as reference).

---

## [FACTS] HARD TECHNICAL FACTS (verified in the real game)

- Plain `wine` does NOT run GUIs in the Proton prefix -> use `protontricks-launch 22380`.
- FNV launcher (`FalloutNVLauncher.exe`) is broken under Proton (process runs, no window) —
  the real entry is `FalloutNV.exe` via MO2.
- MO2 2.5.2 CLI: `ModOrganizer.exe --profile=Default run -e NVSE` (flag form `-e=NVSE` FAILS).
  With `steamAppID=` empty in customExecutables, no "Launch Steam" dialog.
- Game error log: ~1.5 KB = benign vanilla noise (RagdollConstraint rdt, "misnamed BSA" ×10,
  optional texture swaps, animation notes). 0 real MASTERFILE / MODEL ERROR.
- 28 NVSE plugins load (JIP LN v57.30, LOD Fixes v1.33, VanillaPlusTerrain, FART, kNVSE,
  ShowOff, etc.).
- JAM - VNV Configuration (`config/JustMods.ini`) = official VNV preset (sprint + QOL via MCM).
- Incompatible saves from another era of esms -> broken formids ("!" statics, pink DLC
  weapons). Fix: new game; game AUTO-LOADS the last save -> empty `Saves/` for clean tests.
- Shell footgun: `pkill -f` with a pattern in your own command line kills itself -> use
  `pkill -x` or kill by PID.

---

## [LIMITS] KNOWN LIMITS / NOT TESTED (honest)

- Nexus login in docker/VM: blocked by Turnstile anti-VM (works on real hardware).
- MO2 first-boot GUI (Sort button, dialogs) needs a human click on a real desktop; the CLI
  launch path is fully automatable.
- The `.mpi` cannot re-generate Fixed ESMs on the current Steam depot (mismatch) — inherit
  is the only reliable path. Pending: an .mpi that matches the current depot, if the mod
  author releases one.

---

## [RULES] SECURITY RULES

- Cookies in `~/.config/vnv-linux/` with chmod 600; credentials same (600).
- NEVER upload cookies/keys/password to the repos (gitignore: `.config/`, `estado.json`,
  `downloads/`, `venv/`, `repos/` — repos/ is a symlink-free checkout used at runtime).
- Mods are downloaded with YOUR Nexus session — the repos do not redistribute mods.
