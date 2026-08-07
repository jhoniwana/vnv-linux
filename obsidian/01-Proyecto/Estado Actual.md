---
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
