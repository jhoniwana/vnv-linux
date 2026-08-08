#!/usr/bin/env bash
# ============================================================================
# vnv.sh — Fully automated Viva New Vegas (Core) installer on Linux/Steam
#
#   ./vnv.sh setup          → prepare the environment (venv, Camoufox, libs, login)
#   ./vnv.sh login          → automatic Nexus login (Camoufox passes Turnstile)
#   ./vnv.sh config-cookies → save the session cookie manually (fallback)
#   ./vnv.sh download       → download/update the mods (manager with states)
#   ./vnv.sh estado         → verify files vs manifest (55/55, integrity)
#   ./vnv.sh install        → MO2-LINT + Proton prefix + import mods + INIs + LOOT
#   ./vnv.sh run            → launch the game via MO2 (Steam → "Launch Mod Organizer")
#   ./vnv.sh mo2            → open the MO2 manager (GUI); start the game from there
#                             (lanzar-mo2.sh is the shortcut to add to Steam)
#   ./vnv.sh steam-add      → add "Fallout New Vegas (VNV)" to Steam as a non-Steam game
#                             (opens MO2 on click; requires Steam closed)
#   ./vnv.sh update         → alias of download (updates manifest + mods)
#
# Works on: Debian, Ubuntu, Arch, Fedora, openSUSE and derivatives.
# ============================================================================
# vnv.sh — Fully automated Viva New Vegas (Core) installer on Linux/Steam
#
#   ./vnv.sh setup          → prepare the environment (venv, Camoufox, libs, login)
#   ./vnv.sh login          → automatic Nexus login (Camoufox passes Turnstile)
#   ./vnv.sh config-cookies → save the session cookie manually (fallback)
#   ./vnv.sh download       → download/update the mods (manager with states)
#   ./vnv.sh estado         → verify files vs manifest (55/55, integrity)
#   ./vnv.sh install        → MO2-LINT + Proton prefix + import mods + INIs + LOOT
#   ./vnv.sh run            → launch the game via MO2 (Steam → "Launch Mod Organizer")
#   ./vnv.sh mo2            → open the MO2 manager (GUI); start the game from there
#                             (lanzar-mo2.sh is the shortcut to add to Steam)
#   ./vnv.sh steam-add      → add "Fallout New Vegas (VNV)" to Steam as a non-Steam game========
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

GAME_DIR=""
STEAM_LIBRARIES=(
  "$HOME/.steam/steam/steamapps"
  "$HOME/.local/share/Steam/steamapps"
  "${VNV_STEAM_LIBRARY:-}"   # opcional: otra biblioteca de Steam (VNV_STEAM_LIBRARY=/mnt/games/steamapps)
)
MO2_INSTALLER_REPO="Furglitch/modorganizer2-linux-installer"
MO2_LINT="$HOME/.local/bin/mo2-lint"
MO2_INSTANCE="${MO2_INSTANCE:-$HOME/.local/share/modorganizer2}"
MO2_GAME_ID="falloutnv"
WINEPREFIX_DEFAULT="$HOME/.local/share/vnv-wine"
CONFIG_DIR="$HOME/.config/vnv-linux"
TMP_DIR="${TMPDIR:-/tmp}/vnv"
# protontricks-launch: looked up in PATH; fallback to the standard pip ~/.local/bin
PT_LAUNCH="$(command -v protontricks-launch 2>/dev/null || printf '%s\n' "$HOME/.local/bin/protontricks-launch")"
# site-packages of the interpreter that installed protontricks (for the Camoufox venv).
# Busca en ~/.local/lib/python3.*/site-packages el que tenga el paquete.
PT_PYTHONPATH="$(python3 -c 'import site; print(site.USER_SITE)' 2>/dev/null || true)"
if [[ -z "$PT_PYTHONPATH" || ! -d "$PT_PYTHONPATH/protontricks" ]]; then
  # find | head genera SIGPIPE en find → con pipefail mata el script SILENCIOSO.
  # Usar -quit (sin pipe) para que nunca explote en sistemas sin protontricks.
  PT_PYTHONPATH="$(find "$HOME/.local/lib" -maxdepth 2 -type d -name site-packages \
    -exec test -f '{}/protontricks/cli/__init__.py' ';' -print -quit 2>/dev/null || true)"
