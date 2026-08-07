---
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
