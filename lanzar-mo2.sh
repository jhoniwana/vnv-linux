#!/usr/bin/env bash
# Shortcut to add to Steam as a "Non-Steam Game":
#   Steam → + Add a game → Add a non-Steam game → select this script.
# Clicking it opens the Mod Organizer manager (with the mods); the game is started from there.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec ./vnv.sh mo2
