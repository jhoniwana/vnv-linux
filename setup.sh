#!/usr/bin/env bash
# ============================================================================
# setup.sh — Prepara el entorno VNV en CUALQUIER distro Linux
#
#   ./setup.sh             → prepara todo (venv, Camoufox, libs, login)
#   ./setup.sh --chequear  → diagnostics only (no install)
#
# What it does:
#   1. Detecta la distro y muestra/instala dependencias del sistema
#   2. Crea el venv e instala Camoufox (+ Playwright)
#   3. Smoke test: ¿Camoufox arranca con las libs del sistema?
#   4. Si falla → descarga micromamba (user-space, SIN sudo) con pixman
#      and creates a wrapper that resolves the libs (useful on semi-broken Arch,
#      Debian sin GTK3, etc.)
#   5. Checks the Nexus session (cookies); if missing → guides to login
# ============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV="$ROOT/venv"
CONFIG_DIR="$HOME/.config/vnv-linux"
WRAPPER="$VENV/camoufox-python"     # python del venv + libs correctas
LIBFIX="$VENV/libfix"                # micromamba env de respaldo (si hace falta)
MICROMAMBA_BIN="$VENV/micromamba"

info()  { echo -e "\e[1;34m[SETUP]\e[0m $*"; }
ok()    { echo -e "\e[1;32m  ✔\e[0m $*"; }
fail()  { echo -e "\e[1;31m  ✘\e[0m $*"; }

detectar_distro() {
  if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    DISTRO="${ID:-unknown}"
    DISTRO_VERSION="${VERSION_ID:-}"
  else
    DISTRO="unknown"
  fi
  info "Distro: $DISTRO $DISTRO_VERSION ($(uname -m))"
}

deps_sistema() {
  info "Dependencias del sistema para Camoufox (Firefox):"
  # per-distro deps (includes protontricks for the MO2 ↔ Steam/Proton bridge)
  case "$DISTRO" in
    debian|ubuntu|linuxmint|pop)
      echo "  Debian/Ubuntu:"
      echo "    sudo apt install -y libgtk-3-0 libasound2t64 libasound2 libdbus-glib-1-2 libx11-xcb1 libxcb-dri3-0 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libpango-1.0-0 libcairo2 libpixman-1-0 libnss3 libxss1 libegl1 libxkbcommon0 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libglib2.0-0 curl bzip2 python3-venv protontricks"
      ;;
    arch|manjaro|endeavouros)
      echo "  Arch:"
      echo "    sudo pacman -S --needed gtk3 alsa-lib libxcomposite libxdamage libxrandr libxtst pango cairo pixman nss libxss libegl libxkbcommon atk at-spi2-core libcups libdrm libgbm glib2 curl bzip2 python protontricks"
      ;;
    fedora|rhel|centos|rocky|almalinux)
      echo "  Fedora/RHEL:"
      echo "    sudo dnf install -y gtk3 alsa-lib libXcomposite libXdamage libXrandr libXtst pango cairo pixman nss libXScrnSaver libEGL libxkbcommon atk at-spi2-atk libcups libdrm libgbm glib2 curl bzip2 python3-virtualenv protontricks"
      ;;
    opensuse*|suse)
      echo "  openSUSE:"
      echo "    sudo zypper install -y gtk3 alsa-lib libXcomposite1 libXdamage1 libXrandr2 libXtst6 pango cairo pixman nss libXss1 libEGL1 libxkbcommon0 atk at-spi2-atk libcups2 libdrm2 libgbm1 glib2 curl bzip2 python311"
      ;;
    *)
      echo "  Unrecognized distro ($DISTRO) — install manually: GTK3, alsa-lib, nss, cairo, pixman, pango, libXcomposite, libXdamage, libXrandr, libXtst, python3-venv"
      ;;
  esac
  # is sudo available? try installing automatically on Debian/Arch/Fedora
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    info "passwordless sudo available — installing dependencies automatically..."
    case "$DISTRO" in
      debian|ubuntu|linuxmint|pop)
        sudo apt update -qq && sudo apt install -y -qq libgtk-3-0 libasound2t64 libasound2 libdbus-glib-1-2 libx11-xcb1 libxcb-dri3-0 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libpango-1.0-0 libcairo2 libpixman-1-0 libnss3 libxss1 libegl1 libxkbcommon0 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libglib2.0-0 curl bzip2 python3-venv 2>/dev/null && ok "deps installed" || fail "apt failed"
        ;;
      arch|manjaro|endeavouros)
        sudo pacman -S --needed --noconfirm gtk3 alsa-lib libxcomposite libxdamage libxrandr libxtst pango cairo pixman nss libxss libegl libxkbcommon atk at-spi2-core libcups libdrm libgbm glib2 curl bzip2 python 2>/dev/null && ok "deps installed" || fail "pacman failed"
        ;;
      fedora|rhel|centos|rocky|almalinux)
        sudo dnf install -y -q gtk3 alsa-lib libXcomposite libXdamage libXrandr libXtst pango cairo pixman nss libXScrnSaver libEGL libxkbcommon atk at-spi2-atk libcups libdrm libgbm glib2 curl bzip2 python3-virtualenv 2>/dev/null && ok "deps installed" || fail "dnf failed"
        ;;
    esac
  else
    info "No automatic sudo — run the commands above manually if Camoufox fails."
  fi
}

