# 🔁 HANDOFF — VNV Linux Installer

Mensaje para el agente que continúe este proyecto. Léelo completo antes de actuar.

---

## 1. QUÉ ES ESTO

**vnv-linux**: instalador 100% automático del Core de **Viva New Vegas** (53 mods de Fallout New Vegas) para **Linux + Steam**.

- Repo público: `https://github.com/jhoniwana/vnv-linux` (rama `main`)
- Código local: `/home/jhon/vivanewvegas/vnv/`
- Documentación completa: `BRAIN.md` (bitácora técnica) + `obsidian/` (bóveda de 17 docs con wikilinks)
- **El pipeline completo está construido, probado en vivo y el juego llega al menú con todos los mods.**

## 2. ESTADO ACTUAL (verificado en vivo, 6 ago 2026)

| Componente | Estado |
|---|---|
| 53 mods descargados + 4 extras (1.1 GB en `downloads/`) | ✅ auditoría completa: 53/53 main + 4/4 extras, 0 HTML |
| Login automático a Nexus (Camoufox pasa Turnstile) | ✅ probado |
| Gestor de descargas (estados, retries, re-login) | ✅ probado (auto-recuperación: sesión borrada → se recuperó solo) |
| Setup multi-distro (Debian/Ubuntu/Arch/Fedora/openSUSE) | ✅ probado en Arch/EndeavourOS |
| UI web (`./vnv.sh ui` — wizard 6 pasos, sin terminal) | ✅ probado (SSE en vivo) |
| Importador automático a MO2 | ✅ **re-import e2e**: 53/53, modlist 55 líneas, loadorder 21 plugins en orden de guía |
| Root mods (xNVSE, 4GB, EGS, BSA decompressor, UEM Fixes) | ✅ idempotente, re-corrido OK; LAA=0xA620, BSA descomprimidos, Fixed ESMs SHA1 OK |
| Tweaks de INI (nvtf.ini heap/4GB/VRAM + FalloutCustom.ini) | ✅ contenido exacto de la guía |
| `./vnv.sh estado` vs manifest | ✅ 53/53 OK, problemas 0 |
| LOOT (lootcli) | ✅ valida sobre copia no-destructiva (`./vnv.sh loot`) |
| **Lanzamiento real del juego** | ✅ **el juego llega al menú principal con los 53 mods + 27 plugins NVSE** |
| Comando `steam` (diagnóstico Proton appid 22380) | ✅ probado (protontricks-launch es el método de lanzamiento) |

