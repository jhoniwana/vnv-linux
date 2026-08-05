---
tags: [guia, steam, proton, mo2]
---
# Conexión Steam ↔ MO2

Cómo se conecta el modloader con Steam (paso 1 del flujo de instalación).

## Realidad: no hay modloader nativo

- **MO2/Vortex**: apps .NET de Windows → corren con **Wine/Proton**
- **NexusMods.App** (oficial): nativa Linux pero **NO soporta FNV** (solo FO4, Cyberpunk, etc.)
- Conclusión: **MO2 vía Proton es el estándar**

## El mecanismo

```
Steam (FNV, appid 22380)
   │  forzar Proton (Steam Play)
   ▼
Prefix de Proton del juego (steamapps/compatdata/22380/pfx)
   │  protontricks: MO2 corre DENTRO de ese prefix
   ▼
MO2 → botón Run → FalloutNV.exe con los mods montados (VFS)
```

- **Protontricks** = la pieza clave: ejecuta programas en el prefix de Proton de un juego
- **MO2-LINT** automatiza: `mo2-installer install --game fallout-new-vegas`
- **VFS de MO2**: los mods se montan virtualmente — el directorio del juego NO se modifica

## Comando

```bash
./vnv.sh steam          # diagnostica Steam, FNV, prefix, protontricks
./vnv.sh steam --si     # además lanza FNV con Proton para crear el prefix (no-interactivo)
```

## Si el prefix no existe

1. Steam → FNV → Propiedades → Compatibilidad → forzar Proton
2. Jugar una vez (crea el prefix) — o correr `./vnv.sh steam --si`

## Referencias

- [[Lanzamiento del Juego]] — qué hacer después
- [[Problemas Comunes]]
