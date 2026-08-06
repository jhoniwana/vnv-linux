#!/usr/bin/env python3
"""Instala los mods raíz en el directorio del juego (paso "root mods" de la guía VNV).

Root mods = los que van DIRECTAMENTE al directorio del juego (no al VFS de MO2).
En MO2 quedan desactivados a propósito (importar_mo2.py les pone '-').

  xnvse   → copia nvse_*.dll/exe/pdb + Data/NVSE/nvse_config.ini al Root
  4gb     → copia y ejecuta FalloutNVPatcher (ELF nativo "for Proton") en el Root
  epic    → Epic Games Patcher (SOLO EGS; en Steam se omite)
  bsa     → FNV BSA Decompressor (GUI wine: Decompressor.exe en el prefix)
  uefix   → UE ESM Fixes Remastered (GUI wine: Installer.exe → mod "Fixed ESMs")
  all     → xnvse + 4gb + (bsa + uefix interactivos)

El paso no toca el VFS de MO2 salvo para crear el mod "Fixed ESMs" (uefix).
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "downloads"
PY = ROOT / "venv" / "camoufox-python"

APPID = "22380"
GAME_DIR_NAME = "Fallout New Vegas"
STEAM_LIBRARIES = [
    Path.home() / ".steam/steam/steamapps",
    Path.home() / ".local/share/Steam/steamapps",
    Path("/mnt/games/steamapps"),
]

ROOT_MODS = {
    "xnvse": 67883,
    "4gb": 62552,
    "epic": 81281,
    "uefix": 92289,
}
BSA_ID = 65854


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


def buscar_prefix():
    for lib in STEAM_LIBRARIES:
        p = lib / "compatdata" / APPID / "pfx"
        if p.exists():
            return p
    return None


def descomprimir(archivo, destino):
    destino.mkdir(parents=True, exist_ok=True)
    if archivo.name.lower().endswith(".zip"):
        zipfile.ZipFile(archivo).extractall(destino)
        return True
    cmd = shutil.which("7z") or shutil.which("7za") or shutil.which("7zr")
    if not cmd:
        return False
    r = subprocess.run([cmd, "x", str(archivo), f"-o{destino}", "-y"],
                       capture_output=True, text=True)
    return r.returncode == 0


def extraer(mod_id, donde):
    archivos = sorted(DEST.glob(f"*{mod_id}*"))
    if not archivos:
        return None, None
    arch = archivos[0]
    tmp = Path(tempfile.mkdtemp(prefix="vnv-root-"))
    if not descomprimir(arch, tmp):
        return arch, None
    return arch, tmp


def paso_xnvse(game_dir):
    arch, tmp = extraer(ROOT_MODS["xnvse"], None)
    if tmp is None:
        return fail(f"no se pudo extraer xNVSE ({arch.name if arch else 'archivo no encontrado'})")
    raiz = tmp
    for p in tmp.iterdir():
        if p.is_dir():
            raiz = p
            break
    n = 0
    for p in raiz.rglob("*"):
        if p.is_file():
            rel = p.relative_to(raiz)
            dst = game_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            n += 1
    shutil.rmtree(tmp, ignore_errors=True)
    ok(f"xNVSE: {n} archivos copiados al Root")
    return 0


def paso_4gb(game_dir):
    arch, tmp = extraer(ROOT_MODS["4gb"], None)
    if tmp is None:
        return fail(f"no se pudo extraer el 4GB Patcher ({arch.name if arch else 'no encontrado'})")
    binario = next((p for p in tmp.rglob("*") if p.name == "FalloutNVPatcher"), None)
    if binario is None:
        shutil.rmtree(tmp, ignore_errors=True)
        return fail("no está FalloutNVPatcher en el archivo 4GB")
    dst = game_dir / "FalloutNVPatcher"
    shutil.copy2(binario, dst)
    dst.chmod(0o755)
    shutil.rmtree(tmp, ignore_errors=True)
    if (game_dir / "FalloutNV_backup.exe").exists():
        ok("4GB: FalloutNV.exe ya estaba parcheado (existe backup)")
        return 0
    info("4GB: parcheando FalloutNV.exe (ELF nativo)...")
    r = subprocess.run([str(dst)], cwd=str(game_dir), capture_output=True, text=True)
    salida = (r.stdout + r.stderr).strip()
    if (game_dir / "FalloutNV_backup.exe").exists():
        ok(f"4GB: FalloutNV.exe parcheado ({salida[-60:] or 'backup creado'})")
        return 0
    return fail(f"4GB: el patcher no creó el backup. Salida: {salida[:120]}")


def paso_epic(game_dir):
    if (game_dir / "FalloutNV_backup.exe").exists():
        ok("epic: omitido — FalloutNV.exe ya está parcheado (Steam usa 4GB)")
        return 0
    info("epic: el Epic Games Patcher es SOLO para la versión EGS — no se aplica en Steam")
    return 0


def _wine(prefix, args):
    env = dict(os.environ)
    env["WINEPREFIX"] = str(prefix)
    env.setdefault("WINEDLLOVERRIDES", "")
    cmd = ["wine", *args]
    try:
        return subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None


def paso_bsa(game_dir, prefix):
    arch, tmp = extraer(BSA_ID, None)
    if tmp is None:
        return fail(f"no se pudo extraer el BSA Decompressor ({arch.name if arch else 'no encontrado'})")
    exe = next((p for p in tmp.rglob("Decompressor.exe")), None)
    if exe is None:
        shutil.rmtree(tmp, ignore_errors=True)
        return fail("no está Decompressor.exe en el archivo")
    if prefix is None:
        shutil.rmtree(tmp, ignore_errors=True)
        return fail("no hay prefix de Proton (compatdata/22380) — corré ./vnv.sh steam")
    info(f"bsa: lanzando Decompressor.exe en el prefix (wine)...")
    r = _wine(prefix, [str(exe)])
    if r is None:
        info("bsa: la GUI quedó abierta — verificá en pantalla y cerrá el programa")
        return 0
    ok("bsa: Decompressor.exe terminó")
    return 0


def paso_uefix(game_dir, prefix, mo2_dir):
    arch, tmp = extraer(ROOT_MODS["uefix"], None)
    if tmp is None:
        return fail(f"no se pudo extraer UE ESM Fixes ({arch.name if arch else 'no encontrado'})")
    exe = next((p for p in tmp.rglob("Installer.exe")), None)
    if exe is None:
        shutil.rmtree(tmp, ignore_errors=True)
        return fail("no está Installer.exe en el archivo")
    mod_dir = mo2_dir / "mods" / "Fixed ESMs"
    mod_dir.mkdir(parents=True, exist_ok=True)
    if prefix is None:
        shutil.rmtree(tmp, ignore_errors=True)
        return fail("no hay prefix de Proton (compatdata/22380) — corré ./vnv.sh steam")
    info(f"uefix: mod 'Fixed ESMs' creado en {mod_dir}")
    info(f"uefix: lanzando Installer.exe en el prefix (wine)...")
    r = _wine(prefix, [str(exe)])
    if r is None:
        info("uefix: la GUI quedó abierta — verificá en pantalla, cerrá el programa")
        return 0
    ok("uefix: Installer.exe terminó")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-dir")
    ap.add_argument("--prefix")
    ap.add_argument("--mo2-dir", default=str(Path.home() / ".local/share/modorganizer2"))
    ap.add_argument("--solo", choices=["xnvse", "4gb", "epic", "bsa", "uefix"])
    args = ap.parse_args()

    game_dir = Path(args.game_dir) if args.game_dir else buscar_juego()
    if game_dir is None:
        return fail("no encontré el juego — edité STEAM_LIBRARIES o instalalo en Steam")
    prefix = Path(args.prefix) if args.prefix else buscar_prefix()
    mo2_dir = Path(args.mo2_dir)

    print(f"Juego:  {game_dir}")
    print(f"Prefix: {prefix or '(no encontrado — los pasos wine se omiten)'}")

    pasos = ["xnvse", "4gb", "epic", "bsa", "uefix"] if not args.solo else [args.solo]
    if "bsa" in pasos and prefix is not None:
        info("bsa: la GUI de Decompressor.exe se abre en pantalla — click en 'Decompress'")
    if "uefix" in pasos and prefix is not None:
        info("uefix: la GUI de Installer.exe se abre — poné la ruta del mod 'Fixed ESMs' y click 'Install'")

    for p in pasos:
        r = {"xnvse": paso_xnvse, "4gb": paso_4gb, "epic": paso_epic,
             "bsa": paso_bsa, "uefix": paso_uefix}[p]
        rc = r(game_dir, prefix, mo2_dir) if p in ("bsa", "uefix") else r(game_dir)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
