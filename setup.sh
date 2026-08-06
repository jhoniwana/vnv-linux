#!/usr/bin/env bash
# ============================================================================
# setup.sh — Prepara el entorno VNV en CUALQUIER distro Linux
#
#   ./setup.sh             → prepara todo (venv, Camoufox, libs, login)
#   ./setup.sh --chequear  → solo diagnóstico (sin instalar)
#
# Qué hace:
#   1. Detecta la distro y muestra/instala dependencias del sistema
#   2. Crea el venv e instala Camoufox (+ Playwright)
#   3. Smoke test: ¿Camoufox arranca con las libs del sistema?
#   4. Si falla → descarga micromamba (user-space, SIN sudo) con pixman
#      y crea un wrapper que resuelve las libs (útil en Arch medio-roto,
#      Debian sin GTK3, etc.)
#   5. Verifica la sesión de Nexus (cookies); si faltan → guía al login
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
  # deps por distro (incluye protontricks para la conexión MO2 ↔ Steam/Proton)
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
      echo "  Distro no reconocida ($DISTRO) — instalá manualmente: GTK3, alsa-lib, nss, cairo, pixman, pango, libXcomposite, libXdamage, libXrandr, libXtst, python3-venv"
      ;;
  esac
  # ¿hay sudo? intentar instalar automáticamente en Debian/Arch/Fedora
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    info "sudo sin contraseña disponible — instalando dependencias automáticamente..."
    case "$DISTRO" in
      debian|ubuntu|linuxmint|pop)
        sudo apt update -qq && sudo apt install -y -qq libgtk-3-0 libasound2t64 libasound2 libdbus-glib-1-2 libx11-xcb1 libxcb-dri3-0 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libpango-1.0-0 libcairo2 libpixman-1-0 libnss3 libxss1 libegl1 libxkbcommon0 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libglib2.0-0 curl bzip2 python3-venv 2>/dev/null && ok "deps instaladas" || fail "apt falló"
        ;;
      arch|manjaro|endeavouros)
        sudo pacman -S --needed --noconfirm gtk3 alsa-lib libxcomposite libxdamage libxrandr libxtst pango cairo pixman nss libxss libegl libxkbcommon atk at-spi2-core libcups libdrm libgbm glib2 curl bzip2 python 2>/dev/null && ok "deps instaladas" || fail "pacman falló"
        ;;
      fedora|rhel|centos|rocky|almalinux)
        sudo dnf install -y -q gtk3 alsa-lib libXcomposite libXdamage libXrandr libXtst pango cairo pixman nss libXScrnSaver libEGL libxkbcommon atk at-spi2-atk libcups libdrm libgbm glib2 curl bzip2 python3-virtualenv 2>/dev/null && ok "deps instaladas" || fail "dnf falló"
        ;;
    esac
  else
    info "Sin sudo automático — corré los comandos de arriba manualmente si Camoufox falla."
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
      fail "pip install camoufox falló (¿falta python3-venv o red?)"
      return 1
    }
  fi
  if ! "$VENV/bin/python" -c "
from camoufox import pkgman
pkgman.installed_verstr()
" >/dev/null 2>&1; then
    info "Descargando el binario de Camoufox (Firefox anti-detección)..."
    "$VENV/bin/python" -m camoufox fetch 2>&1 | tail -1 || {
      fail "camoufox fetch falló (¿red?)"
      return 1
    }
  fi
  if ! "$VENV/bin/python" -c "import flask" 2>/dev/null; then
    info "Instalando Flask (para la interfaz web)..."
    "$VENV/bin/pip" install -q flask 2>&1 | tail -1 || {
      fail "pip install flask falló"
      return 1
    }
  fi
  ok "venv + Camoufox + Flask listos"
}

