# 🔁 HANDOFF — VNV Linux Installer

Mensaje para el agente que continúe este proyecto. Léelo completo antes de actuar.

---

## 1. QUÉ ES ESTO

**vnv-linux**: instalador 100% automático del Core de **Viva New Vegas** (53 mods de Fallout New Vegas) para **Linux + Steam**.

- Repo público: `https://github.com/jhoniwana/vnv-linux` (rama `main`)
- Código local: `/home/shot/vnv-linux/`
- Documentación completa: `BRAIN.md` (bitácora técnica) + `obsidian/` (bóveda de 17 docs con wikilinks)
- **El pipeline completo está construido y probado EXCEPTO la instalación real con el juego.**

## 2. ESTADO ACTUAL (verificado en vivo)

| Componente | Estado |
|---|---|
| 53 mods descargados (1.1 GB en `downloads/`) | ✅ verificados (0 HTML, versiones correctas) |
| Login automático a Nexus (Camoufox pasa Turnstile) | ✅ probado |
| Gestor de descargas (estados, retries, re-login) | ✅ probado (auto-recuperación: sesión borrada → se recuperó solo) |
| Setup multi-distro (Debian/Ubuntu/Arch/Fedora/openSUSE) | ✅ probado en Arch/EndeavourOS |
| UI web (`./vnv.sh ui` — wizard 6 pasos, sin terminal) | ✅ probado (SSE en vivo) |
| Importador automático a MO2 (53/53) | ✅ probado |
| Comando `steam` (diagnóstico Proton appid 22380) | ✅ script listo, no probado en máquina con Steam |
| Instalación real (MO2-LINT, Wine, LOOT, lanzar juego) | 🟡 **NO probado — requiere hardware con el juego** |

## 3. LO QUE FALTA (priorizado)

### 3.1 PRINCIPAL — Probar la instalación real en una máquina con Steam + FNV
En la máquina del usuario (tiene Steam con Fallout New Vegas):
1. `git clone https://github.com/jhoniwana/vnv-linux && cd vnv-linux`
2. **En Steam**: FNV (appid 22380) → Propiedades → Compatibilidad → forzar Proton → jugar una vez (crea el prefix `steamapps/compatdata/22380/pfx`)
3. `./vnv.sh ui` → correr los 6 pasos en orden (o en terminal: `./vnv.sh setup` → `./vnv.sh login` → `./vnv.sh download` → `./vnv.sh steam --si` → `./vnv.sh install` → `./vnv.sh run`)
4. Verificar: MO2-LINT instala MO2 en el prefix del juego (vía protontricks), los 53 mods importados, INI tweaks aplicados, LOOT ordena, el juego arranca con los mods
5. **Reportar cualquier fallo** con el log de la UI (la UI muestra el output en vivo)

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

## 4. CÓMO FUNCIONA (lo esencial para no romper nada)

### Login y descargas (el gran logro)
- **Login**: `scripts/login_camoufox.py` — Camoufox (Firefox anti-detección) headless pasa el Turnstile de Cloudflare. Guarda `nexusmods_session` + `cf_clearance` en `~/.config/vnv-linux/` (600).
- **Descarga gratis**: la API `download_link` es solo Premium. El endpoint que funciona para FREE es:
  `https://www.nexusmods.com/Download/?id={file_id}&game_id=130&source=ModPage`
  - Con la cookie `nexusmods_session` muestra la página de descarga (auto-download o botón)
- **Gestor**: `scripts/gestor_descargas.py` — estados en `estado.json` (pendiente/descargando/ok/fallo), 3 retries con backoff, espera challenges Cloudflare, **re-login automático** si detecta "Log in" (no "Sign in") en la página.
- **Siempre usar el wrapper**: `./venv/camoufox-python` (python del venv con LD_LIBRARY_PATH correcto) — NUNCA `python3` directo para los scripts de Nexus.

### Instalación
- **MO2-LINT** (`mo2-installer`) instala MO2 en el prefix de Proton del juego vía protontricks
- `scripts/importar_mo2.py` descomprime los 53 mods a `mods/<Nombre>/` + escribe `profiles/Default/modlist.txt`
- `tweaks_ini` escribe `Data/NVSE/Plugins/nvtf.ini` (heap + 4GB)
- LOOT: primera vez botón Sort en MO2
- El juego se lanza DESDE MO2 (no desde Steam directo) — el VFS de MO2 monta los mods

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
- Comandos: `./vnv.sh {ui|setup|login|config-cookies|credenciales|config|download|estado|steam|install|run}`
