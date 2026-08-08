# [VNV] VNV Linux — Viva New Vegas for Linux/Steam

<p align="center">
  <img src="assets/gecko.png" alt="Gecko de Fallout New Vegas" width="160">
</p>

**100% automatic** installer of the Viva New Vegas Core (55 mods) for Fallout New Vegas on Linux.

> [GAME] **A single command and it holds your hand:**
> ```bash
> ./vnv.sh ui
> ```
> A browser opens with a step-by-step wizard (big buttons, live progress).
> **You don't need to use the terminal.**

---

## [OK] What it does for you

| Step | What happens |
|---|---|
| 1 · Environment | Installs Python + Camoufox + libraries (works on Debian, Ubuntu, Arch, Fedora, openSUSE) |
| 2 · Nexus account | Automatic login (free, once) — passes the captcha on its own |
| 3 · Downloads | Downloads the 55 mods with automatic retries and integrity verification |
| 4 · Installation | Detects the game on Steam, creates the MO2 instance (MO2-LINT), imports the 55 mods, applies the INI tweaks, prepares LOOT |
| 5 · Play | Opens Steam -> "Launch Mod Organizer" -> Run, and FNV starts with everything loaded |

## Important notes - read before you start

- **Game language: English** - this installer and the VNV Core modpack are built for the **English** version of Fallout New Vegas. Localized builds (Spanish, German, French...) are not supported.
- **Steam version only** - everything is tested **only on the Steam version** (appid 22380). GOG and Epic versions are not supported by this installer.
- **Reference platform: Arch Linux / EndeavourOS** - developed and **100% verified there**; the setup, downloads, health checks and fallbacks were additionally verified on Ubuntu 24.04 and Arch (docker).

## [START] Getting started

```bash
git clone https://github.com/jhoniwana/vnv-linux
cd vnv-linux
./vnv.sh ui
```

Requirements: Steam with **Fallout New Vegas** installed and run once with Proton (creates the prefix) · Python 3.10+ · ~4 GB of space.

> [WARN] **Once, manually:** FNV -> Properties -> Compatibility -> force **Proton** -> Play 1 time (MO2-LINT recommends Proton 10, but any recent one works).

## [TOOLS] Useful commands (optional — the UI already does everything)

```bash
./vnv.sh setup          # prepares the environment (the UI does this in step 1)
./vnv.sh login          # Nexus login (step 2)
./vnv.sh download       # downloads mods with states and retries (step 3)
./vnv.sh estado         # verifies the 55 files
./vnv.sh bsa            # [WARN] NOT needed on the current depot (see "Tools you do NOT need")
./vnv.sh bsa-verify     # verify CRC64 name hashes without writing
./vnv.sh esmfix         # apply UE ESM Fixes (new port: name matching + validation + inherit)
./vnv.sh install        # MO2 + INIs + LOOT (step 4)
./vnv.sh run            # launches the game (step 5)
```

## [KEYS] Nexus account

- **Automatic login**: the UI (or `./vnv.sh login`) opens Camoufox (anti-detection Firefox) and passes Turnstile on its own. You only have to do it **once**.
- **Credentials**: save them with `./vnv.sh credenciales` (600 permissions) — used ONLY to re-login automatically if the session expires.
- The cookies (`nexusmods_session` + `cf_clearance`) live in `~/.config/vnv-linux/` and allow free downloads without Premium.

## If something fails

- The download manager **retries on its own** (3 attempts, waits for Cloudflare captchas, automatic re-login).
- `./vnv.sh estado` verifies file by file.
- The complete technical log is in **`BRAIN.md`** (APIs, endpoints, resolved bugs).

## Tools ported to Linux (root repos)

The installer delegates to 5 native repos (no Wine for the heavy lifting), all
**public** — and **cloned automatically** on first use (`repos/` is gitignored;
`root_mods.py` clones any missing port from GitHub):

| Tool | Repo | What it does |
|---|---|---|
| **NVSE / xNVSE** | `fnv-4gb-patch-linux` | 4GB/LAA patch + NVSE auto-load via `nvse_steam_loader` |
| **UE ESM Fixes** | `ue-esm-fixes-linux` | extracts and applies the xdelta3 patches from the `.mpi` (LZ4 frames) -> Fixed ESMs |
| **Epic Games Patcher** | `epic-games-patcher-linux` | EGS patching (no-op on Steam: detects LAA already applied) |
| **xNVSE** | `xnvse-linux` | installs the NVSE xNVSE DLLs into the game |

Notes:
- Each one accepts `VNV_STEAM_LIBRARY` (env) for alternate Steam libraries.
- **`ue-esm-fixes-linux`**: the ESMs must be from the current depot — if they come
  from another machine, run `steam steam://validate/22380` first (see its README:
  patches with a different source -> corrupted ESMs that crash the game during dialogue init).
- Steam verify reverts 4GB/NVSE/Fixed ESMs -> run `./vnv.sh install` afterwards (idempotent).

## Tools you do NOT need (verified 2026-08-07)

| Tool | Why it is not needed | Evidence |
|---|---|---|
| **FNV BSA Decompressor** | The 11 BSAs it decompresses already ship **raw** on the current Steam depot (old compressed-DLC era relic); the `.wav` audio files it "fixes" are already standard `RIFF....WAVE`; the only remaining BSAs with zlib (`Meshes.bsa`, `Misc.bsa`) must never be decompressed (32-bit game -> startup crash). It also requires the full 21-BSA `SArchiveList`, which the installer already applies permanently | header parse of all 21 BSAs (30/30 files raw, bit30 on every record) + `.wav` extracted from the 3 DLC Sounds BSAs + VNV guide + decompiled official exe (xEdit wbBSArchive) |
| **FNV 4GB Patcher (EGS variant)** | Only relevant for the Epic Games Store version; on Steam the LAA flag is already handled (`0xA620`) — the Steam launcher (`nvse_steam_loader`) loads NVSE automatically | `fnv-4gb-patch-linux` reports "LAA already applied" on Steam |

The complete technical investigation lives in
**`repos/fnv-bsa-decompressor-linux/README.md`** (deep investigation section) and
**`BRAIN.md`** (`DECOMPRESSOR — 100% NOT NEEDED`).

## [RULES] Legal

The mods are downloaded from Nexus with YOUR session (free). This project does not redistribute mods — it only downloads and installs them. Requires owning the game on Steam.
