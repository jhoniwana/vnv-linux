# 🔁 HANDOFF — VNV Linux Installer (automation guide)

Message for the agent that continues this project. Read it completely before acting.

---

## 1. WHAT THIS IS

**vnv-linux**: 100% automatic installer of the **Viva New Vegas** Core for **Linux + Steam**.
- 55 mods (Core VNV + JAM as requested extra), native root mods (no Wine), launch via MO2 CLI.
- Public repo: `https://github.com/jhoniwana/vnv-linux` (branch `main`)
- Local code: the folder where the repo was cloned (portable — no absolute paths)
- Docs: `BRAIN.md` (technical log) + `obsidian/` + this HANDOFF.

---

## 2. CURRENT STATE — 100% VERIFIED (7 aug 2026)

| Component | State |
|---|---|
| **55 mods downloaded** + 5 extras, 0 HTML | ✅ (includes JAM 66666 + YUPDate/supplement 98514) |
| **55 mods imported** into MO2 | ✅ 50 active + 5 root (disabled, correct) + Fixed ESMs active |
| **Canonical VNV Core load order** | ✅ 23 plugins: base esms → YUP → d20Fixes → UPNVSE+ → NVMIM(-YUP) → FaceGen → Strip Lights → LDF → LTI(-YUP) → fixy → Placements → JAM |
| **Root mods** | ✅ xNVSE (nvse_1_4 + steam_loader), 4GB (LAA=0x20 + import), decompressed BSAs (21, bit30 on all), UE ESM Fixes CORRECT rebuild |
| **Fixed ESMs (rebuild 7 aug)** | ✅ **465,054 records, DIALOG 18,215, INFO 23,247** (the old build had 233K records and 0 dialogues → crash) |
| **INIs** | ✅ nvtf.ini (heap 400 + 4GB + VRAM, in-game and in mod), FalloutCustom.ini (Default profile) |
| **Guide extras** | ✅ JIP Settings INI, Stewie INI, JohnnyGuitar INI Presets, LOD Fixes INI, **JAM - VNV Configuration** (JustMods.ini) |
| **Game** | ✅ runs stable, 28 NVSE plugins loaded, new game playing without visible errors |
| **Error log** | ✅ 1.5 KB = only benign vanilla noise (rdt, misnamed BSA, optional texture swaps) |
| **JGNVSE "EDIDs conflicting"** | ✅ only 1 benign conflict (UPNVSE+ vs YUP: `UPNVSEPVendorQuestItemSCRIPT`) — the vanilla DLC conflicts disappeared with the correct Fixed ESMs |

---

## 3. THE PIPELINE (step by step, commands + logic)

### 3.1 Setup and installation
```bash
./vnv.sh setup            # system deps + venv + Camoufox (multi-distro)
./vnv.sh login            # Nexus cookies (Camoufox passes Turnstile)
./vnv.sh config           # API key (metadata)
./vnv.sh credenciales     # email+pass (automatic re-login)
./vnv.sh download         # actualizar.py (metadata) + gestor_descargas.py (downloads everything)
./vnv.sh install          # importar_mo2.py + root_mods.py + tweaks_ini
./vnv.sh estado           # verifies downloads vs manifest
./vnv.sh run              # launches the game via MO2 CLI (NVSE)
./vnv.sh mo2              # opens the MO2 manager (GUI) — also from Steam (lanzar-mo2.sh)
./vnv.sh steam-add        # adds "Fallout New Vegas (VNV)" to the Steam library (non-Steam)
```

### 3.2 Logic of each script (final state — DO NOT break)
- **`scripts/actualizar.py`** — updates `manifest.json` (names/versions/file_ids) choosing the most recent **MAIN** (`max(uploaded_timestamp)`). ⚠️ CAUTION: if the mod has per-variant versions (e.g. "Placement Fixes TTW" vs "Placement Fixes"), the most recent MAIN may be the wrong variant → verify masters (historical bug 90593 → TTW).
- **`scripts/gestor_descargas.py`** — states in `estado.json` (pending/downloading/ok/failed), retries with backoff, automatic re-login. **Extras with `url` use direct download** (GitHub); extras with `file_id` go through Nexus. ⚠️ Validate that `estado.json` points to the CORRECT file (there were cases where main↔extra got crossed: 58277 JIP dll, 84171 LOD INI).
- **`scripts/importar_mo2.py`** — decompresses each mod to `mods/<Nombre>/` (FOMOD with explicit per-mod choices), merges extras, and **always regenerates the profile lists with the full manifest**:
  - `modlist.txt`: **preserves the previous +/- state** (manual toggles survive — fix 0ffc8ce).
  - `loadorder.txt`/`plugins.txt`: canonical VNV Core order (GUIAS_PLUGINS) — MO2 2.5.2 format: **WITHOUT `*`**, CRLF, header.
  - `--solo MOD_ID`: re-imports ONE mod **without touching the lists** (preserves exact loadorder and inserts the new plugin after its master — fix b7782f3).
