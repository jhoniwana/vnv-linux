# 🎁 VNV Linux — Guide for a friend

100% automatic installer of the **Viva New Vegas** Core on Linux + Steam.

## What you need

- Linux (Arch, Debian/Ubuntu, Fedora, openSUSE)
- Fallout: New Vegas bought on Steam (installed)
- A free Nexus Mods account (to download the mods)

## Steps (in order)

```bash
# 1. Clone the repo
git clone https://github.com/jhoniwana/vnv-linux
cd vnv-linux

# 2. Environment setup (system deps + Python + Camoufox)
./vnv.sh setup

# 3. Nexus login (an anti-detection browser opens; log in with YOUR account)
./vnv.sh login

# 4. Save your Nexus API key (https://www.nexusmods.com/settings/api-keys)
./vnv.sh config

# 5. Save your email+password (for automatic re-login)
./vnv.sh credenciales

# 6. Download the 55 mods (1.1 GB — takes a while, it's automatic)
./vnv.sh download

# 7. Verify everything is OK
./vnv.sh estado

# 8. Install everything (MO2 + mods + root mods + INIs) — Steam must be closed
./vnv.sh install

# 9. Let's play!
./vnv.sh run
```

## Optional (handy)

- **From Steam**: `./vnv.sh steam-add` adds "Fallout New Vegas (VNV)" to your library
  (opens the MO2 manager → Run button → game).
- **Web interface**: `./vnv.sh ui` (terminal-free wizard).

## Important notes

- **The mods are NOT in the repo** (copyright of their authors). They are downloaded
  automatically with YOUR Nexus account.
- The game runs on a **new game** — saves from another installation are not compatible.
- If Steam updates the game (verify), run `./vnv.sh install` afterwards (re-applies
  4GB, NVSE, Fixed ESMs and the INI tweaks). The BSA Decompressor is NOT used
  (vanilla BSAs are optimal).
- Sprint and QOL: JAM is configured in-game (ESC → Mod Configuration → Just Assorted Mods).
- Any questions: the error log is in `HANDOFF.md` and `BRAIN.md`.