fi
PT_PYTHONPATH="${PT_PYTHONPATH:-$HOME/.local/lib/python3/site-packages}"
PY="$ROOT/venv/camoufox-python"   # python del venv con libs correctas

info()  { echo -e "\e[1;34m[VNV]\e[0m $*"; }
ok()    { echo -e "\e[1;32m  ✔\e[0m $*"; }
fail()  { echo -e "\e[1;31m  ✘\e[0m $*"; }

necesita_setup() {
  if [[ ! -x "$PY" ]]; then
    fail "Environment missing — first run:  ./vnv.sh setup"
    exit 1
  fi
}

buscar_juego() {
  info "Looking for Fallout New Vegas on Steam..."
  for lib in "${STEAM_LIBRARIES[@]}"; do
    local cand="$lib/common/Fallout New Vegas"
    if [[ -f "$cand/FalloutNV.exe" ]]; then
      GAME_DIR="$cand"
      ok "Game at: $GAME_DIR"
      return 0
    fi
  done
  fail "Game not found. Edit STEAM_LIBRARIES in the script or install it on Steam."
  return 1
}

instalar_mo2() {
  local MO2_BIN="$(command -v mo2-lint 2>/dev/null || true)"
  if [[ -z "$MO2_BIN" && -x "$MO2_LINT" ]]; then MO2_BIN="$MO2_LINT"; fi
  if [[ -n "$MO2_BIN" ]]; then
    ok "MO2-LINT listo: $MO2_BIN"
    return 0
  fi
  info "Descargando MO2-LINT (instalador de Mod Organizer 2 para Linux)..."
  mkdir -p "$HOME/.local/bin"
  local rel url
  rel="$(curl -fsSL "https://api.github.com/repos/$MO2_INSTALLER_REPO/releases" \
        | grep -m1 '"tag_name":' | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')"
  if [[ -z "$rel" ]]; then
    fail "Could not get the latest MO2-LINT release (network?)"
    return 1
  fi
  url="https://github.com/$MO2_INSTALLER_REPO/releases/download/$rel/mo2-lint"
  curl -fL "$url" -o "$MO2_LINT" 2>/dev/null || {
    fail "MO2-LINT download failed"
    return 1
  }
  chmod +x "$MO2_LINT"
  ok "MO2-LINT instalado en $MO2_LINT"
}

crear_instancia_mo2() {
  info "Creando instancia de MO2 para Fallout: New Vegas en $MO2_INSTANCE..."
  info "  (descarga MO2 + Java + winetricks, configura el prefix de Proton"
  info "   and add the 'Launch Mod Organizer' option to Steam)"
  mo2-lint install "$MO2_GAME_ID" "$MO2_INSTANCE" --unattended -l INFO 2>/dev/null || {
    fail "mo2-lint install failed — check the log (mo2-lint -l DEBUG ...)"
    return 1
  }
  ok "Instancia MO2 creada"
}

dependencias_wine() {
  info "Conectando MO2 con el Proton de Steam (appid 22380 — Fallout NV)..."
  # MO2-LINT usa protontricks para correr MO2 dentro del prefix de Proton del juego
  if ! command -v protontricks >/dev/null 2>&1; then
    fail "Falta protontricks — instalalo (la UI lo muestra en el setup) o:"
    fail "  Debian/Ubuntu: sudo apt install protontricks"
    fail "  Arch:          sudo pacman -S protontricks"
    fail "  Fedora:        sudo dnf install protontricks"
    return 1
  fi
  ok "protontricks disponible"
  # asegurar que Steam tenga el prefix del juego (una corrida con Proton lo crea)
  local prefix="$HOME/.steam/steam/steamapps/compatdata/22380"
  if [[ ! -d "$prefix" ]]; then
    info "Proton prefix for FNV does not exist yet."
    info "  En Steam: FNV → Propiedades → Compatibilidad → forzar Proton → Jugar UNA vez."
    info "  (or run: protontricks-launch 22380 cmd /c echo ready)"
  else
    ok "Prefix de Proton del juego encontrado: $prefix"
  fi
}

importar_mods() {
  info "Importando mods a la instancia de MO2 ($MO2_INSTANCE)..."
  if [[ -d "$ROOT/downloads" && -n "$(ls -A "$ROOT/downloads" 2>/dev/null)" ]]; then
    "$PY" scripts/importar_mo2.py --dir "$MO2_INSTANCE" || {
      fail "The import had failures — check the listing"
      return 1
    }
  else
    fail "downloads/ is empty — first run:  ./vnv.sh download"
    return 1
  fi
}

