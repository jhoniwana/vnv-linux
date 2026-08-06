#!/usr/bin/env bash
# ============================================================================
# vnv.sh — Instalador 100% automático de Viva New Vegas (Core) en Linux/Steam
#
#   ./vnv.sh setup          → prepara entorno (venv, Camoufox, libs, login)
#   ./vnv.sh login          → login automático a Nexus (Camoufox pasa Turnstile)
#   ./vnv.sh config-cookies → guarda la cookie de sesión manualmente (fallback)
#   ./vnv.sh download       → descarga/actualiza los mods (gestor con estados)
#   ./vnv.sh estado         → verifica archivos vs manifest (53/53, integridad)
#   ./vnv.sh install        → MO2-LINT + prefix Proton + importar mods + INIs + LOOT
#   ./vnv.sh run            → lanza el juego vía MO2 (Steam → "Launch Mod Organizer")
#   ./vnv.sh update         → alias de download (actualiza manifest + mods)
#
# Funciona en: Debian, Ubuntu, Arch, Fedora, openSUSE y derivadas.
# ============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

GAME_DIR=""
STEAM_LIBRARIES=(
  "$HOME/.steam/steam/steamapps"
  "$HOME/.local/share/Steam/steamapps"
  "/mnt/games/steamapps"   # editar según tu setup
)
MO2_INSTALLER_REPO="Furglitch/modorganizer2-linux-installer"
MO2_LINT="$HOME/.local/bin/mo2-lint"
MO2_INSTANCE="${MO2_INSTANCE:-$HOME/.local/share/modorganizer2}"
MO2_GAME_ID="falloutnv"
WINEPREFIX_DEFAULT="$HOME/.local/share/vnv-wine"
CONFIG_DIR="$HOME/.config/vnv-linux"
PY="$ROOT/venv/camoufox-python"   # python del venv con libs correctas

info()  { echo -e "\e[1;34m[VNV]\e[0m $*"; }
ok()    { echo -e "\e[1;32m  ✔\e[0m $*"; }
fail()  { echo -e "\e[1;31m  ✘\e[0m $*"; }

necesita_setup() {
  if [[ ! -x "$PY" ]]; then
    fail "Falta el entorno — primero corré:  ./vnv.sh setup"
    exit 1
  fi
}

buscar_juego() {
  info "Buscando Fallout New Vegas en Steam..."
  for lib in "${STEAM_LIBRARIES[@]}"; do
    local cand="$lib/common/Fallout New Vegas"
    if [[ -f "$cand/FalloutNV.exe" ]]; then
      GAME_DIR="$cand"
      ok "Juego en: $GAME_DIR"
      return 0
    fi
  done
  fail "No encontré el juego. Editá STEAM_LIBRARIES en el script o instalalo en Steam."
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
    fail "No pude obtener la última release de MO2-LINT (¿red?)"
    return 1
  fi
  url="https://github.com/$MO2_INSTALLER_REPO/releases/download/$rel/mo2-lint"
  curl -fL "$url" -o "$MO2_LINT" 2>/dev/null || {
    fail "Descarga de MO2-LINT falló"
    return 1
  }
  chmod +x "$MO2_LINT"
  ok "MO2-LINT instalado en $MO2_LINT"
}