crear_venv() {
  if [[ ! -x "$VENV/bin/python" ]]; then
    info "Creando venv..."
    python3 -m venv "$VENV"
  fi
  "$VENV/bin/pip" install -q --upgrade pip 2>/dev/null || true
  if ! "$VENV/bin/python" -c "import camoufox" 2>/dev/null; then
    info "Instalando Camoufox..."
    "$VENV/bin/pip" install -q camoufox 2>&1 | tail -2 || {
      fail "pip install camoufox failed (missing python3-venv or network?)"
      return 1
    }
  fi
  if ! "$VENV/bin/python" -c "
from camoufox import pkgman
pkgman.installed_verstr()
" >/dev/null 2>&1; then
    info "Downloading the Camoufox binary (anti-detection Firefox)..."
    "$VENV/bin/python" -m camoufox fetch 2>&1 | tail -1 || {
      fail "camoufox fetch failed (network?)"
      return 1
    }
  fi
  if ! "$VENV/bin/python" -c "import flask" 2>/dev/null; then
    info "Instalando Flask (para la interfaz web)..."
    "$VENV/bin/pip" install -q flask 2>&1 | tail -1 || {
      fail "pip install flask failed"
      return 1
    }
  fi
  ok "venv + Camoufox + Flask listos"
}

instalar_libfix() {
  # Fallback: micromamba user-space con pixman (para distros con libs rotas)
  info "Problematic system libs — installing pixman via micromamba (no sudo)..."
  mkdir -p "$LIBFIX"
  if [[ ! -x "$MICROMAMBA_BIN" ]]; then
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest -o "$LIBFIX/micromamba.tar.bz2"
    tar -xjf "$LIBFIX/micromamba.tar.bz2" -C "$LIBFIX" bin/micromamba 2>/dev/null || true
    mv "$LIBFIX/bin/micromamba" "$MICROMAMBA_BIN" 2>/dev/null || true
    chmod +x "$MICROMAMBA_BIN"
    rm -rf "$LIBFIX/bin" "$LIBFIX/micromamba.tar.bz2"
  fi
  if [[ ! -x "$MICROMAMBA_BIN" ]]; then
    fail "micromamba could not be downloaded — downloads could fail due to system libs"
    return 1
  fi
  if [[ ! -f "$LIBFIX/lib/libpixman-1.so" ]]; then
    "$MICROMAMBA_BIN" create -p "$LIBFIX" -c conda-forge -y pixman >/dev/null 2>&1 || {
      # Debian/Ubuntu usually do not need this fallback; partially-updated Arch does
      fail "conda pixman failed"
      return 1
    }
  fi
  ok "libfix listo (pixman en $LIBFIX/lib)"
}

