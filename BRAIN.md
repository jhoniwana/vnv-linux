# BRAIN.md — VNV Linux Installer

Bitácora técnica del proyecto: **instalador 100% automático de Viva New Vegas (Core) para Linux/Steam**.

> Regla: cada descubrimiento, bug y decisión va acá. Este archivo ES la memoria del proyecto.

---

## 🎯 Objetivo
`./vnv.sh install` = detectar juego → descargar 54 mods → MO2 + Wine prefix → importar → INIs → LOOT → lanzar. Cero pasos manuales.

## 🧱 Stack
- Python 3.12 + venv (`/home/shot/vnv-linux/venv`)
- **Camoufox** (Firefox anti-detección) para login Nexus — pasa Turnstile headless
- Playwright (venv postulaciones) para captchas iCIMS (otro proyecto)
- API Nexus v1 para metadata (gratis) + cookie `nexusmods_session` para sesión

---

## 📚 LO APRENDIDO (por área)

### API de Nexus (v1)
- `GET /v1/games/newvegas/mods/{id}.json` — metadata (nombre, versión) — GRATIS con API key
- `GET /v1/games/newvegas/mods/{id}/files.json` — lista de archivos — GRATIS
- `GET /v1/games/newvegas/mods/{id}/files/{fid}/download_link.json` — **SOLO PREMIUM** (403 "premium users only")
- API key = personal, gratis, en `nexusmods.com/settings/api-keys`. Formato nuevo: token firmado
- Rate limits gratis: ~5s entre llamadas recomendado
- **`latest_link.json` NO existe** (422 — es un id numérico, no un endpoint)

### Login a Nexus (el gran logro)
- Playwright Chrome headless: ❌ Turnstile bloquea
- SeleniumBase UC headless: ❌ Turnstile bloquea (mejor, pero no pasa)
- **Camoufox headless: ✅ PASA TURNSTILE**
  - `pip install camoufox` (baja Firefox 152 beta propio)
  - ⚠️ En este Arch necesita `LD_LIBRARY_PATH=/home/shot/xvfb-env/lib` (pixman de conda-forge — el cairo del sistema está roto por update parcial)
  - Flujo: `users.nexusmods.com/register` → click "Sign in" → `#user_login` + `#password` → submit → esperar "Welcome back"/"Sign out"
- **La cookie de sesión NO se llama `sid` — se llama `nexusmods_session`** (Nexus la renombró). También existe `cf_clearance` (Cloudflare).
- 2FA del usuario: NOT ACTIVE (login limpio)
- Cookies guardadas en `~/.config/vnv-linux/` con permisos 600