root_mods() {
  info "Installing root mods (xNVSE, 4GB, BSA Decompressor, UE ESM Fixes — native)..."
  "$PY" scripts/root_mods.py --mo2-dir "$MO2_INSTANCE" || {
    fail "root mods: a step failed — check the output"
    return 1
  }
}

tweaks_ini() {
  info "Applying INI tweaks (NVTF / heap / 4GB)..."
  local ini="$GAME_DIR/Data/NVSE/Plugins/nvtf.ini"
  mkdir -p "$(dirname "$ini")"
  cat > "$ini" <<'EOF'
[MAIN]
EnableHeapReplacement = true
HeapReplacementType = 2
HeapReplacementSize = 400
Enable4GBPatch = true
[VRAM]
EnableVRAMSizeOverride = true
EOF
  # also inside the NVTF mod imported to MO2 (if it exists), so the VFS serves it
  local nvtf_ini_mo2="$(find "$MO2_INSTANCE/mods" -maxdepth 4 -path '*NVSE/Plugins/nvtf.ini' 2>/dev/null | head -1)"
  if [[ -n "$nvtf_ini_mo2" ]]; then
    cp "$ini" "$nvtf_ini_mo2"
    ok "nvtf.ini applied (game + $nvtf_ini_mo2)"
  else
    ok "nvtf.ini applied (game — the NVTF mod does not ship the file; MO2 serves it via VFS)"
  fi

  # FalloutCustom.ini from the guide (Custom INI — overrides via JIP LN NVSE).
  # MO2 exposes the profile INIs to the game, so it lives in profiles/Default/.
  local profini="$MO2_INSTANCE/profiles/Default"
  mkdir -p "$profini"
  if [[ -f "$ROOT/files/FalloutCustom.ini" ]]; then
    cp "$ROOT/files/FalloutCustom.ini" "$profini/FalloutCustom.ini"
    ok "FalloutCustom.ini applied (Default profile)"
  else
    fail "Missing files/FalloutCustom.ini — Custom INI not applied"
  fi

  # SArchiveList completo (21 BSAs, orden vanilla, Update.bsa al final = mayor
  # prioridad) en los 3 inis. Steam validate restaura Fallout_default.ini a la
  # lista base de 6 → sin esto las BSAs de DLC quedan sin registrar.
  local sar_list="Fallout - Textures.bsa, Fallout - Textures2.bsa, Fallout - Meshes.bsa, Fallout - Voices1.bsa, Fallout - Sound.bsa, Fallout - Misc.bsa, DeadMoney - Main.bsa, DeadMoney - Sounds.bsa, HonestHearts - Main.bsa, HonestHearts - Sounds.bsa, OldWorldBlues - Main.bsa, OldWorldBlues - Sounds.bsa, LonesomeRoad - Main.bsa, LonesomeRoad - Sounds.bsa, GunRunnersArsenal - Main.bsa, GunRunnersArsenal - Sounds.bsa, ClassicPack - Main.bsa, CaravanPack - Main.bsa, MercenaryPack - Main.bsa, TribalPack - Main.bsa, Update.bsa"
  local inis_bsa=(
    "$GAME_DIR/Fallout_default.ini"
    "$HOME/.local/share/Steam/steamapps/compatdata/22380/pfx/drive_c/users/steamuser/Documents/My Games/FalloutNV/Fallout.ini"
    "$HOME/.local/share/Steam/steamapps/compatdata/22380/pfx/drive_c/users/steamuser/Documents/My Games/FalloutNV/FalloutPrefs.ini"
  )
  for ini_b in "${inis_bsa[@]}"; do
    if [[ -f "$ini_b" ]]; then
      chmod u+w "$ini_b" 2>/dev/null
      sed -i "s|^SArchiveList=.*|SArchiveList=$sar_list|" "$ini_b" 2>/dev/null
    fi
  done
  ok "SArchiveList: 21 BSAs applied (game INIs — survives Steam re-validation)"
}