crear_wrapper() {
  # wrapper: python del venv + LD_LIBRARY_PATH correcto (si hace falta libfix)
  # Rutas RELATIVAS al propio wrapper → el proyecto es movible/portable.
  local EXTRA_LD=""
  if [[ -f "$LIBFIX/lib/libpixman-1.so" ]]; then
    EXTRA_LD='$DIR/libfix/lib'
  fi
  cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
# Wrapper generado por setup.sh — usa las libs correctas para Camoufox
DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$EXTRA_LD\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
exec "\$DIR/bin/python" "\$@"
EOF
  chmod +x "$WRAPPER"
  ok "wrapper creado: $WRAPPER"
}

smoke_test() {
  info "Smoke test: ¿Camoufox arranca?"
  local salida
  salida="$("$WRAPPER" -c "
from camoufox.sync_api import Camoufox
with Camoufox(headless=True) as b:
    print('CAMOUFOX_OK')
" 2>&1)" || true
  if echo "$salida" | grep -q "CAMOUFOX_OK"; then
    ok "Camoufox funciona con libs del sistema"
    return 0
  fi
  fail "Camoufox failed: $(echo "$salida" | grep -i -E "error|symbol|cannot open" | head -1)"
  info "Intentando fallback de libs (micromamba + pixman)..."
  if instalar_libfix && [[ -f "$LIBFIX/lib/libpixman-1.so" ]]; then
    crear_wrapper
    salida="$("$WRAPPER" -c "
from camoufox.sync_api import Camoufox
with Camoufox(headless=True) as b:
    print('CAMOUFOX_OK')
" 2>&1)" || true
    if echo "$salida" | grep -q "CAMOUFOX_OK"; then
      ok "Camoufox funciona con libfix"
      return 0
    fi
    fail "Camoufox sigue fallando: $(echo "$salida" | grep -i -E "error|symbol|cannot open" | head -1)"
    echo "--- diagnosis: run  $WRAPPER -c 'from camoufox.sync_api import Camoufox' ---"
    return 1
  fi
  return 1
}

verificar_sesion() {
  mkdir -p "$CONFIG_DIR"
  if [[ -s "$CONFIG_DIR/nexus_session" && -s "$CONFIG_DIR/cf_clearance" ]]; then
    ok "Session cookies present (nexus_session + cf_clearance)"
    return 0
  fi
  info "No Nexus session — you need to log in once (2 minutes)."
  echo "  Option A (recommended):  ./vnv.sh login"
  echo "    → opens real Chrome, you log in, it captures the cookies by itself"
  echo "  Option B (manual):       ./vnv.sh config-cookies"
  echo "    → paste the 'nexusmods_session' cookie from the browser (F12 → Application → Cookies)"
  return 1
}

# ============================== MAIN ==============================
if [[ "${1:-}" == "--chequear" ]]; then
  detectar_distro
  deps_sistema
  echo
  info "Estado:"
  [[ -x "$VENV/bin/python" ]] && ok "venv exists" || fail "venv does NOT exist (run ./setup.sh)"
  [[ -x "$WRAPPER" ]] && ok "wrapper existe" || fail "wrapper NO existe"
  [[ -s "$CONFIG_DIR/nexus_session" ]] && ok "Nexus session OK" || fail "no Nexus session"
  exit 0
fi

info "=== SETUP VNV LINUX ==="
detectar_distro
deps_sistema
crear_venv || exit 1
# if there is no wrapper yet (first time), create it without libfix
[[ -x "$WRAPPER" ]] || crear_wrapper
if ! smoke_test; then
  fail "Could not start Camoufox — check the system dependencies above."
  exit 1
fi
verificar_sesion || true
info "Setup completo. Siguientes pasos:"
echo "  1. (if no session)  ./vnv.sh login   or   ./vnv.sh config-cookies"
echo "  2. Descargar mods:      ./vnv.sh update"
echo "  3. Instalar:            ./vnv.sh install"
