# 🔁 HANDOFF — VNV Linux Installer (guía de automatización)

Mensaje para el agente que continúe este proyecto. Léelo completo antes de actuar.

---

## 1. QUÉ ES ESTO

**vnv-linux**: instalador 100% automático del Core de **Viva New Vegas** para **Linux + Steam**.
- 55 mods (Core VNV + JAM como extra solicitado), root mods nativos (sin Wine), lanzamiento vía MO2 CLI.
- Repo público: `https://github.com/jhoniwana/vnv-linux` (rama `main`)
- Código local: la carpeta donde se clonó el repo (portable — sin rutas absolutas)
- Docs: `BRAIN.md` (bitácora técnica) + `obsidian/` + este HANDOFF.

---

## 2. ESTADO ACTUAL — VERIFICADO AL 100% (7 ago 2026)

| Componente | Estado |
|---|---|
| **55 mods descargados** + 5 extras, 0 HTML | ✅ (incluye JAM 66666 + YUPDate/supplement 98514) |
| **55 mods importados** a MO2 | ✅ 50 activos + 5 root (desactivados, correcto) + Fixed ESMs activo |
| **Load order canónico VNV Core** | ✅ 23 plugins: base esms → YUP → d20Fixes → UPNVSE+ → NVMIM(-YUP) → FaceGen → Strip Lights → LDF → LTI(-YUP) → fixy → Placements → JAM |
| **Root mods** | ✅ xNVSE (nvse_1_4 + steam_loader), 4GB (LAA=0x20 + import), BSAs descomprimidas (21, bit30 en todos), UE ESM Fixes rebuild CORRECTO |
| **Fixed ESMs (rebuild 7 ago)** | ✅ **465.054 records, DIALOG 18.215, INFO 23.247** (la build vieja tenía 233K records y 0 diálogos → crash) |
| **INIs** | ✅ nvtf.ini (heap 400 + 4GB + VRAM, en juego y en mod), FalloutCustom.ini (perfil Default) |
| **Extras de la guía** | ✅ JIP Settings INI, Stewie INI, JohnnyGuitar INI Presets, LOD Fixes INI, **JAM - VNV Configuration** (JustMods.ini) |
| **Juego** | ✅ corre estable, 28 plugins NVSE cargados, partida nueva jugando sin errores visibles |
| **Log de errores** | ✅ 1.5 KB = solo ruido vanilla benigno (rdt, misnamed BSA, swaps de textura opcionales) |
| **JGNVSE "EDIDs conflicting"** | ✅ 1 solo conflicto benigno (UPNVSE+ vs YUP: `UPNVSEPVendorQuestItemSCRIPT`) — los conflictos DLC vanilla desaparecieron con los Fixed ESMs correctos |

---

## 3. EL PIPELINE (paso a paso, comandos + lógica)

### 3.1 Setup e instalación
```bash
./vnv.sh setup            # deps del sistema + venv + Camoufox (multi-distro)
./vnv.sh login            # cookies Nexus (Camoufox pasa Turnstile)
./vnv.sh config           # API key (metadata)
./vnv.sh credenciales     # email+pass (re-login automático)
./vnv.sh download         # actualizar.py (metadata) + gestor_descargas.py (descarga todo)
./vnv.sh install          # importar_mo2.py + root_mods.py + tweaks_ini
./vnv.sh estado           # verifica descargas vs manifest
./vnv.sh run              # lanza el juego vía MO2 CLI (NVSE)
./vnv.sh mo2              # abre el gestor MO2 (GUI) — también desde Steam (lanzar-mo2.sh)
./vnv.sh steam-add        # agrega "Fallout New Vegas (VNV)" a la biblioteca Steam (non-Steam)
```

### 3.2 Lógica de cada script (estado final — NO romper)
- **`scripts/actualizar.py`** — actualiza `manifest.json` (nombres/versiones/file_ids) eligiendo el **MAIN más reciente** (`max(uploaded_timestamp)`). ⚠️ OJO: si el mod tiene versiones por variante (ej. "Placement Fixes TTW" vs "Placement Fixes"), el MAIN más reciente puede ser la variante equivocada → verificar masters (bug histórico 90593 → TTW).
- **`scripts/gestor_descargas.py`** — estados en `estado.json` (pendiente/descargando/ok/fallo), retries con backoff, re-login automático. **Los extras con `url` usan descarga directa** (GitHub); los extras con `file_id` van por Nexus. ⚠️ Validar que `estado.json` apunte al archivo CORRECTO (hubo casos donde main↔extra quedaron cruzados: 58277 JIP dll, 84171 LOD INI).
- **`scripts/importar_mo2.py`** — descomprime cada mod a `mods/<Nombre>/` (FOMOD con elecciones explícitas por mod), fusiona extras, y **regenera las listas del perfil SIEMPRE con el manifest completo**:
  - `modlist.txt`: **preserva el estado +/- previo** (toggles manuales sobreviven — fix 0ffc8ce).
  - `loadorder.txt`/`plugins.txt`: orden canónico VNV Core (GUIAS_PLUGINS) — formato MO2 2.5.2: **SIN `*`**, CRLF, header.
  - `--solo MOD_ID`: re-importa UN mod **sin tocar las listas** (preserva loadorder exacto e inserta el plugin nuevo tras su master — fix b7782f3).
