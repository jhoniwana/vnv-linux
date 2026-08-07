---
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