instalar_libfix() {
  # Fallback: micromamba user-space con pixman (para distros con libs rotas)
  info "Libs del sistema problemáticas — instalando pixman vía micromamba (sin sudo)..."
  mkdir -p "$LIBFIX"
  if [[ ! -x "$MICROMAMBA_BIN" ]]; then
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest -o "$LIBFIX/micromamba.tar.bz2"
    tar -xjf "$LIBFIX/micromamba.tar.bz2" -C "$LIBFIX" bin/micromamba 2>/dev/null || true
    mv "$LIBFIX/bin/micromamba" "$MICROMAMBA_BIN" 2>/dev/null || true
    chmod +x "$MICROMAMBA_BIN"
    rm -rf "$LIBFIX/bin" "$LIBFIX/micromamba.tar.bz2"
  fi
  if [[ ! -x "$MICROMAMBA_BIN" ]]; then
    fail "micromamba no se pudo descargar — las descargas podrían fallar por libs del sistema"
    return 1
  fi
  if [[ ! -f "$LIBFIX/lib/libpixman-1.so" ]]; then
    "$MICROMAMBA_BIN" create -p "$LIBFIX" -c conda-forge -y pixman >/dev/null 2>&1 || {
      # Debian/Ubuntu no necesita este fallback normalmente; arch con update parcial sí
      fail "conda pixman falló"
      return 1
    }
  fi
  ok "libfix listo (pixman en $LIBFIX/lib)"
}

crear_wrapper() {
  # wrapper: python del venv + LD_LIBRARY_PATH correcto (si hace falta libfix)
  local EXTRA_LD=""
  if [[ -f "$LIBFIX/lib/libpixman-1.so" ]]; then
    EXTRA_LD="$LIBFIX/lib"
  fi
  cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
# Wrapper generado por setup.sh — usa las libs correctas para Camoufox
export LD_LIBRARY_PATH="$EXTRA_LD\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
exec "$VENV/bin/python" "\$@"
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
  fail "Camoufox falló: $(echo "$salida" | grep -i -E "error|symbol|cannot open" | head -1)"
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
    echo "--- diagnóstico: ejecutá  $WRAPPER -c 'from camoufox.sync_api import Camoufox' ---"
    return 1
  fi
  return 1
}

verificar_sesion() {
  mkdir -p "$CONFIG_DIR"
  if [[ -s "$CONFIG_DIR/nexus_session" && -s "$CONFIG_DIR/cf_clearance" ]]; then
    ok "Cookies de sesión presentes (nexus_session + cf_clearance)"
    return 0
  fi
  info "No hay sesión de Nexus — necesitás loguearte una vez (2 minutos)."
  echo "  Opción A (recomendada):  ./vnv.sh login"
  echo "    → abre Chrome real, te logueás, captura las cookies sola"
  echo "  Opción B (manual):       ./vnv.sh config-cookies"
  echo "    → pegás la cookie 'nexusmods_session' del navegador (F12 → Application → Cookies)"
  return 1
}

# ============================== MAIN ==============================
if [[ "${1:-}" == "--chequear" ]]; then
  detectar_distro
  deps_sistema
  echo
  info "Estado:"
  [[ -x "$VENV/bin/python" ]] && ok "venv existe" || fail "venv NO existe (corré ./setup.sh)"
  [[ -x "$WRAPPER" ]] && ok "wrapper existe" || fail "wrapper NO existe"
  [[ -s "$CONFIG_DIR/nexus_session" ]] && ok "sesión Nexus OK" || fail "sin sesión Nexus"
  exit 0
fi

info "=== SETUP VNV LINUX ==="
detectar_distro
deps_sistema
crear_venv || exit 1
# si no hay wrapper aún (primera vez), crearlo sin libfix
[[ -x "$WRAPPER" ]] || crear_wrapper
if ! smoke_test; then
  fail "No se pudo arrancar Camoufox — revisá las dependencias del sistema de arriba."
  exit 1
fi
verificar_sesion || true
info "Setup completo. Siguientes pasos:"
echo "  1. (si no hay sesión)  ./vnv.sh login   o   ./vnv.sh config-cookies"
echo "  2. Descargar mods:      ./vnv.sh update"
echo "  3. Instalar:            ./vnv.sh install"
