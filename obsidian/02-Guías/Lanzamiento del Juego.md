---
tags: [guia, lanzamiento, mo2, teoria]
---
# Lanzamiento del Juego

> ⚠️ **Teoría** — este paso requiere hardware real con Steam + FNV. No probado aún.

## Secuencia completa

1. `mo2-installer install --game fallout-new-vegas` → MO2 en el prefix del juego
2. `mo2-installer run --game fallout-new-vegas` → abre MO2 con el entorno Wine del juego
3. El perfil "Default" ya tiene los 53 mods importados ([[Importar a MO2]])
4. **LOOT** (primera vez): botón Sort en MO2 → ordena plugins → escribe `loadorder.txt`
5. **Run** en MO2 → lanza `FalloutNV.exe` con el VFS (mods montados virtualmente)
6. NVTF aplica heap + 4GB + vsync desde `Data/NVSE/Plugins/nvtf.ini` (lo escribe `tweaks_ini`)
7. FNV en Proton: **fullscreen-only** — la guía VNV recomienda fullscreen + NVTF

## Troubleshooting

| Problema | Solución |
|---|---|
| Crash al inicio | Verificar `nvtf.ini` (EnableHeapReplacement) y NVTF activo en el modlist |
| Sin mods cargados | Lanzar DESDE MO2 (no desde Steam directo); perfil Default activo |
| Pantalla negra | Fullscreen; probar Proton GE |
| LOOT no ordena | Correr LOOT desde MO2; reinstalar con `mo2-installer install` |

## Referencias

- [[Conexión Steam]] — paso previo
- [[Problemas Comunes]]