### Bugs encontrados en la auditoría y sus fixes
- **MO2 2.5.2 trunca `plugins.txt` al apagar tras sesión de juego** (deja solo `FalloutNV.esm`; el `loadorder.txt` queda intacto). Reproducido 2 veces. **Fix**: `lanzar()` re-sincroniza `plugins.txt` desde `loadorder.txt` antes de cada launch (vnv.sh:214-226).
- **lootcli standalone no ve el VFS de MO2** → re-escribía `plugins.txt` con ~10 plugins. **Fix**: `./vnv.sh loot` valida sobre una copia en `/tmp/opencode/loot_plugins.txt` (no-destructivo) y se sacó LOOT del `install` (vnv.sh:172-192).
- **CRASH "error de Tale of Two Wastelands" al lanzar el juego (CAUSA RAIZ)**: `actualizar.py` elige el MAIN más reciente del mod 90593 "Vanilla Placement Fixes", que resultó ser la versión **TTW** (`Placement Fixes TTW`, file_id `1000152141`, v1.8) → `Placement Fixes.esm` requería `TaleOfTwoWastelands.esm` y el juego crasheaba al inicio. **Fix**: file_id corregido a `1000152138` (`Placement Fixes` vanilla v1.8), re-descargado (`Placement Fixes-90593-1-8-1747772681.7z`), re-importado, masters verificados (`FalloutNV/HonestHearts/OldWorldBlues/LonesomeRoad.esm` — sin TTW). Para detectar estos casos: escanear masters de plugins con `TES4` + size u32 en 0x04 y subrecords con tamaño **u16** (`<4sH`), buscando `MAST`.
- **`plugins.txt` MO2 2.5.2 SIN `*`**: el archivo = lista de plugins ACTIVOS sin asterisco (CRLF, header). Con `*` MO2 no reconoce NINGÚN plugin (`Plugin not found: *FalloutNV.esm`). Aplicado en `importar_mo2.py` (~556) y `preparar_lanzamiento()` de vnv.sh; `correr_loot()` arma la copia LOOT con `*` desde `loadorder.txt`.
- **`--solo` de `importar_mo2.py` pisaba las listas del perfil** (modlist/loadorder/plugins quedaban con UN solo mod → MO2 trataba los demás como nuevos → los desactivaba → juego "sin mods"). **Fix**: las listas se regeneran SIEMPRE con el manifest completo; `--solo` solo (re)extrae ese mod.
- **JIP LN NVSE nunca cargó**: `estado.json` de 58277 apuntaba al archivo INI (`JIP LN Settings INI-...`) en vez del main (`JIP LN NVSE Plugin-58277-57-30-...7z`) → faltaba `jip_nvse.dll`. Fix en estado.json + re-import.
- **INI de LOD Fixes faltante**: extra 84171:1000150631 apuntaba al main → `LOD Fixes.ini` nunca se instaló. Fix en estado.json + re-import.
- **Fixed ESMs CORRUPTOS (crash al inicio, ACCESS VIOLATION en "[FNV] LoadingMenu")**: los parches xdelta3 del `.mpi` de UE ESM Fixes se aplicaron contra esms que difieren del vanilla oficial (DeadMoney ±20B, FalloutNV ±8KB — el Data del juego resultó ser vanilla legítimo según verify de Steam; los parches del .mpi apuntan a otra versión vanilla) → xdelta3 produce esms con cabecera TES4 válida pero records faltantes (`00115C5F`, `00094EB8` ausentes) → diálogos DLC referencian forms inexistentes → crash. **Fix actual**: mod "Fixed ESMs" desactivado, se usan los esms vanilla (juego estable). **Pendiente**: investigar la fuente exacta de los parches (versión de los esms del .mpi) o reconstruir sin el .mpi.
- **SArchiveList sin BSAs de DLC** en los 3 inis (`Fallout.ini` del prefix + `FalloutPrefs.ini` + `Fallout_default.ini`): solo las 6 BSAs base → DLC sin contenido. **Fix**: 21 BSAs en orden vanilla (`Update.bsa` al final — mayor prioridad). No era la causa principal pero es correcto.
- **Errores de mallas/texturas (1145 → ~0)**: kf (`h2hattack`, `1hpaim`...), muros de Goodsprings (`NVGSRmWall01-03`...), 10mm Pre-Order, texturas de cuerpo (`00000007modbodyfemale`) — TODOS causados por la cadena de bugs de arriba (Fixed ESMs corruptos + JIP faltante + saves incompatibles). BSAs verificadas 100% correctas: las 11 comprimidas con bit30 en TODOS los records, data raw válida (nif `Gamebryo`/dds `DDS `).
- **Saves incompatibles**: las partidas (oct 2025 + autosave 22:06) se crearon con otra instalación/era de esms (formids reenumerados por los UE fixes) → al cargarlas: statics rotos ("!"), armas DLC rosadas, texturas de cuerpo con formid viejo. **Fix**: saves movidos a backup; **partida nueva = todo OK** (verificado por el usuario: texturas y contenido perfectos).
- **El juego AUTO-CARGA el último save** (nvse.log `DoLoadGameHook: autosave.fos` sin interacción) → al testear configuraciones hay que vaciar `Saves/` o el test carga la partida vieja.
- **Load order INCORRECTO (crash de diálogos al inicio, intermitente)**: YUP iba 8º en vez de 1º → las ediciones de YUP sobre diálogos (Doctors, OWB) ganaban sobre las de UPNVSE+ → condiciones con referencias rotas → ACCESS VIOLATION determinista (0x00AA991C, contexto TESTopicInfo 000377F6 "Last modified by YUP"). **Fix**: loadorder/plugins en orden canónico VNV Core (YUP 1º tras los esms base, Placement Fixes último) + GUIAS_PLUGINS del script alineado (fade38a).
- **`importar_mo2.py` re-activaba mods desactivados manualmente**: el modlist se regeneraba de cero y "Fixed ESMs" (carpeta existente) volvía a `+` → los esms corruptos recargados → crash. **Fix**: el script preserva el estado +/- del modlist previo (0ffc8ce).
- **"Some EDIDs are conflicting" (JGNVSE)**: benigno — conflictos de formids DLC vanilla (los UE fixes los corregirían) + duplicado conocido YUP/UPNVSE+ (`UPNVSEPVendorQuestItemSCRIPT`).

