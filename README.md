# ⚡ VNV Linux — Viva New Vegas for Linux/Steam

<p align="center">
  <img src="assets/gecko.png" alt="Gecko de Fallout New Vegas" width="160">
</p>

**100% automatic** installer of the Viva New Vegas Core (53 mods) for Fallout New Vegas on Linux.

> 🎮 **A single command and it holds your hand:**
> ```bash
> ./vnv.sh ui
> ```
> A browser opens with a step-by-step wizard (big buttons, live progress).
> **You don't need to use the terminal.**

---

## ✅ What it does for you

| Step | What happens |
|---|---|
| 1 · Environment | Installs Python + Camoufox + libraries (works on Debian, Ubuntu, Arch, Fedora, openSUSE) |
| 2 · Nexus account | Automatic login (free, once) — passes the captcha on its own |
| 3 · Downloads | Downloads the 53 mods with automatic retries and integrity verification |
| 4 · Installation | Detects the game on Steam, creates the MO2 instance (MO2-LINT), imports the 53 mods, applies the INI tweaks, prepares LOOT |
| 5 · Play | Opens Steam → "Launch Mod Organizer" → Run, and FNV starts with everything loaded |

## 🚀 Getting started

```bash
git clone https://github.com/jhoniwana/vnv-linux
cd vnv-linux
./vnv.sh ui
```

Requirements: Steam with **Fallout New Vegas** installed and run once with Proton (creates the prefix) · Python 3.10+ · ~4 GB of space.

> ⚠️ **Once, manually:** FNV → Properties → Compatibility → force **Proton** → Play 1 time (MO2-LINT recommends Proton 10, but any recent one works).

## 🛠️ Useful commands (optional — the UI already does everything)

```bash
./vnv.sh setup          # prepares the environment (the UI does this in step 1)
./vnv.sh login          # Nexus login (step 2)
./vnv.sh download       # downloads mods with states and retries (step 3)
./vnv.sh estado         # verifies the 53 files
./vnv.sh bsa            # decompress the game BSAs (xEdit semantics fix)
./vnv.sh bsa-verify     # verify CRC64 name hashes without writing
./vnv.sh esmfix         # apply Ultimate Edition ESM Fixes (xdelta patches)
./vnv.sh install        # MO2 + INIs + LOOT (step 4)
./vnv.sh run            # launches the game (step 5)
```

## 🔑 Nexus account

- **Automatic login**: the UI (or `./vnv.sh login`) opens Camoufox (anti-detection Firefox) and passes Turnstile on its own. You only have to do it **once**.
- **Credentials**: save them with `./vnv.sh credenciales` (600 permissions) — used ONLY to re-login automatically if the session expires.
- The cookies (`nexusmods_session` + `cf_clearance`) live in `~/.config/vnv-linux/` and allow free downloads without Premium.

## 🐛 If something fails

- The download manager **retries on its own** (3 attempts, waits for Cloudflare captchas, automatic re-login).
- `./vnv.sh estado` verifies file by file.
- The complete technical log is in **`BRAIN.md`** (APIs, endpoints, resolved bugs).

## 🔧 Tools ported to Linux (root repos)

The installer delegates to 5 native repos (no Wine for the heavy lifting), all
**private** by the user's decision (they contain copyrighted binaries):

| Tool | Repo | What it does |
|---|---|---|
| **NVSE / xNVSE** | `fnv-4gb-patch-linux` | 4GB/LAA patch + NVSE auto-load via `nvse_steam_loader` |
| **FNV BSA Decompressor** | `fnv-bsa-decompressor-linux` | decompresses the 11 BSAs with flag 0x100 (bit30 + raw, game-compatible) |
| **UE ESM Fixes** | `ue-esm-fixes-linux` | extracts and applies the xdelta3 patches from the `.mpi` (LZ4 frames) → Fixed ESMs |
| **Epic Games Patcher** | `epic-games-patcher-linux` | EGS patching (no-op on Steam: detects LAA already applied) |
| **xNVSE** | `xnvse-linux` | installs the NVSE xNVSE DLLs into the game |

Notes:
- Each one accepts `VNV_STEAM_LIBRARY` (env) for alternate Steam libraries.
- **`ue-esm-fixes-linux`**: the ESMs must be from the current depot — if they come
  from another machine, run `steam steam://validate/22380` first (see its README:
  patches with a different source → corrupted ESMs that crash the game during dialogue init).
- Steam verify reverts 4GB/BSAs/ESMs → run `./vnv.sh root` afterwards.

## 📜 Legal

The mods are downloaded from Nexus with YOUR session (free). This project does not redistribute mods — it only downloads and installs them. Requires owning the game on Steam.
