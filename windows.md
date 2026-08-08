# 🪟 VNV Core para Windows (amigo) — Instalación con Mod Organizer 2

> Guía completa para que MO2 en Windows detecte y active TODO automáticamente.
> Generada desde la instalación Linux verificada (Viva New Vegas Core, 55 mods).

## 0 · Requisitos previos (hacer una sola vez)

1. **Fallout New Vegas + todos los DLCs** instalado (Steam o GOG), **ejecutado una vez** (crea el prefix/registro).
2. **Mod Organizer 2** instalado desde [MO2 Nexus](https://www.nexusmods.com/site/mods/62805) o GitHub.
3. **Nexus Premium o sesión activa** para descargas automáticas (o descargar a mano).

> ⚠️ **IMPORTANTE**: NO uses el "FNV BSA Decompressor" en esta instalación.
> En el depot actual (2026) es un **no-op** (las BSAs ya vienen sin comprimir) y
> descomprimir `Meshes.bsa`/`Misc.bsa` hace **crash el juego** (32-bit).
> Usa solo los pasos de abajo.

---

## 1 · Los 55 mods (descargar en Nexus)

| Mod ID | File ID | Sección | Nombre |
|---|---|---|---|
| 51664 | [1000174766](https://www.nexusmods.com/newvegas/mods/51664?tab=files&file_id=1000174766) | bugfix | Yukichigai Unofficial Patch - YUP |
| 57174 | [1000080073](https://www.nexusmods.com/newvegas/mods/57174?tab=files&file_id=1000080073) | utilities | UIO - User Interface Organizer |
| 58277 | [1000132314](https://www.nexusmods.com/newvegas/mods/58277?tab=files&file_id=1000132314) | utilities | JIP LN NVSE Plugin |
| 62552 | [1000079136](https://www.nexusmods.com/newvegas/mods/62552?tab=files&file_id=1000079136) | utilities | FNV 4GB Patcher |
| 65854 | [1000136741](https://www.nexusmods.com/newvegas/mods/65854?tab=files&file_id=1000136741) | utilities | FNV BSA Decompressor |
| 65906 | [1000122282](https://www.nexusmods.com/newvegas/mods/65906?tab=files&file_id=1000122282) | utilities | Console Paste Support |
| 66347 | [1000177460](https://www.nexusmods.com/newvegas/mods/66347?tab=files&file_id=1000177460) | bugfix | lStewieAl's Tweaks and Engine Fixes |
| 66537 | [1000156835](https://www.nexusmods.com/newvegas/mods/66537?tab=files&file_id=1000156835) | utilities | NVTF - New Vegas Tick Fix |
| 66666 | [1000133586](https://www.nexusmods.com/newvegas/mods/66666?tab=files&file_id=1000133586) | utilities | Just Assorted Mods |
| 66927 | [1000175713](https://www.nexusmods.com/newvegas/mods/66927?tab=files&file_id=1000175713) | utilities | JohnnyGuitar NVSE |
| 67883 | [1000175507](https://www.nexusmods.com/newvegas/mods/67883?tab=files&file_id=1000175507) | utilities | New Vegas Script Extender (NVSE xNVSE) |
| 68714 | [1000172551](https://www.nexusmods.com/newvegas/mods/68714?tab=files&file_id=1000172551) | utilities | FNV Mod Limit Fix |
| 70801 | [1000120606](https://www.nexusmods.com/newvegas/mods/70801?tab=files&file_id=1000120606) | utilities | Improved Console (NVSE) |
| 71239 | [1000174627](https://www.nexusmods.com/newvegas/mods/71239?tab=files&file_id=1000174627) | bugfix | Unofficial Patch NVSE Plus |
| 71336 | [1000142858](https://www.nexusmods.com/newvegas/mods/71336?tab=files&file_id=1000142858) | utilities | kNVSE Animation Plugin |
| 71577 | [1000164167](https://www.nexusmods.com/newvegas/mods/71577?tab=files&file_id=1000164167) | bugfix | Mostly Fixed FaceGen Tints (NV or TTW) |
| 71973 | [1000074493](https://www.nexusmods.com/newvegas/mods/71973?tab=files&file_id=1000074493) | bugfix | Combat Lag Fix (NVSE) |
| 72541 | [1000172754](https://www.nexusmods.com/newvegas/mods/72541?tab=files&file_id=1000172754) | utilities | ShowOff xNVSE Plugin |
| 73596 | [1000167222](https://www.nexusmods.com/newvegas/mods/73596?tab=files&file_id=1000167222) | bugfix | Strip Lights Region Fix |
| 73937 | [1000174034](https://www.nexusmods.com/newvegas/mods/73937?tab=files&file_id=1000174034) | bugfix | Landscape Disposition Fix |
| 74295 | [1000165242](https://www.nexusmods.com/newvegas/mods/74295?tab=files&file_id=1000165242) | bugfix | New Vegas Mesh Improvement Mod - NVMIM |
| 75417 | [1000112545](https://www.nexusmods.com/newvegas/mods/75417?tab=files&file_id=1000112545) | utilities | ISControl Enabler and Ironsights adjuster (now ESPless) |
| 77073 | [1000132747](https://www.nexusmods.com/newvegas/mods/77073?tab=files&file_id=1000132747) | bugfix | Misc Audio Tweaks and Fixes |
| 77205 | [1000094799](https://www.nexusmods.com/newvegas/mods/77205?tab=files&file_id=1000094799) | bugfix | Climate Control NVSE |
| 79358 | [1000178007](https://www.nexusmods.com/newvegas/mods/79358?tab=files&file_id=1000178007) | utilities | Viva New Vegas Resources |
| 80316 | [1000125920](https://www.nexusmods.com/newvegas/mods/80316?tab=files&file_id=1000125920) | bugfix | Fallout Alpha Rendering Tweaks - NVSE |
| 80443 | [1000170915](https://www.nexusmods.com/newvegas/mods/80443?tab=files&file_id=1000170915) | bugfix | External Emittance Fix - NVSE |
| 80666 | [1000107287](https://www.nexusmods.com/newvegas/mods/80666?tab=files&file_id=1000107287) | bugfix | ActorCause Save Bloat Fix |
| 80993 | [1000115492](https://www.nexusmods.com/newvegas/mods/80993?tab=files&file_id=1000115492) | bugfix | lStewieAl's Engine Optimizations |
| 81200 | [1000162968](https://www.nexusmods.com/newvegas/mods/81200?tab=files&file_id=1000162968) | bugfix | Depth of Field Fix - NVSE |
| 81201 | [1000169890](https://www.nexusmods.com/newvegas/mods/81201?tab=files&file_id=1000169890) | bugfix | Muzzle Flash Light Fix - NVSE |
| 81281 | [1000129652](https://www.nexusmods.com/newvegas/mods/81281?tab=files&file_id=1000129652) | utilities | Epic Games Patcher |
| 81775 | [1000141500](https://www.nexusmods.com/newvegas/mods/81775?tab=files&file_id=1000141500) | bugfix | PipBoyOn Node Fixes |
| 81933 | [1000166344](https://www.nexusmods.com/newvegas/mods/81933?tab=files&file_id=1000166344) | bugfix | Iron Sights Aligned |
| 82042 | [1000162222](https://www.nexusmods.com/newvegas/mods/82042?tab=files&file_id=1000162222) | bugfix | skinned mesh improvement mod - redone redux remake retry revengeance retopology refridgerator |
| 82540 | [1000172208](https://www.nexusmods.com/newvegas/mods/82540?tab=files&file_id=1000172208) | utilities | Yvile's Crash Logger |
| 83425 | [1000150443](https://www.nexusmods.com/newvegas/mods/83425?tab=files&file_id=1000150443) | bugfix | Landscape Texture Improvements (FNV - TTW) |
| 83815 | [1000174474](https://www.nexusmods.com/newvegas/mods/83815?tab=files&file_id=1000174474) | bugfix | Meshes and Collision - Totally Enhanced Nifs (MAC-TEN) |
| 84171 | [1000150632](https://www.nexusmods.com/newvegas/mods/84171?tab=files&file_id=1000150632) | bugfix | LOD Fixes and Improvements - NVSE |
| 84443 | [1000169893](https://www.nexusmods.com/newvegas/mods/84443?tab=files&file_id=1000169893) | bugfix | Viewmodel Shake Fix - NVSE |
| 84781 | [1000145573](https://www.nexusmods.com/newvegas/mods/84781?tab=files&file_id=1000145573) | bugfix | Viewmodel Shading Fix - NVSE |
| 84823 | [1000123023](https://www.nexusmods.com/newvegas/mods/84823?tab=files&file_id=1000123023) | bugfix | VATS Lag Fix |
| 85198 | [1000167727](https://www.nexusmods.com/newvegas/mods/85198?tab=files&file_id=1000167727) | bugfix | 3rd Person Animation Fixpack |
| 85622 | [1000155727](https://www.nexusmods.com/newvegas/mods/85622?tab=files&file_id=1000155727) | bugfix | Items Transformed - Enhanced Meshes (ITEM) |
| 85748 | [1000150970](https://www.nexusmods.com/newvegas/mods/85748?tab=files&file_id=1000150970) | utilities | hNVSE |
| 86136 | [1000151133](https://www.nexusmods.com/newvegas/mods/86136?tab=files&file_id=1000151133) | utilities | No Exit to Main Menu |
| 86200 | [1000175896](https://www.nexusmods.com/newvegas/mods/86200?tab=files&file_id=1000175896) | utilities | JohnnyGuitar NVSE - INI Presets |
| 87814 | [1000169903](https://www.nexusmods.com/newvegas/mods/87814?tab=files&file_id=1000169903) | utilities | Shader Loader - NVSE |
| 87830 | [1000140291](https://www.nexusmods.com/newvegas/mods/87830?tab=files&file_id=1000140291) | bugfix | Blood Decal Flashing Fix |
| 90593 | [1000152138](https://www.nexusmods.com/newvegas/mods/90593?tab=files&file_id=1000152138) | bugfix | Vanilla Placement Fixes |
| 91705 | [1000160476](https://www.nexusmods.com/newvegas/mods/91705?tab=files&file_id=1000160476) | bugfix | LOD Flicker Fix - NVSE |
| 92289 | [1000176515](https://www.nexusmods.com/newvegas/mods/92289?tab=files&file_id=1000176515) | utilities | Ultimate Edition ESM Fixes Remastered |
| 92519 | [1000154397](https://www.nexusmods.com/newvegas/mods/92519?tab=files&file_id=1000154397) | bugfix | Vanilla Plus Terrain |
| 96007 | [1000177683](https://www.nexusmods.com/newvegas/mods/96007?tab=files&file_id=1000177683) | bugfix | Third Person Aim Fix NVSE |
| 98514 | [1000179156](https://www.nexusmods.com/newvegas/mods/98514?tab=files&file_id=1000179156) | bugfix | Supplementary Fixes And Tweaks (YUPDate) |

**Cómo descargar**: entra a cada `Mod ID` → pestaña *Files* → descarga el *File ID* indicado.
Si usas **MO2 → botón "Download with Mod Manager"**, los archivos caen solos a `Downloads/`.
Puedes usar **Nexus auto-downloader** o **"Mods downloader"** (extensión) para bajar los 55 de corrido con tu sesión.

---

## 2 · Estructura de mods en MO2 (para que "detecte todo")

### A) Mods "normales" → carpeta `mods/` del perfil
MO2 → *left pane → Install from file* (o `Downloads/` → doble clic). El **nombre del mod en MO2**
debe quedar como en `modlist.txt` de abajo para que el orden de prioridad se respete.

### B) Mods "root" → VAN AL JUEGO DIRECTAMENTE (NO a MO2)

**¿Qué es un mod root?** Los root mods modifican archivos que viven en la **carpeta del juego**
(no en la VFS de MO2): DLLs del engine, el exe, etc. Por eso **NO se instalan como mods de MO2**
(si los metes en MO2, el juego no los ve — el engine los busca en su propia carpeta).
En `modlist.txt` aparecen con `-` (desactivados) solo como recordatorio.

**Carpeta del juego en Windows:**
```
Steam:  C:\Program Files (x86)\Steam\steamapps\common\Fallout New Vegas\
GOG:    C:\GOG Games\Fallout New Vegas\    (o donde lo instales)
```

**Lista completa de root mods de VNV Core:**

| Root mod | Archivos que van al juego | Estado |
|---|---|---|
| **xNVSE** (NVSE) | `nvse_1_4.dll`, `nvse_loader.exe`, `nvse_steam_loader.dll`, `nvse_editor_1_4.dll` + los 4 `.pdb` | **OBLIGATORIO** |
| **FNV 4GB Patcher** | Parchea `FalloutNV.exe` (habilita LAA 4GB) | **OBLIGATORIO** |
| Epic Games Patcher | Parchea `FalloutNV.exe` | Solo versión Epic (no-op en Steam) |
| FNV BSA Decompressor | — | **NO INSTALAR** |

**Cómo instalar xNVSE en Windows (paso a paso):**
1. Descarga **xNVSE** en Nexus: [New Vegas Script Extender (xNVSE)](https://www.nexusmods.com/newvegas/mods/67883) → archivo **Main file** (`xNVSE 6.x.x.7z`).
2. Extrae el `.7z` (7-Zip o WinRAR) → dentro hay una carpeta `nvse_6_x_x/`.
3. Copia estos archivos a la **carpeta del juego** (junto a `FalloutNV.exe`):
   ```
   nvse_1_4.dll          ← el plugin del engine (¡el que el juego carga!)
   nvse_steam_loader.dll ← cargador automático (Steam) / nvse_loader.exe (GOG)
   nvse_editor_1_4.dll   ← soporte del GECK (editor)
   nvse_1_4.pdb / nvse_steam_loader.pdb / nvse_editor_1_4.pdb / nvse_loader.pdb
   ```
4. Verifica que queden **en la misma carpeta que `FalloutNV.exe`**, así:
   ```
   Fallout New Vegas/
   ├── FalloutNV.exe
   ├── nvse_1_4.dll        ← aquí
   ├── nvse_steam_loader.dll ← aquí
   ├── Data/
   └── ...
   ```
5. (Opcional pero recomendado) extrae también `Data/NVSE/` (los INIs de configuración de NVSE).
6. Prueba: arranca el juego → en el menú principal verás **"NVSE version 6.x"** abajo a la izquierda.
   También se crea `nvse.log` en la carpeta del juego (muestra los plugins NVSE cargados).

> 💡 **Para MO2**: el mod `-New Vegas Script Extender (NVSE xNVSE)` queda desactivado — es solo
> el recordatorio de que esto va root. Si instalaste xNVSE con el instalador/extracción manual,
> MO2 no tiene que tocar nada de esto.

**Cómo instalar el FNV 4GB Patcher en Windows:**
1. Descarga **FNV 4GB Patcher**: [New Vegas 4GB Patcher (mods 62552)](https://www.nexusmods.com/newvegas/mods/62552) → Main file.
2. Extrae `FalloutNVPatcher.exe` a la carpeta del juego (junto a `FalloutNV.exe`).
3. **Clic derecho → Ejecutar como administrador** (o simplemente doble clic si Steam no está en Program Files).
4. El patcher crea una copia de seguridad automática: `FalloutNV_backup.exe` y parchea `FalloutNV.exe`
   (habilita el flag LAA 4GB). **Cierra el juego antes** — no se puede parchear un exe en uso.
5. Verificación: el `FalloutNV_backup.exe` existe junto al exe parcheado ✓.
6. (Recomendado por VNV) el `nvse_steam_loader.dll` de xNVSE ya inyecta NVSE solo; el 4GB patch
   es independiente.

> ⚠️ Si alguna vez revalidad el juego en Steam (Verify integrity), **se revierten** los root mods
> (exe y DLLs vuelven a vanilla) → re-ejecuta el 4GB patcher y vuelve a copiar las DLLs de xNVSE.

**Epic Games Patcher** (solo si tu juego es de Epic Games Store):
- Descarga [Epic Games Patcher](https://www.nexusmods.com/newvegas/mods/81281) → extrae `patch.xdelta`
  + `FalloutNVPatcher.exe` a la carpeta del juego → ejecuta. En Steam **no hace falta** (el exe ya es compatible).

### C) Fixed ESMs (esencial — el juego crashea sin esto)
Extraer en `mods/Fixed ESMs/` (se activa como `+Fixed ESMs`):

```
DeadMoney.esm      FalloutNV.esm       GunRunnersArsenal.esm
HonestHearts.esm   LonesomeRoad.esm    OldWorldBlues.esm
```

> Son los ESMs parcheados (Ultimate Edition ESM Fixes Remastered). Se activan vía VFS de MO2.

> ⚠️ **IMPORTANTE (2026)**: el `.mpi` v1.03 del mod NO matchea los ESMs del
> depot actual de Steam (diferencias de ±bytes) — el instalador de Nexus falla
> con "checksum mismatch" / "source file too short". **NO fuerces la aplicación**
> (produce ESMs con TES4 válido pero records faltantes → crash `0x00AA991C`
> al iniciar). La forma correcta: **heredar los 6 ESMs de una instalación que
> ya funciona** (cópialos desde ahí a `mods/Fixed ESMs/`). En Windows, si ya
> tenías los Fixed ESMs de antes, cópialos tal cual (son idénticos — mismo juego).

---

## 3 · Perfil de MO2: `Default` (copiar estos 3 archivos)

Ruta en Windows: `%LOCALAPPDATA%/ModOrganizer/falloutnv/profiles/Default/`
(o `MO2/portable/profiles/Default` si usas **MO2 portable — recomendado**).

### `loadorder.txt` — copiar EXACTO (24 plugins, orden canónico VNV):

```
# This file was automatically generated by Mod Organizer.
FalloutNV.esm
DeadMoney.esm
HonestHearts.esm
OldWorldBlues.esm
LonesomeRoad.esm
GunRunnersArsenal.esm
ClassicPack.esm
MercenaryPack.esm
TribalPack.esm
CaravanPack.esm
YUP - Base Game + All DLC.esm
Unofficial Patch NVSE Plus.esp
NVMIM.esp
NVMIM - YUP Patch.esp
FNV FaceGen Fix.esp
Strip Lights Region Fix.esm
Landscape Disposition Fix.esm
Landscape Texture Improvements.esm
Landscape Texture Improvements - YUP Patch.esm
fixy crap ue.esp
Placement Fixes.esm
d20Fixes.esm
JustAssortedMods.esp
```

### `plugins.txt` — copiar (los 23 activos):

```
# This file was automatically generated by Mod Organizer.
FalloutNV.esm
DeadMoney.esm
HonestHearts.esm
OldWorldBlues.esm
LonesomeRoad.esm
GunRunnersArsenal.esm
ClassicPack.esm
MercenaryPack.esm
TribalPack.esm
CaravanPack.esm
YUP - Base Game + All DLC.esm
Unofficial Patch NVSE Plus.esp
NVMIM.esp
NVMIM - YUP Patch.esp
FNV FaceGen Fix.esp
Strip Lights Region Fix.esm
Landscape Disposition Fix.esm
Landscape Texture Improvements.esm
Landscape Texture Improvements - YUP Patch.esm
fixy crap ue.esp
Placement Fixes.esm
d20Fixes.esm
JustAssortedMods.esp
```

### `modlist.txt` — copiar (orden de prioridad, "+" activo / "-" desactivado):

```
# This file was automatically generated by Mod Organizer.
+Bug Fixes_separator
+Supplementary Fixes And Tweaks (YUPDate)
+Third Person Aim Fix NVSE
+Vanilla Plus Terrain
+LOD Flicker Fix - NVSE
+Vanilla Placement Fixes
+Blood Decal Flashing Fix
+Items Transformed - Enhanced Meshes (ITEM)
+3rd Person Animation Fixpack
+VATS Lag Fix
+Viewmodel Shading Fix - NVSE
+Viewmodel Shake Fix - NVSE
+LOD Fixes and Improvements - NVSE
+Meshes and Collision - Totally Enhanced Nifs (MAC-TEN)
+Landscape Texture Improvements (FNV - TTW)
+skinned mesh improvement mod - redone redux remake retry revengeance retopology refridgerator
+Iron Sights Aligned
+PipBoyOn Node Fixes
+Muzzle Flash Light Fix - NVSE
+Depth of Field Fix - NVSE
+lStewieAl's Engine Optimizations
+ActorCause Save Bloat Fix
+External Emittance Fix - NVSE
+Fallout Alpha Rendering Tweaks - NVSE
+Climate Control NVSE
+Misc Audio Tweaks and Fixes
+New Vegas Mesh Improvement Mod - NVMIM
+Landscape Disposition Fix
+Strip Lights Region Fix
+Combat Lag Fix (NVSE)
+Mostly Fixed FaceGen Tints (NV or TTW)
+Unofficial Patch NVSE Plus
+lStewieAl's Tweaks and Engine Fixes
+Yukichigai Unofficial Patch - YUP
+Utilities_separator
+Just Assorted Mods
-Ultimate Edition ESM Fixes Remastered
+Shader Loader - NVSE
+JohnnyGuitar NVSE - INI Presets
+No Exit to Main Menu
+hNVSE
+Yvile's Crash Logger
-Epic Games Patcher
+Viva New Vegas Resources
+ISControl Enabler and Ironsights adjuster (now ESPless)
+ShowOff xNVSE Plugin
+kNVSE Animation Plugin
+Improved Console (NVSE)
+FNV Mod Limit Fix
-New Vegas Script Extender (NVSE xNVSE)
+JohnnyGuitar NVSE
+NVTF - New Vegas Tick Fix
+Console Paste Support
-FNV BSA Decompressor
-FNV 4GB Patcher
+JIP LN NVSE Plugin
+UIO - User Interface Organizer
+Fixed ESMs
*DLC: CaravanPack
*DLC: ClassicPack
*DLC: DeadMoney
*DLC: GunRunnersArsenal
*DLC: HonestHearts
*DLC: LonesomeRoad
*DLC: MercenaryPack
*DLC: OldWorldBlues
*DLC: TribalPack
```

> Si tu MO2 ya creó el perfil, reemplaza estos 3 archivos. Luego **no** uses el "Sort" de LOOT:
> el orden ya es el canónico (LOOT pondría `Unofficial Patch NVSE Plus.esp` antes de YUP — no).

---

## 4 · INIs — tweaks obligatorios

### `FalloutCustom.ini` (lo carga JIP LN NVSE automáticamente)
Guardar en `profiles/Default/FalloutCustom.ini` (MO2 lo sirve al juego por VFS):

```ini
; Value types (prefixes):
; i = integer (whole number)
; f = float (decimal number)
; s = string (text)
; b = boolean (0 = Off, 1 = On)

[Audio]
; Enables additional worker thread for minor performance improvement
bMultiThreadAudio=1

; Disables unnecessary copy operations performed on sound data
bUseAudioDebugInformation=0

; Increase audio file cache size to reduce loading stutter
iAudioCacheSize=16384
iMaxSizeForCachedSound=2048

[BackgroundLoad]
; Forces cell unload on fast travel to lessen memory usage
bSelectivePurgeUnusedOnFastTravel=1

; Reduces stutter when loading multiple NPCs
bBackgroundLoadLipFiles=1

[Controls]
; Disables mouse acceleration in menus
; Game does not have mouse acceleration for the camera
fForegroundMouseAccelBase=0
fForegroundMouseAccelTop=0
fForegroundMouseBase=0
fForegroundMouseMult=0

[Display]
; Enables Fullscreen mode for the best performance in D3D9
; Refer to the Performance Guide for more info
bFull Screen=1

; Use this for V-Sync control (the Launcher setting doesn't work)
; 0 = Off, 1 = On, Higher values toggle fractional V-Sync (not recommended, very laggy and disables Variable Refresh Rate)
iPresentInterval=1

; Forces highest texture quality so textures won't break if you had it set to anything lower
iTexMipMapSkip=0

; Disables actor shadows due to their low visual impact and high performance cost
bDrawShadows=0
iActorShadowCountInt=0
```
(archivo completo incluido en este repo: `files/FalloutCustom.ini`)

### `SArchiveList` — las 21 BSAs en UNA línea (en `Fallout.ini`, sección `[Archive]`)

```ini
SArchiveList=Fallout - Textures.bsa, Fallout - Textures2.bsa, Fallout - Meshes.bsa, Fallout - Voices1.bsa, Fallout - Sound.bsa, Fallout - Misc.bsa, DeadMoney - Main.bsa, DeadMoney - Sounds.bsa, HonestHearts - Main.bsa, HonestHearts - Sounds.bsa, OldWorldBlues - Main.bsa, OldWorldBlues - Sounds.bsa, LonesomeRoad - Main.bsa, LonesomeRoad - Sounds.bsa, GunRunnersArsenal - Main.bsa, GunRunnersArsenal - Sounds.bsa, ClassicPack - Main.bsa, CaravanPack - Main.bsa, MercenaryPack - Main.bsa, TribalPack - Main.bsa, Update.bsa
```

> Sin esto, las BSAs de los DLC no se registran → mallas/texturas faltantes (triángulos rojos).
> `Update.bsa` al FINAL = máxima prioridad (requisito VNV).

---

## 5 · Arrancar

1. MO2 → perfil **Default** → todo en verde.
2. Botón ▶ **Run** → **FalloutNV** (con `nvse_steam_loader.dll` arranca el NVSE solo).
3. Nuevo juego → Settings: **Stewie Tweaks presente** = mods cargados ✓.

### Diagnóstico rápido
| Síntoma | Causa | Fix |
|---|---|---|
| Triángulos rojos / perks rosas | SArchiveList incompleto o BSA descomprimida | Paso 4 (21 BSAs, una línea) |
| Crash al arrancar (File not found) | Meshes.bsa descomprimida o Fixed ESMs mal | Steam validate + NO BSA Decompressor |
| Crash diálogos (0x00AA991C) | Fixed ESMs no activos / de otra versión | Paso 2C: `+Fixed ESMs` |
| "Game not found" en MO2 | FNV nunca ejecutado | Ejecutar FNV 1 vez, configurar ruta |