## 3. LO QUE FALTA (priorizado)

### 3.1 Principal — nada del pipeline. Solo queda pulido:
- **Rebuild de Fixed ESMs (opcional)**: los parches del `.mpi` (v1.03, jun 2026) no matchean los esms de este depot (±20B DeadMoney / ±8KB FalloutNV — el Data es vanilla legítimo según verify de Steam) → esms corruptos. Sin esto: los formids DLC quedan en conflicto (vanilla) → JGNVSE avisa "Some EDIDs are conflicting" (benigno, el juego corre bien). Investigar la versión de esms que usa el .mpi.
- **Sprint y "ver contenedores sin abrir"**: features de **JAM (Just Assorted Mods, mod 66666 v4.6)** — YA AGREGADO al manifest + importado + en loadorder (22 plugins). Config vía MCM en el juego (el Custom INI del Patch Emporium ya no existe online — el repo fue borrado; el extra queda registrado sin descargar).
- Probar `./vnv.sh setup` en una distro que no sea Arch (Debian/Ubuntu — sección 3.4)
- Social preview del repo (sección 3.2)
- Seguridad: regenerar credenciales (sección 3.5)

### 3.2 Repo — Social Preview (ícono al compartir)
GitHub NO permite avatar por repo. Para que el gecko oficial del juego aparezca al compartir el link:
1. Abrir `https://github.com/jhoniwana/vnv-linux/settings`
2. Sección **"Social preview"** → Edit
3. Subir `assets/gecko.png` (render oficial del Green Gecko de FNV, 512x512)
4. Set social preview

### 3.3 Opcional — Ícono permanente vía organización
Si se quiere el gecko como ícono fijo del repo (cambia la URL):
```
gh org create vnv-linux --public
gh repo transfer jhoniwana/vnv-linux vnv-linux --yes
```
Poner el gecko (`assets/gecko.png`) como avatar de la org.

### 3.4 Probar en Debian real
El setup multi-distro solo se probó en Arch. En una VM Debian/Ubuntu: `./vnv.sh setup` → debe detectar la distro, instalar deps con sudo, y el smoke test de Camoufox debe pasar (sin fallback micromamba si el sistema está sano).

### 3.5 Seguridad — regenerar credenciales (IMPORTANTE)
Las credenciales del usuario estuvieron expuestas en chats:
- **Cambiar la contraseña de Nexus** (users.nexusmods.com → Account settings)
- **Regenerar la API key** (nexusmods.com/settings/api-keys) y guardarla: `./vnv.sh config`
- Correr `./vnv.sh credenciales` (guarda email+pass con permisos 600 para el re-login automático)
- Las cookies de sesión (`nexus_session` + `cf_clearance` en `~/.config/vnv-linux/`) se regeneran con `./vnv.sh login`

### 3.6 Repos root privados + payload UE ESMs (IMPORTANTE)
- Los 5 root repos (`epic-games-patcher-linux`, `fnv-4gb-patch-linux`, `fnv-bsa-decompressor-linux`, `ue-esm-fixes-linux`, `xnvse-linux`) son **PRIVADOS** por decisión del usuario (contienen binarios/BSAs con copyright). No volverlos públicos.
- El `.mpi` de Ultimate Edition ESM Fixes (220 MB) **no está en el repo** (límite GitHub de 100 MB). `ue-esm-fixes-linux/port.py` lo extrae del `.7z` en `downloads/` con 7z a `~/.cache/vnv-uefix/`. Requisito: `7z` instalado.
- Los submods de los 5 root repos se instalan como repos git anidados (NO trackeados por el repo principal, `a1b8295`).