crear_instancia_mo2() {
  info "Creando instancia de MO2 para Fallout: New Vegas en $MO2_INSTANCE..."
  info "  (descarga MO2 + Java + winetricks, configura el prefix de Proton"
  info "   y agrega la opción 'Launch Mod Organizer' a Steam)"
  mo2-lint install "$MO2_GAME_ID" "$MO2_INSTANCE" --unattended -l INFO 2>/dev/null || {
    fail "mo2-lint install falló — revisá el log (mo2-lint -l DEBUG ...)"
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
    info "Prefix de Proton para FNV no existe aún."
    info "  En Steam: FNV → Propiedades → Compatibilidad → forzar Proton → Jugar UNA vez."
    info "  (o corré: protontricks-launch 22380 cmd /c echo listo)"
  else
    ok "Prefix de Proton del juego encontrado: $prefix"
  fi
}

importar_mods() {
  info "Importando mods a la instancia de MO2 ($MO2_INSTANCE)..."
  if [[ -d "$ROOT/downloads" && -n "$(ls -A "$ROOT/downloads" 2>/dev/null)" ]]; then
    "$PY" scripts/importar_mo2.py --dir "$MO2_INSTANCE" || {
      fail "La importación tuvo fallos — revisá el listado"
      return 1
    }
  else
    fail "downloads/ vacío — primero corré:  ./vnv.sh download"
    return 1
  fi
}

root_mods() {
  info "Instalando root mods (xNVSE, 4GB, BSA Decompressor, UE ESM Fixes — nativos)..."
  "$PY" scripts/root_mods.py --mo2-dir "$MO2_INSTANCE" || {
    fail "root mods: falló algún paso — revisá la salida"
    return 1
  }
}

tweaks_ini() {
  info "Aplicando tweaks de INI (NVTF / heap / 4GB)..."
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
  # además, dentro del mod NVTF importado a MO2 (si existe), para que VFS lo provea
  local nvtf_ini_mo2="$(find "$MO2_INSTANCE/mods" -maxdepth 4 -path '*NVSE/Plugins/nvtf.ini' 2>/dev/null | head -1)"
  if [[ -n "$nvtf_ini_mo2" ]]; then
    cp "$ini" "$nvtf_ini_mo2"
    ok "nvtf.ini aplicado (juego + $nvtf_ini_mo2)"
  else
    ok "nvtf.ini aplicado (juego — el mod NVTF no incluye el archivo; MO2 lo ve por VFS)"
  fi
}

correr_loot() {
  info "Ordenando plugins con LOOT..."
  info "  Abrí MO2 (Steam → Play → 'Launch Mod Organizer') y pulsá el botón Sort la primera vez."
  if command -v mo2-lint >/dev/null 2>&1; then
    info "  LOOT corre dentro del prefix del juego (lo incluye MO2-LINT)."
  fi
}

lanzar() {
  info "Lanzando Fallout New Vegas vía MO2..."
  info "  En Steam: FNV → Play (botón con flechita) → 'Launch Mod Organizer'."
  info "  Eso abre MO2 con los 53 mods; después pulsá 'Run' dentro de MO2 para jugar."
  if [[ -f "$MO2_INSTANCE/ModOrganizer.exe" ]]; then
    if command -v steam >/dev/null 2>&1 || command -v steam-native >/dev/null 2>&1; then
      info "  (abriendo Steam...)"
      nohup steam steam://rungameid/22380 >/dev/null 2>&1 &
    fi
  else
    fail "MO2 no está instalado — corré ./vnv.sh install"
  fi
}

case "${1:-}" in
  setup)
    bash "$ROOT/setup.sh"
    ;;
  config)
    # Guarda la API key local (permisos 600) para metadata vía API
    mkdir -p "$CONFIG_DIR"
    read -rsp "Pegá tu API key de Nexus (https://www.nexusmods.com/settings/api-keys): " KEY_INPUT
    echo
    if [[ -z "$KEY_INPUT" ]]; then
      fail "Key vacía — no se guardó nada"
      exit 1
    fi
    umask 077
    printf '%s\n' "$KEY_INPUT" > "$CONFIG_DIR/api_key"
    ok "Key guardada en $CONFIG_DIR/api_key (permisos 600)"
    ;;
  login)
    necesita_setup
    # Login automático: Camoufox headless pasa el Turnstile y guarda las cookies
    info "Login automático a Nexus (Camoufox)..."
    NEXUS_USER="${NEXUS_USER:-}" NEXUS_PASS="${NEXUS_PASS:-}" "$PY" scripts/login_camoufox.py
    ;;
  config-cookies)
    # Fallback manual: pegar la cookie nexusmods_session
    mkdir -p "$CONFIG_DIR"
    echo "Para sacar tu cookie de sesión:"
    echo "  1. Logueate en https://www.nexusmods.com"
    echo "  2. F12 → Application → Cookies → https://www.nexusmods.com"
    echo "  3. Copiá el valor de 'nexusmods_session'"
    read -rsp "Pegá el valor de la cookie nexusmods_session: " SID_INPUT
    echo
    if [[ -z "$SID_INPUT" ]]; then
      fail "Cookie vacía"
      exit 1
    fi
    umask 077
    printf '%s\n' "$SID_INPUT" > "$CONFIG_DIR/nexus_session"
    ok "Cookie guardada en $CONFIG_DIR/nexus_session (permisos 600)"
    # cf_clearance se obtiene en el primer smoke test / login automático
    ;;
  credenciales)
    # Guarda user+pass de Nexus (permisos 600) para el re-login automático
    mkdir -p "$CONFIG_DIR"
    read -rsp "Email de Nexus: " USER_INPUT
    echo
    read -rsp "Contraseña de Nexus: " PASS_INPUT
    echo
    if [[ -z "$USER_INPUT" || -z "$PASS_INPUT" ]]; then
      fail "Credenciales vacías"
      exit 1
    fi
    umask 077
    printf '%s\n%s\n' "$USER_INPUT" "$PASS_INPUT" > "$CONFIG_DIR/credenciales"
    ok "Credenciales guardadas en $CONFIG_DIR/credenciales (permisos 600)"
    echo "⚠ Recomendado: regenerá tu contraseña en Nexus de vez en cuando."
    echo "  El gestor las usa SOLO para re-loguear automáticamente si la sesión expira."
    ;;
  download|update)
    necesita_setup
    # actualiza manifest (nombres/versiones/file_ids correctos) y descarga lo pendiente
    if [[ -s "$CONFIG_DIR/api_key" ]]; then
      info "Actualizando metadata desde la API..."
      export NEXUS_API_KEY="$(cat "$CONFIG_DIR/api_key")"
      "$PY" scripts/actualizar.py
    fi
    info "Descargando mods (gestor con estados y retries)..."
    "$PY" scripts/gestor_descargas.py
    ;;
  estado|verificar)
    necesita_setup
    "$PY" scripts/gestor_descargas.py --verificar
    ;;
  ui)
    necesita_setup
    # Interfaz web local: abre el navegador, TODO desde la UI (sin terminal)
    info "Abriendo la interfaz web..."
    exec "$PY" "$ROOT/ui.py"
    ;;
  steam)
    # Diagnóstico/conexión con Steam + Proton (paso 1 del flujo de instalación)
    info "=== Conexión con Steam ==="
    local steam_bin=""
    for c in steam steam-native flatpak; do
      command -v "$c" >/dev/null 2>&1 && steam_bin="$c" && break
    done
    if [[ -z "$steam_bin" ]]; then
      fail "No encontré Steam. Instalalo y logueate, después volvé a correr esto."
      exit 1
    fi
    ok "Steam detectado: $steam_bin"

    # ¿está instalado FNV?
    local fnv_dir=""
    for lib in "${STEAM_LIBRARIES[@]}"; do
      local cand="$lib/common/Fallout New Vegas"
      if [[ -f "$cand/FalloutNV.exe" ]]; then
        fnv_dir="$cand"
        break
      fi
    done
    if [[ -z "$fnv_dir" ]]; then
      fail "No encontré Fallout New Vegas instalado. Instalalo en Steam primero."
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
      info "El prefix de Proton del juego NO existe todavía."
      info "  Para crearlo: en Steam, FNV → Propiedades → Compatibilidad →"
      info "  'Force the use of a specific Steam Play compatibility tool' → Proton."
      echo
      if [[ "${2:-}" == "--si" ]]; then
        R="s"
      else
        read -rp "¿Querés que intente lanzar FNV con Proton ahora (crea el prefix)? [s/N]: " R
      fi
      if [[ "$R" =~ ^[sSyY]$ ]]; then
        info "Lanzando FNV vía Steam... (esperá a que aparezca la ventana y cerrala)"
        nohup "$steam_bin" steam://rungameid/22380 >/dev/null 2>&1 &
        sleep 5
        info "Revisá en 1-2 minutos si apareció $HOME/.steam/steam/steamapps/compatdata/22380"
      fi
    else
      ok "Prefix de Proton listo: $prefix"
    fi
    if command -v protontricks >/dev/null 2>&1; then
      ok "protontricks disponible (MO2 podrá correr en el prefix del juego)"
    else
      fail "Falta protontricks — mirá las deps del sistema en ./vnv.sh setup"
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
    correr_loot
    info "Instalación lista. Siguiente: ./vnv.sh run"
    ;;
  run)
    buscar_juego
    lanzar
    ;;
  *)
    echo "Uso: $0 {setup|login|config-cookies|config|download|estado|install|run}"
    ;;
esac