- **`scripts/root_mods.py`** — delega en los 5 root repos: `xnvse` (copia dlls + steam_loader), `4gb` (parche LAA nativo), `epic` (no-op en Steam), `bsa` (decompress.py — las 11 BSAs con 0x100 → bit30 + raw), `uefix` (port.py — parches xdelta3 del .mpi).
  - ⚠️ **ORDEN CRÍTICO**: el verify de Steam revierte el 4GB y los esms → si se corre `steam steam://validate/22380`, hay que re-correr `./vnv.sh root` (4gb + bsa + uefix) DESPUÉS.
- **`repos/ue-esm-fixes-linux/port.py`** — extrae los parches LZ4/xdelta3 del `.mpi` y los aplica a los esms del Data. ⚠️ **Los parches exigen los esms vanilla EXACTOS del depot actual** (los del usuario copiados de otra máquina NO matchean → esms corruptos con cabecera TES4 válida pero records faltantes → crash de diálogos). Tras un verify de Steam los esms quedan correctos y el rebuild sale bien.
- **`vnv.sh preparar_lanzamiento()`** — re-sincroniza `plugins.txt` desde `loadorder.txt` si MO2 los desincronizó (MO2 2.5.2 los reescribe al cerrar).
- **`vnv.sh correr_loot()`** — LOOT valida sobre una COPIA (lootcli no ve el VFS de MO2) — nunca toca el perfil.
- **`tweaks_ini`** — nvtf.ini (heap 400MB, 4GB, VRAM) en `Data/NVSE/Plugins/` + copia en el mod NVTF; FalloutCustom.ini en `profiles/Default/`.

### 3.3 Lanzamiento
- CLI MO2 correcto: `ModOrganizer.exe --profile=Default run -e NVSE` (`-e` sin valor; `-e=NVSE` NO funciona).
- El juego **AUTO-CARGA el último save** al iniciar → al testear configuraciones, vaciar `Saves/` del prefix o el test carga la partida vieja.
- Los saves viejos de otra instalación son **incompatibles** (formids de los UE fixes reenumerados) → "!"/texturas rosadas. Partida nueva = todo OK.

---

## 4. BUGS HISTÓRICOS (todos resueltos — no reintroducir)

1. **Mod 90593 TTW** — actualizar.py eligió la variante TTW → master `TaleOfTwoWastelands.esm` → crash. Fix: file_id manual `1000152138` + verificación de masters.
2. **plugins.txt con `*`** — MO2 2.5.2 no usa `*` (lo trata como parte del nombre → ningún plugin reconocido).
3. **`--solo` pisaba las listas** → modlist de 1 mod → MO2 desactivaba todo ("mods no configurados").
4. **estado.json cruzado** (58277 main→INI, 84171 extra→main) → faltaban `jip_nvse.dll` y `LOD Fixes.ini`.
5. **Fixed ESMs corruptos** (fuente esm vieja del usuario) → records faltantes → crash determinista `0x00AA991C` en init de diálogos (contexto: records YUP "Doctors"). Rebuild correcto post-verify.
6. **SArchiveList incompleto** (solo 6 BSAs base) en los 3 inis → DLC sin assets. Fix: 21 BSAs, `Update.bsa` al final.
7. **Load order incorrecto** (YUP 8º) → crash intermitente de diálogos. Fix: orden canónico.
8. **Re-activación de mods desactivados** por el regenerado del modlist → preservar estados.
9. **Verify de Steam revierte 4GB/BSAs/esms** → re-correr root_mods después.

---

## 5. LO QUE FALTA (pulido, nada del pipeline)

- Probar `./vnv.sh setup` en Debian/Ubuntu real (solo probado en Arch).
- Social preview del repo (`assets/gecko.png` en GitHub settings).
- Seguridad: regenerar contraseña Nexus + API key (`./vnv.sh config`) + `./vnv.sh credenciales`.
- Verificar `./vnv.sh install` completo en una máquina limpia (recrear el estado desde cero).

## 6. REGLAS IMPORTANTES

- **NO subir credenciales**; `downloads/`, `venv/`, `~/.config/` fuera del repo.
- **Siempre** usar `./venv/camoufox-python` (nunca `python3`) para los scripts de Nexus.
- **Rate limits Nexus**: 5s entre API, 8-15s entre descargas.
- Root repos **privados** (binarios con copyright) — no volverlos públicos.
- `.mpi` de UE fixes (220 MB) fuera del repo; `port.py` lo extrae del `.7z` a `~/.cache/vnv-uefix/` con 7z.
- El repo NO redistribuye mods (se descargan con la sesión del usuario).

## 7. REFERENCIAS

- `BRAIN.md` — detalle técnico completo.
- `obsidian/` — bóveda documental (`Inicio.md` es el hub).
- `README.md` — guía de usuario.
- Comandos: `./vnv.sh {setup|login|config|credenciales|download|estado|install|loot|run|mo2|steam-add|ui}`