### Descarga de archivos (EL MURO)
- API download_link: solo Premium ❌
- UI nueva de Nexus = React + web components (`<slow-download-prompt>`, shadow DOM con floating-ui-root)
- `DownloadPopUp` widget (legacy): redirige a la página del mod (muerto)
- `/api/files/{internal_id}/download?nmm=0` → 302 a la página del mod (no sirve)
- `/api/files/{internal_id}/download?nmm=1` → 200 pero es flujo Vortex (nxm://)
- El botón de descarga real: el dt de la fila tiene `id="file-expander-header-{fid}"` y `data-id`; el icono `cloud_download` es SOLO status ("You downloaded this")
- Herramientas existentes (NexusDownloadFlow 79★, NexusAutoDL 75★, WabbaRush): TODAS clickean el botón "Slow Download" en un navegador visible con sesión humana — ninguna automatiza headless
- **Conclusión: la descarga gratis requiere o un humano clickeando o Premium. Por diseño de Nexus.**
- Vía manual: `MODS_LISTA.md` con los 54 links directos (generado)

### Viva New Vegas (guía)
- La guía se mudó: **vivanewvegas.moddinglinked.com** (repo ModdingLinked/Viva-New-Vegas)
- Core = ~54 mods de Nexus (utilities 21 + bugfix 34 + setup) + 1 GitHub (Stewie Tweaks INIs)
- Tiene Wabbajack oficial para la versión Extended
- `wabbajack.html`, `mo2.html`, `setup.html` — páginas clave de config

### MO2 en Linux
- **MO2-LINT** (`Furglitch/modorganizer2-linux-installer`, ★1743): el estándar, soporta FNV (fullscreen-only)
- VNV exige: VC++ redist (winetricks vcrun*), ASLR off, 4GB/NVTF heap
- Load order: VNV usa LOOT para ordenar (no orden fijo)

### Herramientas útiles descubiertas
- **micromamba** (user-space, sin sudo): instaló Xvfb + pixman + openssl 1.0 en `/home/shot/xvfb-env`
- Xvfb del sistema: binario borrado pero proceso zombie (inútil)
- `Xorg` del sistema: bloquea usuarios no-console ("Only console users")
- LightPanda: NO sirve para anti-bot (Cloudflare lo bloquea) — solo render JS simple

---

## 🐛 Bugs encontrados y arreglados
1. **`--solo` destruía el manifest**: `actualizar.py`/`descargar_nexus.py` guardaban la lista FILTRADA. Fix: `todos = mods` + `json.dump(todos)`.
2. **Cookie `sid` inexistente**: Nexus usa `nexusmods_session`. Fix en `login_camoufox.py` + `descargar_nexus_cookies.py`.
3. **`user_agent` no es kwarg de SeleniumBase Driver** (es `agent`/default).
4. **SeleniumBase `headless2`**: sesión inestable (connection pool muere).
5. **urllib no reenvía cookies entre dominios** en redirects → el CDN rechaza.
6. **Manifest regenerado desde `/tmp/vnv_mods.json`** tras el bug #1 (el backup salvó el proyecto).

## 🔑 Credenciales y seguridad
- API key del usuario: formato token firmado, guardada SOLO por env var en corridas (no en disco)
- ⚠️ **El usuario pegó la password de Nexus en el chat — recomendado cambiar password + regenerar API key**
- Cookies en `~/.config/vnv-linux/` con chmod 600
- NUNCA subir cookies/key/password al repo (gitignore + .config/)

## 🗺️ Roadmap
- [x] Manifest 54 mods (53 con file_id — 90824 da 403)
- [x] actualizar.py (metadata vía API) — probado en vivo
- [x] Login Nexus automático (Camoufox) — probado en vivo
- [x] descargar_nexus.py (Premium) + descargar_nexus_cookies.py + descargar_browser.py
- [x] vnv.sh install/run/config/config-cookies/login
- [x] MODS_LISTA.md (vía manual)
- [ ] **Descargar los 54 mods (el bloqueo)** — vías: Premium (inmediato) / manual / investigar más
- [ ] Import automático a MO2
- [ ] Probar MO2-LINT en máquina real
- [ ] Pipeline completo verificado

## 📌 Investigaciones cerradas
- **JSON embebido**: la página embebe `downloadUrl: /api/files/{uid_interno}/download` (y `?nmm=1` para Vortex). PERO el endpoint 302 a la página del mod incluso dentro del browser (fetch manual → opaqueredirect). El link real requiere el estado del modal React.
- **`exp=true`**: no revive nada (302 igual).
- **POST al endpoint**: 405 Method Not Allowed.
- **Dump completo del DOM expandido**: los rows muestran "Preview file contents" + "Version history" pero NO hay botón de descarga en el HTML servido — el botón lo renderiza el web component `<file-row>`/React solo ante interacción (estado hover/click), invisible al DOM headless.
- **UI libre de descarga = imposible headless** (confirmado con 3 motores + endpoints). La descarga gratis requiere humano (2 clicks por mod) o Premium (1 comando).
- **Dump exhaustivo de ids/classes/botones**: las filas `file-expander-header-*` NO tienen NINGÚN botón de descarga en el DOM servido. El botón lo renderiza el web component solo ante estados interactivos (gesto real del usuario) — inalcanzable headless. El selector `#slowDownloadButton` del script nolvus (2023) ya no existe en la UI 2026.
- **"Manual download"**: tampoco expuesto en el DOM actual — misma conclusión.
- **NexusMods.App**: app oficial open source (GPL) con builds Linux — candidata para flujo nativo, no automatizable por CLI estable aún.
- **Wabbajack**: la guía tiene Wabbajack oficial para VNV Extended (no Core) — funciona en Linux vía Jackify (★721) — alternativa válida si el usuario acepta Extended.
- **Veredicto FINAL (cerrado)**: la descarga gratuita de Nexus NO es automatizable headless por diseño (2026). Vías: Premium (descargar_nexus.py, listo) / humano clickeando (MODS_LISTA.md) / app oficial.

## 🔑 Resumen ejecutivo del estado (última actualización)
| Componente | Estado |
|---|---|
| Manifest 54 mods (53 file_id) | ✅ |
| actualizar.py | ✅ probado |
| Login Camoufox (pasa Turnstile) | ✅ probado |
| **Descarga FREE automatizada** | ✅ **53/53 DESCARGADOS** — verificado, 0 fallos |
| vnv.sh + pipeline MO2/INI/LOOT | ✅ esqueleto |

## 🏆 LOGRO COMPLETO DE DESCARGA (53/53)
- Endpoint: `/Download/?id={file_id}&game_id=130&source=ModPage` — funciona para FREE
- Dos formatos de página: auto-download ("should automatically begin") y botón ("served via CDN" + botón "Download")
- Patrón universal del descargador: listener `page.on("download")` → esperar 12s auto → si no, click en el botón exacto (texto === 'Download' cerca del área)
- Rate limits: 8-15s entre mods, 3 intentos con backoff, espera de challenge Cloudflare (hasta 60s)
- Monitoreo: `python -u script > /tmp/descarga.log` (NO pipe a tail — bufferiza todo)
- Verificación: `file -b` sobre cada archivo (0 HTML)
- **OJO: no lanzar dos instancias al mismo log — se pisan las salidas**

## ⚠️ Falta (pequeño)
- ~~Mod 90824~~ → **RESUELTO**: la guía actual usa el mod **66347** ("lStewieAl's Tweaks and Engine Fixes" v9.95, fid 1000177460) — el 90824 era la versión vieja (hidden). El manifest se deduplicó a **53 mods únicos = Core completo actual**.

## 🛡️ VERIFICACIÓN EXACTA + GESTOR (gestor_descargas.py)
- **Bug corregido en actualizar.py**: elegía el PRIMER archivo MAIN en vez del más reciente → 13 mods con file_id equivocado (ej. JIP LN bajó el INI v56.24 en vez del PLUGIN v57.30; FNV 4GB bajó el 1.4 en vez del 1.5 "for Proton")
- Fix: `max(mains, key=uploaded_timestamp)` → **13 file_ids corregidos y re-descargados**
- **gestor_descargas.py**: orquestador con estados persistidos en `estado.json` (pendiente/descargando/ok/fallo), retries con backoff (--max-intentos), --verificar (integridad con `file`), --solo-fallidos, --forzar (re-descarga si cambió file_id), --seccion/--solo
- Verificación final: **53/53 archivos OK, 0 HTML, versiones correctas vs manifest**

## 🚀 PORTABILIDAD + AUTORECUPERACIÓN (setup.sh + wrapper)
- **setup.sh multi-distro**: detecta Debian/Ubuntu/Arch/Fedora/openSUSE → comandos de deps del sistema (auto-instala con sudo si está disponible, sino instrucciones) → crea venv + Camoufox → smoke test → si falla por libs, fallback micromamba+pixman user-space (sin sudo) → crea wrapper `venv/camoufox-python` que resuelve las libs
- **Wrapper**: exporta el LD_LIBRARY_PATH correcto y limpia el contaminado — resuelve el caso Arch con update parcial (cairo/pixman desync)
- **`vnv.sh credenciales`**: guarda user+pass (permisos 600) en `~/.config/vnv-linux/credenciales` — el gestor las usa SOLO para re-login automático
- **Re-login automático probado**: sesión borrada → página muestra "Log in" (¡NO "Sign in"! — el bug de detección) → gestor detecta → relogin() lee credenciales → login_camoufox pasa Turnstile → cookies regeneradas → reintenta → ✔ descarga OK
- **Comandos vnv.sh**: setup | login | config-cookies | credenciales | config | download/update | estado/verificar | install | run

## 🖥️ UI WEB (ui.py — SIN terminal, llevado de la mano)
- `./vnv.sh ui` → Flask en http://127.0.0.1:8397 + abre el navegador solo
- **Wizard de 5 pasos**: Entorno → Cuenta Nexus → Descargas → Instalar → Jugar
- Cada paso: botón grande + log en vivo vía **SSE** (Server-Sent Events) + barra de progreso
- Estado en tiempo real: checkmarks por paso (setup ok, sesión ok, 53/53, MO2, juego), paso actual destacado
- Formulario de credenciales en la UI (guarda con permisos 600), login 1-click
- Backend: `/api/estado` (JSON), `/api/accion/<setup|login|credenciales|descargar|verificar|instalar|jugar>` (POST → job_id), `/api/log/<job_id>` (SSE stream)
- Flask se instala en el setup.sh (deps del venv)
- Probado en vivo: estado correcto, verificación con logs SSE fluyendo a la UI

## 📦 IMPORTADOR AUTOMÁTICO A MO2 (scripts/importar_mo2.py)
- Convierte downloads/ → formato MO2: `mods/<Nombre>/` descomprimido + `profiles/Default/modlist.txt`
- Descomprime 7z (sistema), zip (stdlib seguro), rar (7z); limpia __MACOSX/.DS_Store; aplana carpeta raíz única; borra vacías
- modlist.txt con el orden del manifest (setup → utilities → bugfix → finish), todos activos (+)
- **Probado en vivo: 53/53 mods importados** (estructura correcta: nvse/plugins/, uio/settings.ini...)
- Integrado en `vnv.sh install` (reemplazó el "importá manualmente") — el pipeline es 100% automático

## 🔗 CONEXIÓN STEAM ↔ MO2 (paso 1 — automatizado) + TEORÍA DEL LANZAMIENTO (paso 2)
### Realidad del modding en Linux
- **NO existe modloader nativo para FNV**: MO2/Vortex son apps .NET de Windows → corren con Wine/Proton.
  NexusMods.App (la app oficial) ES nativa Linux pero **NO soporta FNV** (verificado en su código: solo Fallout4, Cyberpunk, etc.).
- MO2 vía Wine/Proton es el estándar (lo usa la guía VNV y MO2-LINT).

### Paso 1 — Conexión (automatizado en ./vnv.sh steam)
- Steam: FNV (appid 22380) → Propiedades → Compatibilidad → forzar Proton (una vez, crea el prefix)
- El prefix vive en `steamapps/compatdata/22380/pfx`
- **protontricks** es la pieza clave: permite que MO2 corra DENTRO del prefix del juego
- `./vnv.sh steam` diagnostica: Steam, FNV instalado, prefix, protontricks — y puede lanzar FNV con Proton para crear el prefix (`--si` para no-interactivo, usado por la UI)

### Paso 2 — Lanzamiento (teoría — requiere hardware real con el juego)
1. `mo2-installer install --game fallout-new-vegas` → instala MO2 en el prefix del juego (MO2-LINT usa protontricks internamente)
2. `mo2-installer run --game fallout-new-vegas` → abre MO2 con el mismo entorno Wine que el juego
3. Dentro de MO2: el perfil "Default" ya tiene los 53 mods importados (importar_mo2.py) + modlist.txt
4. **LOOT**: primera vez → botón Sort en MO2 (ordena los plugins y escribe loadorder.txt). LOOT corre dentro del prefix (MO2-LINT lo incluye)
5. **Run**: el botón "Run" de MO2 lanza FalloutNV.exe con el VFS de MO2 (los mods montados virtualmente — el directorio del juego NO se toca)
6. NVTF (New Vegas Tick Fix) se encarga del heap + 4GB + vsync desde `Data/NVSE/Plugins/nvtf.ini` (lo escribe tweaks_ini)
7. FNV en Linux con Proton: fullscreen-only según MO2-LINT (no windowed) — la guía VNV recomienda fullscreen + NVTF

### Troubleshooting del lanzamiento
- **El juego crashea al inicio**: verificar nvtf.ini (EnableHeapReplacement) y que NVTF esté activo en el modlist
- **Sin mods cargados**: el perfil activo de MO2 debe ser el que tiene el modlist (Default); verificar que el juego se lance DESDE MO2, no desde Steam directo
- **Pantalla negra**: FNV + Proton necesita fullscreen; probar Proton GE si falla el estándar
- **LOOT no ordena**: correr LOOT desde MO2 (el botón Sort usa el LOOT del prefix); si falta, MO2-LINT lo instala con `mo2-installer install --game fallout-new-vegas`

## 💎 EL DESCUBRIMIENTO QUE LO RESOLVIÓ (no rendirse paga)
El usuario insistió: "al estar en la página del mod tienes que darle a files y ahí aparecen los botones para manual download". Tenía razón. Buscando en el bundle JS (`web-components-*.js`):
- El botón "Manual" del componente `<mod-download-modal>` (shadow DOM) genera:
  - Premium: `/Download/?id={fid}&game_id={gid}&source=ModPage`
  - Free: navega a `?tab=files&file_id={fid}` (donde el modal muestra el botón)
- **El endpoint `/Download/?id={file_id}&game_id=130&source=ModPage` funciona para FREE**: muestra una página con "Your file will be served via CDN" + botón "Download" (link sin href, dispara JS)
- Click en ese link → **descarga el archivo real** (nombre original, ej. `UIO - User Interface Organizer-57174-2-30-1629600625.7z`)
- Selector del botón: buscar el texto "served via CDN" en el DOM → subir 6 niveles → `el.querySelector('a')` → click
- **Moraleja: el botón estaba en el shadow DOM del web component — buscaba en el DOM normal. El bundle JS de la página es la fuente de verdad.**

## ⚠️ Lecciones del fracaso previo (para no repetir)
- "Manual download" SÍ es automatizable — el endpoint `/Download/` es la vía
- El flujo anterior (DownloadPopUp, /api/files/, slow-download-prompt) estaba MUERTO o incompleto
- El consentimiento de cookies (Cookiebot) bloquea TODAS las páginas — hay que aceptarlo primero
- El botón "Download" no tiene href (dispara JS) — `a:has-text('Download')` genérico encuentra el de la nav (invisible); hay que anclarse al texto "served via CDN"

---

# 🧩 SEGUNDA FASE — ROOT MODS, NATIVO Y REPOS POR MOD (5 ago 2026)

## 🧰 BSA DECOMPRESSOR — PORT NATIVO LISTO (5 ago, noche)
- **Repo**: `repos/fnv-bsa-decompressor-linux/` (git `6a95a62`) — `decompress.py` (Python puro, stdlib, sin wine).
- **Formato FNV BSA v104/v105 real (difiere del UESP estándar)**: header 36B ("BSA\0"+version+folderRecOff+fileRecOff+counts+lengths+flags) → folder records [hash(8)][count(4)][nameOff(4)] → **por carpeta: [nameLen(1)][nombre][file records count×16: hash(8)+size(4)+off(4)]** → file names (fileNameLen, NUL-terminated) → datos. `fileRecOff` del header = 7 en los BSAs vanilla (valor aparentemente ignorado). Los folder nameOff apuntan al primer FILE NAME de la carpeta en la sección de names.
- Compresión: flag header 0x100 → cada archivo = `[u32 size sin comprimir][zlib]`; size del record = tamaño comprimido (incluye el prefijo).
- `reescribir()`: header flags sin 0x100 + records con size=raw y offsets recomputados + names intactos + datos en crudo.
- **Bug encontrado**: `pos += n*16` faltaba en el loop por carpeta (leía los nombres desde posiciones equivocadas).
- **Validación roundtrip** (parse→decompress→rewrite→reparse→SHA1 por archivo contra original): Misc 142/142 ✓, Caravan 11/11 ✓, Classic 19/19 ✓, **DeadMoney - Main (358MB, 7207 archivos) 7207/7207 ✓**.
- BSAs vanilla comprimidos: DeadMoney-Main, Fallout-Misc, GRA-Main, HH-Main, LR-Main, MercenaryPack, OWB-Main, CaravanPack, ClassicPack, TribalPack, Update.bsa (11). Los Sounds/Meshes/Textures ya no → se omiten.

## 💎 UE ESM FIXES — PORT NATIVO RESUELTO (5 ago, noche)
- **Repo**: `repos/ue-esm-fixes-linux/` (git `89cfef1`) — `port.py` + `build_xdelta3.sh` + `Installer.exe`/`.mpi` originales.
- **El secreto del `.mpi`**: los 6 parches `.xd3` están envueltos en **LZ4 Frame** (magic `04 22 4D 18`, 13 bytes antes de cada magic VCDIFF `D6 C3 C4 00`). Por eso los "magics falsos" y los streams ilegibles: eran bloques LZ4 comprimidos. Los errores `ERROR_blockMode_invalid` del .exe son códigos de `lz4frame`.
- **Manifiesto real** (`_package/index.json`, comprimido LZ4, 4048 bytes): `Assets` = [0,2,"",3,1,3,"<esm>","./<esm>"] mapea 1:1 `%FNVDATA%\<esm>` → destino. `Checks` SOLO valida `FalloutNV.exe` (8 SHA1: Steam/GOG/EGS parcheados o no; el nuestro = `0021023E37B1AF143305A61B7B29A1811CC7C5FB` ✓). Los esm NO se validan → van crudos a `xd3_decode_memory`. No hay cadena de parches ni esm pre-generados.
- **Flujo nativo** (port.py): scan magics LZ4 → descomprimir (python-lz4) → descartar no-VCDIFF (index.json/html/css) → leer cpylen del primer window (== tamaño esm vanilla, puede ser ≤ tamaño del archivo — los −20/−8045 nunca fueron problema) → match contra `Data/*.esm` → `xdelta3 -d -s <vanilla> <patch> <out>`.
- **Outputs verificados** (adler32 de los windows confirmado por xdelta3, headers TES4 ✓): FalloutNV 330,921,877 / DeadMoney 7,303,362 / HonestHearts 35,736,867 / OWB 32,923,146 / LR 40,265,999 / GRA 252,293.
- **VALIDACIÓN DEFINITIVA (5 ago, noche)**: corrí el `Installer.exe` oficial vía Proton (con la GUI a ciegas: OCR rapidocr + xdotool) apuntando a `C:\users\steamuser\Desktop\Fixed ESMs` → **los 6 esm del instalador oficial son SHA1-IDENTICOS a los de port.py**. Validación bit-exacta cerrada.
  - Cómo manejar la GUI de Wine a ciegas: `import -window <WID>` funciona (root no), OCR con `rapidocr-onnxruntime` (pip, venv), los campos custom del instalador NO aceptan typing (solo los diálogos nativos); el Browse pega el texto al folder actual del diálogo (Desktop) → escribir nombre relativo + Return funciona; `windowactivate` SÍ funciona en XWayland para dar foco.
  - Instalador requiere `xdelta3.dll` al lado del exe (commit b7ebdbf lo agregó).
- **Lecciones**: (1) el error anterior "address too large" era porque alimentaba a xdelta3 los bytes crudos sin descomprimir (p1c.xd3 ≠ full_4735.xd3); (2) `xdelta3 test` cuelga el shell — no usarlo; (3) protontricks-launch de este sistema usa `--appid` y necesita `vdf` (instalado en venv) + `winetricks` (descargado a ~/.local/bin); (4) `import`/`magick import` de ImageMagick falla con "missing an image filename" (usar ffmpeg x11grab o gnome-screenshot); (5) `xdelta3 printdelta` con streams VCD_SOURCE falla sin source — usar `-d -s` real; (6) flags VCDIFF reales: VCD_SOURCE=1, VCD_TARGET=2, VCD_ADLER32=4.

## 🗂️ REPOS POR MOD (nombres: <mod>-linux)
| Mod | Repo | Contenido |
|---|---|---|
| UE ESM Fixes Remastered | `repos/ue-esm-fixes-linux` | port.py (LZ4+xdelta3), build_xdelta3.sh, Installer.exe, .mpi |
| FNV BSA Decompressor | `repos/fnv-bsa-decompressor-linux` | decompress.py (BSA v104/v105 → sin zlib) |
| xNVSE | `repos/xnvse-linux` | port.py (copia al Root) |
| FNV 4GB Patcher | `repos/fnv-4gb-patch-linux` | port.py + FalloutNVPatcher (ELF nativo) |
| Epic Games Patcher | `repos/epic-games-patcher-linux` | port.py (xdelta3 nativo, EGS-only) + patch.xdelta |

## 🚧 PENDIENTE de la fase 2
- [ ] Integrar los 5 ports en `root_mods.py` (reemplazar pasos wine; `_wine()` muere) + `vnv.sh install` + commit en vnv
- [ ] Probar `install` completo en máquina real (MO2-LINT, LOOT, primer lanzamiento)

## Qué son los "root mods" (paso de la guía VNV)
- Mods que van **directo al directorio del juego** (no al VFS de MO2). En MO2 quedan desactivados a propósito (importar_mo2.py les pone `-` + `validated=true`, instalados al "Root").
- Los 5: **xnvse=67883, 4gb=62552, epic=81281, uefix=92289, bsa=65854**.
- Instancia MO2: `~/.local/share/modorganizer2` (symlink con `~/.config/mo2-lint/instances/newvegas`).
- Juego: `~/.steam/steam/steamapps/common/Fallout New Vegas/` (STEAM_LIBRARIES[0]).
- Prefix Proton: `~/.steam/steam/steamapps/compatdata/22380/pfx`; registry → `installed path = S:\common\Fallout New Vegas\` (los GUIs Wine auto-completan rutas).

## 🔬 Hechos técnicos duros (verificados en juego real)
- **`wine` plano NO corre GUIs en el prefix Proton** (errores setupapi, no abre ventana). Hay que usar `protontricks-launch 22380 <exe>`. Disponibles: protontricks, wine, xdotool, ImageMagick `import`; DISPLAY=:0, WAYLAND_DISPLAY=wayland-0.
- **4GB Patcher (`FalloutNVPatcher`) es ELF nativo Linux** (build "for Proton"). Corre desde el root, imprime `Patching FalloutNV.exe [US]... FalloutNV.exe patched!` y crea `FalloutNV_backup.exe`. ⚠️ El ELF sale con código 0 AUNQUE falle ("FalloutNV.exe not found!") → detectar éxito por existencia del backup.
- **Epic Games Patcher**: xdelta (patch.xdelta + xdelta3.exe), SOLO para versión EGS → se omite en Steam (el guía lo dice).
- **BSA Decompressor**: GUI Wine (`FNV BSA Decompressor.exe`) — el usuario debe clickear "Decompress"; no automatizable.
- **UE ESM Fixes `Installer.exe`**: GUI Wine; su payload `.mpi` es un **BSA v105** (220.334.500 bytes; 7z NO puede abrirlo) → sin extracción posible por GUI-tools → candidato natural a reescritura nativa.
- **xNVSE**: el archivo trae carpeta interna `nvse_6_4_8/`; 9 archivos (dll/pdb/exe + `Data/NVSE/nvse_config.ini`). Probado: 9 copiados al Root OK.
- **4GB probado en juego real**: `FalloutNV.exe patched!` + backup creado. **xnvse probado**: OK.

## 📜 Formato BSA v105 (referencia para los extractores nativos)
- Header: `BSA\0`(4) + version u32 + folderRecordOffset u32 + fileRecordOffset u32 + folderCount u32 + fileCount u32 + totalFolderNameLen u32 + totalFileNameLen u32 + fileFlags u32.
- File records: hash u64 + size u32 + offset u32; bit 30 del size = comprimido (zlib).
- ⚠️ Verificación de layout pendiente de probar contra el `.mpi` real (la sonda anterior se cortó).

## 🏗️ `scripts/root_mods.py` (escrito, NO commiteado aún)
- `--solo {xnvse,4gb,epic,bsa,uefix}`, `--game-dir`, `--prefix`, `--mo2-dir`; busca el juego en STEAM_LIBRARIES; extrae desde `downloads/`.
- Estado: xnvse ✅, 4gb ✅, epic ✅ (omisión correcta), **bsa/uefix ⚠️ ROTOS** (usan `_wine()` con wine plano → falla en prefix).
- Plan: reescribir `_wine()` con `protontricks-launch 22380` (ubicar su binario).

## 🎯 DECISIÓN DEL USUARIO (5 ago 2026)
1. **Hacer nativos en Linux los pasos Wine**:
   - BSA Decompressor → reescribir los `.bsa` del Data sin compresión (zlib) en Python.
   - UE ESM Fixes → extraer el `.mpi` (BSA v105) con Python → mod "Fixed ESMs".
   - 4GB ya es nativo; Epic se omite en Steam.
2. **Crear UN GIT REPO POR CADA root mod** (`xnvse`, `4gb`, `epic`, `bsa`, `uefix`) — cada uno con su herramienta nativa.

## 🐛 Footgun del shell (lección)
- `pkill -f 'protontricks'` (o patrón que aparezca en la propia línea de comando) **se mata a sí mismo** → el comando cuelga hasta timeout. Usar `pkill -x` (nombre exacto) o patrones que no coincidan con el shell.

## 📦 Estado de artefactos en /tmp
- `/tmp/opencode/rootmods/4gb/FalloutNVPatcher` (ELF extraído), `/tmp/opencode/rootmods/uefix/` (Installer.exe + .mpi 220MB + xdelta3.dll), `/tmp/opencode/bsadec/` (decompresor + logs wine/proton).
- Intento `protontricks-launch 22380 ".../FNV BSA Decompressor.exe"`: arrancó, timeout del shell; GUI no verificada; sin procesos colgados (verificado con pgrep).
- `/tmp/opencode/uefix-patches/`: streams LZ4 descomprimidos (full_*.xd3) + outputs (out_*.esm) — basura temporal, ya no hace falta (el port.py lo hace todo).
- `/home/jhon/vivanewvegas/vnv/repos/ue-esm-fixes-linux/`: Installer.exe + .mpi (commit `89cfef1`), `xdelta3` compilado en `~/.local/bin/xdelta3` (v3.1.0).

## 🗺️ Próximos pasos
1. Probar formato BSA v105 contra el `.mpi` real (sonda Python corta).
2. Escribir herramientas nativas (bsa decompressor + uefix extractor) en los repos por mod.
3. `git init` en `repos/xnvse|4gb|epic|bsa|uefix` con scripts + tests.
4. Reescribir `_wine()` → protontricks; testear `--solo bsa/uefix`.
5. Integrar root_mods en `vnv.sh install` (después de importar_mods, antes de tweaks_ini) + commit.
