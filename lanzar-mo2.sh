#!/usr/bin/env bash
# Acceso directo para agregar a Steam como "Non-Steam Game":
#   Steam → + Agregar un juego → Agregar un juego no Steam → seleccionar este script.
# Al hacer clic abre el gestor Mod Organizer (con los mods); desde ahí se inicia el juego.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./vnv.sh mo2
