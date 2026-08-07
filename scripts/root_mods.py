#!/usr/bin/env python3
"""Installs the root mods into the game directory (the "root mods" step of the VNV guide).

Root mods = the ones that go DIRECTLY into the game directory (not into MO2's VFS).
In MO2 they are disabled on purpose (importar_mo2.py marks them with '-').

Each step delegates to its native Linux port (repos/):
  xnvse   → repos/xnvse-linux/port.py
  4gb     → repos/fnv-4gb-patch-linux/port.py
  epic    → repos/epic-games-patcher-linux/port.py (no-op on Steam: detects LAA already applied)
  uefix   → repos/ue-esm-fixes-linux/port.py (mod "Fixed ESMs")
  all     → xnvse + 4gb + uefix (epic is a no-op on Steam)

NOTE: 'bsa' (the FNV BSA Decompressor) was REMOVED from the automatic order on
2026-08-07: it is a no-op on the current depot (the 11 target BSAs ship raw) and
HARMFUL on the zlib ones (Meshes.bsa/Misc.bsa decompressed → 32-bit game crashes
at startup with "File not found"). Historical root cause of the broken walls /
startup crashes: every `install`/`root` run re-decompressed Meshes+Misc.
Keep it available only via `--solo bsa` for research.

No Wine/Proton: everything runs natively on Linux.
"""
from __future__ import annotations

import argparse
import os
import struct
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
]
EXTRA_LIBRARY = os.environ.get("VNV_STEAM_LIBRARY")
if EXTRA_LIBRARY:
    STEAM_LIBRARIES.append(Path(EXTRA_LIBRARY))

PASOS = {
    "xnvse": REPOS / "xnvse-linux" / "port.py",
    "4gb": REPOS / "fnv-4gb-patch-linux" / "port.py",
    "epic": REPOS / "epic-games-patcher-linux" / "port.py",
    "bsa": REPOS / "fnv-bsa-decompressor-linux" / "decompress.py",  # research-only (--solo bsa)
    "uefix": REPOS / "ue-esm-fixes-linux" / "port.py",
}
# bsa intentionally NOT in the automatic order — see module docstring.
ORDEN = ["xnvse", "4gb", "epic", "uefix"]


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


def verificar_paso(paso, game_dir, mo2_dir):
    """Verificación POST-paso: comprueba el resultado REAL (no solo el rc).

    Returns (ok: bool, detalle: str). Cada port define aquí su prueba de oro.
    """
    try:
        if paso == "xnvse":
            dlls = ["nvse_1_4.dll", "nvse_steam_loader.dll", "nvse_loader.exe"]
            faltan = [d for d in dlls if not (game_dir / d).exists()]
            return (not faltan), f"NVSE DLLs: {', '.join(faltan) or 'todas presentes'}"
        if paso == "4gb":
            exe = (game_dir / "FalloutNV.exe").read_bytes()
            if exe[:2] != b"MZ":
                return False, "FalloutNV.exe no es un PE válido"
            pe_off = struct.unpack("<I", exe[0x3C:0x40])[0]
            chars = struct.unpack("<H", exe[pe_off + 22: pe_off + 24])[0]
            laa = bool(chars & 0x20)
            return laa, f"LAA: {'0xA620 aplicado' if laa else 'NO aplicado (chars=%#x)' % chars}"
        if paso == "epic":
            return True, "no-op en Steam (LAA ya aplicado)"
        if paso == "uefix":
            fixed = mo2_dir / "mods" / "Fixed ESMs"
            esms = ["FalloutNV.esm", "DeadMoney.esm", "HonestHearts.esm",
                    "OldWorldBlues.esm", "LonesomeRoad.esm", "GunRunnersArsenal.esm"]
            faltan = [e for e in esms if not (fixed / e).exists()]
            notes4 = [e for e in esms if (fixed / e).exists() and (fixed / e).read_bytes()[:4] != b"TES4"]
            if faltan or notes4:
                return False, f"esms: faltan {faltan or '—'}, no-TES4 {notes4 or '—'}"
            return True, "6/6 esms TES4 válidos"
        if paso == "bsa":
            return True, "research-only (no parte del orden automático)"
    except Exception as e:
        return False, f"verificación falló: {e}"
    return True, "sin verificación definida"


FALLBACKS = {
    # paso: comandos de re-ejecución si la verificación falla (una sola vez)
    "xnvse": ["--solo", "xnvse"],
    "4gb": ["--solo", "4gb"],
    "uefix": ["--solo", "uefix"],  # el propio port re-aplica con --force vía root_mods
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dir")
    ap.add_argument("--mo2-dir", default=str(Path.home() / ".local/share/modorganizer2"))
    ap.add_argument("--solo", choices=list(PASOS))
    args = ap.parse_args()

    game_dir = Path(args.game_dir) if args.game_dir else buscar_juego()
    if game_dir is None:
        return fail("game not found — edit STEAM_LIBRARIES or install it in Steam")
    mo2_dir = Path(args.mo2_dir)
    fixed = mo2_dir / "mods" / "Fixed ESMs"

    print(f"Game:  {game_dir}")
    print(f"MO2:   {mo2_dir}")

    pasos = [args.solo] if args.solo else ORDEN
    for p in pasos:
        script = PASOS[p]
        if not script.exists():
            return fail(f"missing port {script}")
        cmd = [str(PY), str(script), "--game-dir", str(game_dir)]
        if p == "uefix":
            cmd += ["--dest", str(fixed)]
        info(f"== step {p}: {script.name} ==")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            return fail(f"step {p} failed (rc={r.returncode})")
        ok(f"step {p} completed")
        # --- verificación post-paso + fallback ---
        vok, det = verificar_paso(p, game_dir, mo2_dir)
        if vok:
            ok(f"verify {p}: {det}")
            continue
        info(f"verify {p} FAILED: {det} — reintentando ({p})...")
        r = subprocess.run([str(PY), str(script), "--game-dir", str(game_dir)]
                           + (["--dest", str(fixed)] if p == "uefix" else [])
                           + (["--force"] if p == "uefix" else []))
        if r.returncode != 0:
            return fail(f"fallback step {p} failed (rc={r.returncode})")
        vok, det = verificar_paso(p, game_dir, mo2_dir)
        if not vok:
            return fail(f"verify {p} failed even after retry: {det} — "
                        f"run 'steam steam://validate/22380' then './vnv.sh install' again")
        ok(f"verify {p} (tras fallback): {det}")

    if "uefix" in pasos and fixed.exists():
        modlist = mo2_dir / "profiles" / "Default" / "modlist.txt"
        if modlist.exists() and "+Fixed ESMs" not in modlist.read_text():
            with open(modlist, "a") as f:
                f.write("+Fixed ESMs\n")
            ok("mod 'Fixed ESMs' enabled in modlist.txt")
    ok("Root mods ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