correr_loot() {
  # VALIDACIÓN NO-DESTRUCTIVA: lootcli standalone NO ve el VFS de MO2 y usa el
  # formato propio de LOOT (plugins.txt con '*'), no el de MO2 2.5.2. Por eso se
  # valida sobre una COPIA construida desde loadorder.txt (21 activos en orden de
  # guide) and the real profile stays untouched.
  info "Validating load order with LOOT (lootcli, on a copy — does not touch the profile)..."
  local lootcli="$MO2_INSTANCE/loot/lootcli.exe"
  if [[ ! -f "$lootcli" ]]; then
    fail "lootcli.exe not found in $MO2_INSTANCE/loot — check the MO2 installation"
    return 1
  fi
  mkdir -p "$TMP_DIR"
  {
    printf '%s\n' "# This file was automatically generated by Mod Organizer."
    grep -v '^#' "$MO2_INSTANCE/profiles/Default/loadorder.txt" | sed 's/^/*/'
  } > "$TMP_DIR/loot_plugins.txt"
  local dlls="Z:$(echo "$MO2_INSTANCE" | sed 's|/|\\\\|g')\\dlls"
  local game_path="Z:$(echo "$GAME_DIR" | sed 's|/|\\\\|g')"
  local plugin_list="Z:$(echo "$TMP_DIR/loot_plugins.txt" | sed 's|/|\\\\|g')"
  local out="$TMP_DIR/loot_report.json"
  WINEPATH="$dlls" PYTHONPATH="$PT_PYTHONPATH" "$PY" "$PT_LAUNCH" \
    --appid 22380 "$lootcli" --game FalloutNV --gamePath "$game_path" \
    --pluginListPath "$plugin_list" --out "Z:$(echo "$TMP_DIR/loot_report.json" | sed 's|/|\\\\|g')" \
    --auto-sort 2>&1 | rg -iv "fixme|pressure|Fontconfig|protontricks \(WARNING\)" | tail -5
  if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
    ok "LOOT validated the load order (diagnostic only — profile untouched)"
  else
    fail "LOOT failed — check the output"
    return 1
  fi
}