- **`scripts/root_mods.py`** — delegates to the 5 root repos: `xnvse` (copies dlls + steam_loader), `4gb` (native LAA patch), `epic` (no-op on Steam), `bsa` (decompress.py — the 11 BSAs with 0x100 → bit30 + raw), `uefix` (port.py — xdelta3 patches from the .mpi).
  - ⚠️ **CRITICAL ORDER**: Steam verify reverts the 4GB and the esms → if `steam steam://validate/22380` is run, `./vnv.sh root` (4gb + bsa + uefix) must be re-run AFTERWARDS.
- **`repos/ue-esm-fixes-linux/port.py`** — extracts the LZ4/xdelta3 patches from the `.mpi` and applies them to the Data esms. ⚠️ **The patches demand the EXACT vanilla esms of the current depot** (esms copied by the user from another machine do NOT match → corrupted esms with a valid TES4 header but missing records → dialogue crash). After a Steam verify the esms are correct and the rebuild succeeds.
- **`vnv.sh preparar_lanzamiento()`** — re-syncs `plugins.txt` from `loadorder.txt` if MO2 desynced them (MO2 2.5.2 rewrites them on close).
- **`vnv.sh correr_loot()`** — LOOT validates against a COPY (lootcli can't see MO2's VFS) — never touches the profile.
- **`tweaks_ini`** — nvtf.ini (heap 400MB, 4GB, VRAM) in `Data/NVSE/Plugins/` + a copy in the NVTF mod; FalloutCustom.ini in `profiles/Default/`.

### 3.3 Launch
- Correct MO2 CLI: `ModOrganizer.exe --profile=Default run -e NVSE` (`-e` with no value; `-e=NVSE` does NOT work).
- The game **AUTO-LOADS the last save** on start → when testing configurations, empty `Saves/` in the prefix or the test loads the old game.
- Old saves from another installation are **incompatible** (formids renumbered by the UE fixes) → "!"/pink textures. New game = everything OK.

---

## 4. HISTORICAL BUGS (all resolved — do not reintroduce)

1. **Mod 90593 TTW** — actualizar.py chose the TTW variant → master `TaleOfTwoWastelands.esm` → crash. Fix: manual file_id `1000152138` + master verification.
2. **plugins.txt with `*`** — MO2 2.5.2 doesn't use `*` (treats it as part of the name → no plugin recognized).
3. **`--solo` overwrote the lists** → modlist of 1 mod → MO2 disabled everything ("mods not configured").
4. **Crossed estado.json** (58277 main→INI, 84171 extra→main) → `jip_nvse.dll` and `LOD Fixes.ini` were missing.
5. **Corrupted Fixed ESMs** (old esm source from the user) → missing records → deterministic crash `0x00AA991C` during dialogue init (context: YUP "Doctors" records). Correct rebuild post-verify.
6. **Incomplete SArchiveList** (only 6 base BSAs) in the 3 inis → DLC without assets. Fix: 21 BSAs, `Update.bsa` last.
7. **Incorrect load order** (YUP 8th) → intermittent dialogue crash. Fix: canonical order.
8. **Re-activation of disabled mods** by the modlist regeneration → preserve states.
9. **Steam verify reverts 4GB/BSAs/esms** → re-run root_mods afterwards.

---

## 5. WHAT'S LEFT (polish, nothing in the pipeline)

- Test `./vnv.sh setup` on a real Debian/Ubuntu (only tested on Arch).
- Social preview of the repo (`assets/gecko.png` in GitHub settings).
- Security: regenerate Nexus password + API key (`./vnv.sh config`) + `./vnv.sh credenciales`.
- Verify a full `./vnv.sh install` on a clean machine (recreate the state from scratch).

## 6. IMPORTANT RULES

- **NEVER upload credentials**; keep `downloads/`, `venv/`, `~/.config/` out of the repo.
- **Always** use `./venv/camoufox-python` (never `python3`) for the Nexus scripts.
- **Nexus rate limits**: 5s between API calls, 8-15s between downloads.
- Root repos **private** (copyrighted binaries) — do not make them public.
- The UE fixes `.mpi` (220 MB) stays out of the repo; `port.py` extracts it from the `.7z` to `~/.cache/vnv-uefix/` with 7z.
- The repo does NOT redistribute mods (they are downloaded with the user's session).

## 7. REFERENCES

- `BRAIN.md` — full technical detail.
- `obsidian/` — documentation vault (`Inicio.md` is the hub).
- `README.md` — user guide.
- Commands: `./vnv.sh {setup|login|config|credenciales|download|estado|install|loot|run|mo2|steam-add|ui}`
