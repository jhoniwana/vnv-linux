#!/usr/bin/env python3
"""Instala los mods raíz en el directorio del juego (paso "root mods" de la guía VNV).

Root mods = los que van DIRECTAMENTE al directorio del juego (no al VFS de MO2).
En MO2 quedan desactivados a propósito (importar_mo2.py les pone '-').

Cada paso delega en su port nativo Linux (repos/):
  xnvse   → repos/xnvse-linux/port.py
  4gb     → repos/fnv-4gb-patch-linux/port.py
  epic    → repos/epic-games-patcher-linux/port.py (SOLO EGS; en Steam se omite)
  bsa     → repos/fnv-bsa-decompressor-linux/decompress.py
  uefix   → repos/ue-esm-fixes-linux/port.py (mod "Fixed ESMs")
  all     → xnvse + 4gb + bsa + uefix (epic se omite en Steam)

Sin Wine/Proton: todo corre nativo en Linux.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOS = ROOT / "repos"
PY = ROOT / "venv" / "camoufox-python"

APPID = "22380"
GAME_DIR_NAME = "Fallout New Vegas"
STEAM_LIBRARIES = [
    Path.home() / ".steam/steam/steamapps",
    Path.home() / ".local/share/Steam/steamapps",
    Path("/mnt/games/steamapps"),
]

PASOS = {
    "xnvse": REPOS / "xnvse-linux" / "port.py",
    "4gb": REPOS / "fnv-4gb-patch-linux" / "port.py",
    "epic": REPOS / "epic-games-patcher-linux" / "port.py",
    "bsa": REPOS / "fnv-bsa-decompressor-linux" / "decompress.py",
    "uefix": REPOS / "ue-esm-fixes-linux" / "port.py",
}
ORDEN = ["xnvse", "4gb", "epic", "bsa", "uefix"]


def info(msg):
    print(f"  ℹ {msg}", flush=True)


def ok(msg):
    print(f"  ✔ {msg}", flush=True)


def fail(msg, code=1):
    print(f"  ✘ {msg}", flush=True)
    return code


def buscar_juego():
    for lib in STEAM_LIBRARIES:
        cand = lib / "common" / GAME_DIR_NAME
        if (cand / "FalloutNV.exe").exists():
            return cand
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dir")
    ap.add_argument("--mo2-dir", default=str(Path.home() / ".local/share/modorganizer2"))
    ap.add_argument("--solo", choices=list(PASOS))
    args = ap.parse_args()

    game_dir = Path(args.game_dir) if args.game_dir else buscar_juego()
    if game_dir is None:
        return fail("no encontré el juego — edité STEAM_LIBRARIES o instalalo en Steam")
    mo2_dir = Path(args.mo2_dir)
    fixed = mo2_dir / "mods" / "Fixed ESMs"

    print(f"Juego:  {game_dir}")
    print(f"MO2:    {mo2_dir}")

    pasos = [args.solo] if args.solo else ORDEN
    for p in pasos:
        script = PASOS[p]
        if not script.exists():
            return fail(f"falta el port {script}")
        cmd = [str(PY), str(script), "--game-dir", str(game_dir)]
        if p == "uefix":
            cmd += ["--dest", str(fixed)]
        info(f"== paso {p}: {script.name} ==")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            return fail(f"paso {p} falló (rc={r.returncode})")
        ok(f"paso {p} completado")

    if "uefix" in pasos and fixed.exists():
        modlist = mo2_dir / "profiles" / "Default" / "modlist.txt"
        if modlist.exists() and "+Fixed ESMs" not in modlist.read_text():
            with open(modlist, "a") as f:
                f.write("+Fixed ESMs\n")
            ok("mod 'Fixed ESMs' activado en modlist.txt")
    ok("Root mods listos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
