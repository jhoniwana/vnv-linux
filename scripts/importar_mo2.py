#!/usr/bin/env python3
"""Importador automático de mods a MO2 (Mod Organizer 2).

Convierte los archivos descargados (downloads/) en el formato que MO2 entiende:
  mods/<NombreMod>/        ← mod descomprimido
  profiles/Default/modlist.txt   ← orden de carga (generado del manifest)

Uso:
    importar_mo2.py                     # detecta MO2 (o crea uno en el HOME)
    importar_mo2.py --dir ~/mo2-test    # usar otro directorio (pruebas)
    importar_mo2.py --solo 57174        # un solo mod
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

BASE = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = BASE / "manifest.json"
DEST = BASE / "downloads"

# dónde busca MO2 (mismo orden que vnv.sh)
MO2_CANDIDATOS = [
    pathlib.Path.home() / ".local/share/modorganizer2",
    pathlib.Path.home() / ".modorganizer2",
]

BASURA = {"__MACOSX", ".DS_Store", "Thumbs.db", "desktop.ini"}


def descomprimir(archivo, destino):
    """Descomprime un archivo (7z/zip/rar) en destino. Devuelve True si pudo."""
    destino.mkdir(parents=True, exist_ok=True)
    if str(archivo).lower().endswith(".zip"):
        # zip: stdlib (robusto contra rutas maliciosas)
        with zipfile.ZipFile(archivo) as z:
            for m in z.infolist():
                if m.is_dir():
                    continue
                # evitar path traversal
                nombre = m.filename.replace("\\", "/")
                if nombre.startswith("/") or ".." in nombre.split("/"):
                    continue
                out = destino / nombre
                out.parent.mkdir(parents=True, exist_ok=True)
                with z.open(m) as src, open(out, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        return True
    # 7z/rar: usar 7z del sistema
    cmd = shutil.which("7z") or shutil.which("7za") or shutil.which("7zr")
    if not cmd:
        return False
    r = subprocess.run([cmd, "x", str(archivo), f"-o{destino}", "-y"],
                       capture_output=True, text=True)
    return r.returncode == 0


def limpiar_carpeta(mod_dir):
    """Quita basura (carpetas vacías, __MACOSX) y aplana si hay una sola raíz."""
    for p in list(mod_dir.rglob("*")):
        if p.name in BASURA or p.name.startswith("._"):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
    # aplanar: si el mod vino con una única carpeta raíz, subir su contenido
    hijos = [p for p in mod_dir.iterdir() if p.name != ".metadata"]
    if len(hijos) == 1 and hijos[0].is_dir():
        raiz = hijos[0]
        for p in list(raiz.iterdir()):
            shutil.move(str(p), str(mod_dir / p.name))
        raiz.rmdir()
    # borrar carpetas vacías
    for p in sorted(mod_dir.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    # ¿quedó contenido útil?
    archivos = [p for p in mod_dir.rglob("*") if p.is_file()]
    return len(archivos) > 0


def nombre_mod(m):
    return re.sub(r'[\\/:*?"<>|]+', "_", (m.get("nombre") or f"mod-{m['mod_id']}").strip())


def importar(mo2_dir, args):
    mods = json.load(open(MANIFEST))
    if args.solo:
        mods = [m for m in mods if m["mod_id"] == args.solo]
    mods = [m for m in mods if m.get("file_id")]

    mods_dir = mo2_dir / "mods"
    profile_dir = mo2_dir / "profiles" / "Default"
    mods_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    # el orden de mods del manifest define el modlist (setup → utilities → bugfix → finish)
    ORDEN_SECCIONES = {"setup": 0, "utilities": 1, "bugfix": 2, "basefinish": 3, "finish": 4}
    mods_ord = sorted(mods, key=lambda m: ORDEN_SECCIONES.get(m.get("seccion"), 9))

    modlist = []
    ok, fail = 0, []
    for m in mods_ord:
        archivos = sorted(DEST.glob(f"*{m['mod_id']}*"))
        if not archivos:
            fail.append((m["mod_id"], "sin archivo descargado"))
            continue
        arch = archivos[0]
        nombre = nombre_mod(m)
        mod_dir = mods_dir / nombre
        if mod_dir.exists():
            shutil.rmtree(mod_dir, ignore_errors=True)
        if not descomprimir(arch, mod_dir):
            fail.append((m["mod_id"], f"no se pudo descomprimir {arch.name[:40]}"))
            continue
        if not limpiar_carpeta(mod_dir):
            shutil.rmtree(mod_dir, ignore_errors=True)
            fail.append((m["mod_id"], "mod vacío tras limpiar"))
            continue
        modlist.append(f"+{nombre}")
        ok += 1
        print(f"  ✔ {nombre[:55]}", flush=True)

    # escribir modlist.txt (orden de la guía: setup primero, finish al final)
    (profile_dir / "modlist.txt").write_text("\n".join(modlist) + "\n")
    print(f"\n✅ {ok}/{len(mods_ord)} mods importados a {mods_dir}")
    print(f"   modlist.txt escrito ({len(modlist)} mods activos)")
    if fail:
        print("   Fallos:")
        for mid, err in fail:
            print(f"     ✘ {mid}: {err}")
    return 0 if not fail else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="directorio MO2 (por defecto: detecta ~/.local/share/modorganizer2)")
    ap.add_argument("--solo", type=int)
    args = ap.parse_args()

    if args.dir:
        mo2_dir = pathlib.Path(args.dir).expanduser()
    else:
        mo2_dir = next((p for p in MO2_CANDIDATOS if p.exists()), MO2_CANDIDATOS[0])
        if not mo2_dir.exists():
            mo2_dir.mkdir(parents=True, exist_ok=True)
    print(f"📦 Importando a MO2: {mo2_dir}")
    sys.exit(importar(mo2_dir, args))


if __name__ == "__main__":
    main()