# Common preparation before touching the prefix: Steam running, writable INIs,
# y lista activa (plugins.txt) sincronizada desde loadorder.txt. MO2 2.5.2 usa
# plugins.txt SIN el marcador '*' (lista de activos CRLF); si el archivo tiene
# '*', MO2 does not recognize any plugin ("Plugin not found: *FalloutNV.esm") and on
# shutdown it leaves only the master. loadorder.txt survives, so we re-sync
# la lista activa desde loadorder.txt antes de cada launch.
preparar_lanzamiento() {
  if ! pgrep -f "steamwebhelper" >/dev/null 2>&1; then
    info "Steam is not running — starting it (the game needs it)..."
    nohup steam >/dev/null 2>&1 &
    sleep 20
  fi
  # los INIs del perfil deben ser escribibles (el juego los modifica al arrancar)
  chmod u+w "$MO2_INSTANCE"/profiles/*/*.ini 2>/dev/null
  local prof="$MO2_INSTANCE/profiles/Default"
  if [[ -f "$prof/loadorder.txt" ]]; then
    if ! diff -q <(grep -v '^#' "$prof/loadorder.txt") <(grep -v '^#' "$prof/plugins.txt") >/dev/null 2>&1; then
      info "plugins.txt out of sync with loadorder.txt — regenerating active list..."
      {
        printf '%s\r\n' "# This file was automatically generated by Mod Organizer."
        tr -d '\r' < "$prof/loadorder.txt" | grep -v '^#' | sed 's/$/\r/'
      } > "$prof/plugins.txt"
    fi
  fi
}

lanzar() {
  info "Launching Fallout New Vegas via MO2 (NVSE)..."
  if [[ ! -f "$MO2_INSTANCE/ModOrganizer.exe" ]]; then
    fail "MO2 is not installed — run ./vnv.sh install"
    return 1
  fi
  preparar_lanzamiento
  PYTHONPATH="$PT_PYTHONPATH" "$PY" "$PT_LAUNCH" \
    --appid 22380 "$MO2_INSTANCE/ModOrganizer.exe" \
    --profile=Default run -e NVSE
}

# Abre el GESTOR (GUI de Mod Organizer) en el prefix del juego: se ven los mods
# and from there the game starts (Play button with NVSE selected).
abrir_mo2() {
  info "Opening the Mod Organizer manager (GUI)..."
  if [[ ! -f "$MO2_INSTANCE/ModOrganizer.exe" ]]; then
    fail "MO2 is not installed — run ./vnv.sh install"
    return 1
  fi
  preparar_lanzamiento
  PYTHONPATH="$PT_PYTHONPATH" "$PY" "$PT_LAUNCH" \
    --appid 22380 "$MO2_INSTANCE/ModOrganizer.exe" \
    --profile=Default
}

case "${1:-}" in
  setup)
    bash "$ROOT/setup.sh"
    ;;
  config)
    # Save the local API key (0600 perms) for API metadata
    mkdir -p "$CONFIG_DIR"
    read -rsp "Paste your Nexus API key (https://www.nexusmods.com/settings/api-keys): " KEY_INPUT
    echo
    if [[ -z "$KEY_INPUT" ]]; then
      fail "Empty key — nothing was saved"
      exit 1
    fi
    umask 077
    printf '%s\n' "$KEY_INPUT" > "$CONFIG_DIR/api_key"
    ok "Key guardada en $CONFIG_DIR/api_key (permisos 600)"
    ;;
  login)
    necesita_setup
    # Automatic login: headless Camoufox passes the Turnstile and saves the cookies
    info "Automatic Nexus login (Camoufox)..."
    NEXUS_USER="${NEXUS_USER:-}" NEXUS_PASS="${NEXUS_PASS:-}" "$PY" scripts/login_camoufox.py
    ;;
  config-cookies)
    # Fallback manual: pegar la cookie nexusmods_session
    mkdir -p "$CONFIG_DIR"
    echo "To grab your session cookie:"
    echo "  1. Logueate en https://www.nexusmods.com"
    echo "  2. F12 → Application → Cookies → https://www.nexusmods.com"
    echo "  3. Copy the value of 'nexusmods_session'"
    read -rsp "Paste the value of the nexusmods_session cookie: " SID_INPUT
    echo
    if [[ -z "$SID_INPUT" ]]; then
      fail "Empty cookie"
      exit 1
    fi
    umask 077
    printf '%s\n' "$SID_INPUT" > "$CONFIG_DIR/nexus_session"
    ok "Cookie guardada en $CONFIG_DIR/nexus_session (permisos 600)"
    # cf_clearance is captured during the first smoke test / automatic login
    ;;
  credenciales)
    # Save Nexus user+pass (0600 perms) for automatic re-login
    mkdir -p "$CONFIG_DIR"
    read -rsp "Nexus email: " USER_INPUT
    echo
    read -rsp "Nexus password: " PASS_INPUT
    echo
    if [[ -z "$USER_INPUT" || -z "$PASS_INPUT" ]]; then
      fail "Empty credentials"
      exit 1
    fi
    umask 077
    printf '%s\n%s\n' "$USER_INPUT" "$PASS_INPUT" > "$CONFIG_DIR/credenciales"
    ok "Credentials saved to $CONFIG_DIR/credenciales (permisos 600)"
    echo "⚠ Recommended: regenerate your Nexus password from time to time."
    echo "  The manager uses them ONLY to re-login automatically if the session expires."
    ;;
  download|update)
    necesita_setup
    # actualiza manifest (nombres/versiones/file_ids correctos) y descarga lo pendiente
    if [[ -s "$CONFIG_DIR/api_key" ]]; then
      info "Updating metadata from the API..."
      export NEXUS_API_KEY="$(cat "$CONFIG_DIR/api_key")"
      "$PY" scripts/actualizar.py
    fi
    info "Downloading mods (manager with states and retries)..."
    "$PY" scripts/gestor_descargas.py
    ;;
  estado|verificar)
    necesita_setup
    "$PY" scripts/gestor_descargas.py --verificar
    ;;
  ui)
    necesita_setup
    # Interfaz web local: abre el navegador, TODO desde la UI (sin terminal)
    info "Opening the web interface..."
    exec "$PY" "$ROOT/ui.py"
    ;;
  steam)
    # Steam + Proton connection diagnostics (step 1 of the install flow)
    info "=== Steam connection ==="
    local steam_bin=""
    for c in steam steam-native flatpak; do
      command -v "$c" >/dev/null 2>&1 && steam_bin="$c" && break
    done
    if [[ -z "$steam_bin" ]]; then
      fail "Steam not found. Install it and log in, then run this again."
      exit 1
    fi
    ok "Steam detectado: $steam_bin"

    # is FNV installed?
    local fnv_dir=""
    for lib in "${STEAM_LIBRARIES[@]}"; do
      local cand="$lib/common/Fallout New Vegas"
      if [[ -f "$cand/FalloutNV.exe" ]]; then
        fnv_dir="$cand"
        break
      fi
    done
    if [[ -z "$fnv_dir" ]]; then
      fail "Fallout New Vegas not found. Install it on Steam first."
      exit 1
    fi
    ok "Fallout New Vegas en: $fnv_dir"

    # ¿prefix de Proton creado? (compatdata/22380)
    local prefix=""
    for lib in "${STEAM_LIBRARIES[@]}"; do
      local p="$lib/compatdata/22380"
      if [[ -d "$p/pfx" ]]; then
        prefix="$p"
        break
      fi
    done
    if [[ -z "$prefix" ]]; then
      info "The game Proton prefix does not exist yet."
      info "  Para crearlo: en Steam, FNV → Propiedades → Compatibilidad →"
      info "  'Force the use of a specific Steam Play compatibility tool' → Proton."
      echo
      if [[ "${2:-}" == "--si" ]]; then
        R="s"
      else
        read -rp "Try launching FNV with Proton now (creates the prefix)? [y/N]: " R
      fi
      if [[ "$R" =~ ^[sSyY]$ ]]; then
        info "Launching FNV via Steam... (wait for the window and close it)"
        nohup "$steam_bin" steam://rungameid/22380 >/dev/null 2>&1 &
        sleep 5
        info "Check in 1-2 minutes whether $HOME/.steam/steam/steamapps/compatdata/22380 appeared"
      fi
    else
      ok "Prefix de Proton listo: $prefix"
    fi
    if command -v protontricks >/dev/null 2>&1; then
      ok "protontricks available (MO2 will run in the game prefix)"
    else
      fail "protontricks missing — check the system deps in ./vnv.sh setup"
    fi
    ;;
  install)
    necesita_setup
    buscar_juego
    instalar_mo2
    if [[ ! -f "$MO2_INSTANCE/ModOrganizer.exe" ]]; then
      crear_instancia_mo2
    else
      ok "Instancia MO2 ya existe: $MO2_INSTANCE"
    fi
    importar_mods
    root_mods
    tweaks_ini
    info "Installation ready. The load order is already in the guide order (== LOOT)."
    info "  To re-sort in MO2: GUI → Sort button. To validate with lootcli: ./vnv.sh loot"
    ;;
  loot)
    necesita_setup
    buscar_juego
    correr_loot
    ;;
  run)
    buscar_juego
    lanzar
    ;;
  mo2)
    buscar_juego
    abrir_mo2
    ;;
  steam-add)
    necesita_setup
    "$PY" scripts/agregar_a_steam.py "${@:2}"
    ;;
  bsa)
    # ⚠️ NOT NEEDED on the current depot (all 11 target BSAs ship raw; audio is
    # already valid RIFF WAVE — see README "Tools you do NOT need"). Kept only
    # for research: do NOT run Meshes.bsa/Misc.bsa (32-bit game crashes).
    necesita_setup
    buscar_juego
    "$PY" scripts/bsa_decompressor.py --game-dir "$GAME_DIR" "${@:2}"
    ;;
  bsa-verify)
    # Verify CRC64 name hashes without writing (harmless, useful for checks)
    necesita_setup
    buscar_juego
    "$PY" scripts/bsa_decompressor.py --game-dir "$GAME_DIR" --verify "${@:2}"
    ;;
  esmfix)
    # Apply Ultimate Edition ESM Fixes (xdelta patches)
    necesita_setup
    buscar_juego
    "$PY" scripts/esm_fixes.py --game-dir "$GAME_DIR" --dest "${ESMFIX_DEST:-$HOME/.local/share/modorganizer2/mods/Fixed ESMs}" "${@:2}"
    ;;
  salud)
    # Full health check: verifies EVERY component (exe/LAA, NVSE, BSAs, INIs,
    # Fixed ESMs, downloads, session, MO2). Exit 0 = everything OK.
    necesita_setup
    "$PY" scripts/salud.py "${@:2}"
    ;;
  *)
    echo "Usage: $0 {setup|login|config-cookies|config|download|estado|install|loot|run|mo2|steam-add|bsa|bsa-verify|esmfix}"
    ;;
esac