## 4. CÓMO FUNCIONA (lo esencial para no romper nada)

### Login y descargas (el gran logro)
- **Login**: `scripts/login_camoufox.py` — Camoufox (Firefox anti-detección) headless pasa el Turnstile de Cloudflare. Guarda `nexusmods_session` + `cf_clearance` en `~/.config/vnv-linux/` (600).
- **Descarga gratis**: la API `download_link` es solo Premium. El endpoint que funciona para FREE es:
  `https://www.nexusmods.com/Download/?id={file_id}&game_id=130&source=ModPage`
  - Con la cookie `nexusmods_session` muestra la página de descarga (auto-download o botón)
- **Gestor**: `scripts/gestor_descargas.py` — estados en `estado.json` (pendiente/descargando/ok/fallo), 3 retries con backoff, espera challenges Cloudflare, **re-login automático** si detecta "Log in" (no "Sign in") en la página.
- **Siempre usar el wrapper**: `./venv/camoufox-python` (python del venv con LD_LIBRARY_PATH correcto) — NUNCA `python3` directo para los scripts de Nexus.

### Instalación
- **MO2-LINT** (`mo2-installer`) instala MO2 en el prefix de Proton del juego vía protontricks (`mo2-lint install --unattended`)
- `scripts/importar_mo2.py` descomprime los 53 mods a `mods/<Nombre>/` + escribe `profiles/Default/modlist.txt` (root mods con `-`, Fixed ESMs con `+`)
- `scripts/root_mods.py` delega en los 5 root repos (xnvse/4gb/epic/bsa/uefix); **epic es no-op en Steam** (detecta LAA ya aplicado)
- `tweaks_ini` escribe `Data/NVSE/Plugins/nvtf.ini` (heap+4GB) + `profiles/Default/FalloutCustom.ini`
- El juego se lanza DESDE MO2: `ModOrganizer.exe --profile=Default run -e NVSE` (CLI MO2 2.5.2; `-e` es flag sin valor). `-e=NVSE` NO funciona.
- El load order viene en el orden de la guía (== LOOT); `./vnv.sh loot` lo valida sin tocarlo.

### Setup
- `setup.sh`: detecta distro → deps del sistema (con o sin sudo) → venv + Camoufox + Flask → smoke test → si las libs del sistema están rotas, fallback micromamba+pixman (sin sudo) → crea el wrapper

## 5. ADVERTENCIAS / REGLAS

- **NO subir credenciales** al repo (gitignore cubre `~/.config/`, venv/, downloads/ — verificar si se agregan archivos)
- **NO lanzar dos instancias del gestor al mismo log** (se pisan salidas) — usar `> /tmp/log 2>&1` con `python -u` y monitorear el archivo
- **Rate limits de Nexus**: ~5s entre llamadas API, 8-15s entre descargas (ritmo humano — no acelerar)
- **`actualizar.py`**: elegir SIEMPRE el MAIN más reciente (`max(uploaded_timestamp)`) — bug histórico de elegir el primero
- **Módulo 90824** estaba hidden; la guía usa el **66347** (lStewieAl's Tweaks) — ya corregido en el manifest
- Los mods NO se redistribuyen: se descargan con la sesión del usuario (legal)

## 6. REFERENCIAS RÁPIDAS

- `BRAIN.md` — TODO el detalle técnico, bugs y descubrimientos
- `obsidian/` — bóveda documental (Inicio.md es el hub)
- `README.md` — guía de usuario
- `scripts/gen_obsidian.py` — regenera la bóveda si cambia la doc
- Comandos: `./vnv.sh {ui|setup|login|config-cookies|credenciales|config|download|estado|install|loot|run}`
