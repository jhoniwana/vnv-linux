#!/usr/bin/env python3
"""Importador automático de mods a MO2 (Mod Organizer 2) para FNV.

Convierte los archivos descargados (downloads/) en el formato que MO2 entiende:
  mods/<NombreMod>/      ← mod descomprimido (raíces corregidas + meta.ini)
  profiles/Default/      ← modlist.txt, loadorder.txt, plugins.txt

Correcciones frente a la versión anterior (bug del "flatten"):
  * Una carpeta raíz que ya es carpeta de datos (meshes/, sound/, NVSE/, ...) ya NO se
    aplana.
  * Una carpeta raíz "Data/" (o "data/") se PROMUEVE (su contenido sube al mod root).
  * Una carpeta raíz que no es de datos (nvse_6_4_8/, el wrapper del archivo) se aplana.
  * Se normaliza la caja a los nombres válidos del checker de FNV (p.ej. "NVSE"→"nvse",
    "Shaders"→"shaders"), porque el checker de MO2 (falloutnvmoddatachecker.h) es
    case-sensitive y usvfs hace matching case-insensitive en tiempo de ejecución.
  * Se escribe meta.ini con installationFile= y validated=true para los mods que quedan
    sin contenido válido (el flag "No valid game data" depende de !isValid() && !m_Validated).

Motor FOMOD genérico (MO2 GamebryoScriptExtender semantics):
  * requiredInstallFiles + installSteps (visibility por <visible>, grupos por tipo
    SelectExactlyOne/SelectAtMostOne/SelectAny, <conditionFlags>, <dependencies>) +
    conditionalFileInstalls (flagDependency/fileDependency).
  * Mapa de elección explícito FOMOD_CHOICES por (mod_id) → {(step, group): [opciones]}.
    Las elecciones NO marcadas usan el default de MO2 (primera opción en
    SelectExactlyOne, ninguna en SelectAny/SelectAtMostOne).

Uso:
    importar_mo2.py                     # importa al MO2 detectado
    importar_mo2.py --dir ~/mo2-test    # otro directorio (pruebas)
    importar_mo2.py --solo 81933        # un solo mod
    importar_mo2.py --reinstalar        # borra y reimporta todo
    importar_mo2.py --verificar         # solo comprueba raíces de mods/ ya importados
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

BASE = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = BASE / "manifest.json"
DEST = BASE / "downloads"

MO2_CANDIDATOS = [
    pathlib.Path.home() / ".local/share/modorganizer2",
    pathlib.Path.home() / ".modorganizer2",
]

BASURA = {"__MACOSX", ".DS_Store", "Thumbs.db", "desktop.ini"}

# Carpetas válidas del checker de FNV (falloutnvmoddatachecker.h). Compare
# case-sensitive; en tiempo de ejecución usvfs iguala sin importar la caja.
FNV_FOLDERS = {
    "fonts", "interface", "menus", "meshes", "music", "scripts", "shaders",
    "sound", "strings", "textures", "trees", "video", "facegen", "materials",
    "nvse", "distantlod", "asi", "Tools", "MCM", "distantland", "mits",
    "dllplugins", "CalienteTools", "shadersfx", "config", "KEYWORDS",
    "BaseObjectSwapper", "RaceMenuPresets", "Devkit",
}
FNV_FOLDERS_LOWER = {f.lower() for f in FNV_FOLDERS}
FNV_EXTS = {"esp", "esm", "esl", "bsa", "ba2", "modgroups", "ini"}

# Mods "Root": se instalan en el directorio del juego (no a través de MO2).
# En MO2 quedan importados pero desactivados (-) y con validated=true.
ROOT_MODS = {62552, 65854, 67883, 81281, 92289}

# Elecciones FOMOD explícitas: mod_id -> {(nombreStep, nombreGroup): [opciones]}
# Lo no marcado usa el default de MO2 (primera opción en SelectExactlyOne, nada en
# SelectAny/SelectAtMostOne). Para ISA solo se marca el patch de YUP (instrucción
# de la guía: "1. Yukichigai's Unofficial Patch, 2. Install"); el resto de pasos
# (NVAO/kNVSE/weapon replacers) queda sin seleccionar y se ocultan solos.
FOMOD_CHOICES = {
    81933: {
        ("Iron Sights Aligned Options", "Additional Patches"):
            ["Yukichigai's Unofficial Patch"],
    },
    82042: {
        ("Setup", "Plugin Version"): ["FNV Ultimate Edition"],
        ("Environment Masks", "Real Time Reflections"): ["Real Time Reflections"],
        ("Protectron Domes", "Enable Transparency"): ["Enable Transparency"],
    },
    83425: {
        ("Game", "Game Selection"): ["FNV"],
        ("FNV Patches", "Patch Selection"): ["YUP Patch"],
    },
}

# Esms base (siempre en el loadorder) + plugins de la guía (files/loadorder.txt)
# filtrados a los mods que instalamos. El loadorder se filtra por los plugins que
# realmente se importaron (los que falten, p.ej. YUPDate.esm, se omiten).
BASE_ESMS = [
    "FalloutNV.esm", "DeadMoney.esm", "HonestHearts.esm", "OldWorldBlues.esm",
    "LonesomeRoad.esm", "GunRunnersArsenal.esm", "ClassicPack.esm",
    "MercenaryPack.esm", "TribalPack.esm", "CaravanPack.esm",
]
GUIAS_PLUGINS = [
    "YUP - Base Game + All DLC.esm",
    "YUPDate.esm",
    "Unofficial Patch NVSE Plus.esp",
    "NVMIM.esp",
    "NVMIM - YUP Patch.esp",
    "NVMIM - YUPDate Patch.esp",
    "fixy crap ue.esp",
    "Strip Lights Region Fix.esm",
    "Landscape Texture Improvements.esm",
    "Landscape Texture Improvements - YUP Patch.esm",
    "Landscape Disposition Fix.esm",
    "Placement Fixes.esm",
    "FNV FaceGen Fix.esp",
]

# Orden de display del modlist (arriba = mayor prioridad). En la guía se instalan
# primero los Utilities (quedan abajo) y al final los de Base Finish (arriba).
ORDEN_SECCIONES = {"setup": 0, "utilities": 1, "bugfix": 2, "basefinish": 3, "finish": 4}
NOMBRE_SECCION = {
    "setup": "Setup", "utilities": "Utilities", "bugfix": "Bug Fixes",
    "basefinish": "Base Finish", "finish": "Finish",
}
SECCIONES_DISPLAY = ["basefinish", "bugfix", "utilities"]


def descomprimir(archivo, destino):
    """Descomprime un archivo (7z/zip/rar) en destino. Devuelve True si pudo."""
    destino.mkdir(parents=True, exist_ok=True)
    if str(archivo).lower().endswith(".zip"):
        with zipfile_abrir(archivo) as z:
            for m in z.infolist():
                if m.is_dir():
                    continue
                nombre = m.filename.replace("\\", "/")
                if nombre.startswith("/") or ".." in nombre.split("/"):
                    continue
                out = destino / nombre
                out.parent.mkdir(parents=True, exist_ok=True)
                with z.open(m) as src, open(out, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        return True
    cmd = shutil.which("7z") or shutil.which("7za") or shutil.which("7zr")
    if not cmd:
        return False
    r = subprocess.run([cmd, "x", str(archivo), f"-o{destino}", "-y"],
                       capture_output=True, text=True)
    return r.returncode == 0


def zipfile_abrir(archivo):
    import zipfile
    return zipfile.ZipFile(archivo)


def limpiar_basura(mod_dir):
    """Quita basura (__MACOSX, .DS_Store, archivos ._*) y carpetas vacías."""
    for p in list(mod_dir.rglob("*")):
        if p.name in BASURA or p.name.startswith("._"):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
    for p in sorted(mod_dir.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()


def promover_data(mod_dir):
    """Promueve una carpeta top-level Data/ (su contenido sube al mod root)."""
    for p in list(mod_dir.iterdir()):
        if p.is_dir() and p.name.lower() == "data" and p.name != ".metadata":
            for q in list(p.iterdir()):
                shutil.move(str(q), str(mod_dir / q.name))
            p.rmdir()
            return True
    return False


def normalizar_case(mod_dir):
    """Renombra carpetas top-level a la caja canónica del checker de FNV."""
    canon = {f.lower(): f for f in FNV_FOLDERS}
    for p in list(mod_dir.iterdir()):
        if not p.is_dir() or p.name == ".metadata":
            continue
        c = canon.get(p.name.lower())
        if not c or c == p.name:
            continue
        dest = mod_dir / c
        if not dest.exists():
            p.rename(dest)
        else:
            for q in list(p.iterdir()):
                d2 = dest / q.name
                if d2.exists():
                    if q.is_dir() and d2.is_dir():
                        shutil.copytree(q, d2, dirs_exist_ok=True)
                        shutil.rmtree(q, ignore_errors=True)
                    else:
                        if d2.is_dir():
                            shutil.rmtree(d2, ignore_errors=True)
                        shutil.move(str(q), str(d2))
                else:
                    shutil.move(str(q), str(d2))
            p.rmdir()


def arrumar_raizes(mod_dir):
    """Arregla la estructura de raíces del mod (sin romper carpetas de datos).

    - Limpia basura.
    - Promueve Data/ (siempre).
    - Si queda UNA sola raíz que NO es carpeta de datos (wrapper del archivo), la
      aplana. Si la única raíz ya es de datos (meshes/, sound/, ...), la conserva.
    - Normaliza la caja de los nombres de carpeta válidos.
    """
    for _ in range(4):
        limpiar_basura(mod_dir)
        if promover_data(mod_dir):
            continue
        entries = [p for p in mod_dir.iterdir() if p.name != ".metadata"]
        dirs = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]
        if len(entries) == 1 and len(dirs) == 1 and not files:
            raiz = dirs[0]
            if raiz.name.lower() in FNV_FOLDERS_LOWER:
                break
            for p in list(raiz.iterdir()):
                shutil.move(str(p), str(mod_dir / p.name))
            raiz.rmdir()
            continue
        break
    limpiar_basura(mod_dir)
    normalizar_case(mod_dir)
    limpiar_basura(mod_dir)


def tiene_contenido_valido(mod_dir):
    """Misma regla que ModDataChecker::dataLooksValid de FNV (case-insensitive)."""
    for p in mod_dir.iterdir():
        if p.name in (".metadata", "meta.ini"):
            continue
        if p.is_dir():
            if p.name.lower() in FNV_FOLDERS_LOWER:
                return True
        elif p.suffix.lower().lstrip(".") in FNV_EXTS:
            return True
    return False


def escribir_meta(mod_dir, arch, valido):
    """Escribe meta.ini. validated=true suprime el flag 'No valid game data'."""
    lines = ["[General]"]
    if arch is not None:
        lines.append(f"installationFile={arch.name}")
    if not valido:
        lines.append("validated=true")
    (mod_dir / "meta.ini").write_text("\n".join(lines) + "\n")


def norm_sep(s):
    return (s or "").replace("\\", "/").lstrip("/")


def _copiar(src, dst):
    if src.is_dir():
        if dst.exists() and not dst.is_dir():
            dst.unlink()
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.iterdir():
            _copiar(p, dst / p.name)
    else:
        if src == dst:
            return
        if dst.exists() and dst.is_dir():
            shutil.rmtree(dst, ignore_errors=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def satisfacer(nodo, flags, mod_dir):
    tag = nodo.tag
    if tag == "flagDependency":
        nombre = nodo.get("flag")
        want = nodo.get("value") or ""
        have = flags.get(nombre)
        if want == "":
            return have in (None, "")
        return have == want
    if tag == "fileDependency":
        return (mod_dir / norm_sep(nodo.get("file") or "")).exists()
    # gameDependency / versionDependency / typeDependency / fomodDependency:
    return True


def evaluar_deps(nodo, flags, mod_dir):
    op = nodo.get("operator", "And")
    hijos = list(nodo)
    if not hijos:
        return True
    if op == "Or":
        return any(satisfacer(h, flags, mod_dir) for h in hijos)
    return all(satisfacer(h, flags, mod_dir) for h in hijos)


def decodificar_fomod(path):
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-16-le", "utf-16"):
        try:
            return raw.decode(enc).lstrip("\ufeff")
        except (UnicodeDecodeError, ValueError):
            continue
    return raw.decode("latin-1")


def aplicar_fomod(mod_dir, mod_id):
    """Aplica un FOMOD. Devuelve (n_mappings, lista_errores)."""
    fomod_dir = mod_dir / "fomod"
    mc = fomod_dir / "ModuleConfig.xml"
    if not mc.exists():
        mc = fomod_dir / "ModuleConfig.txt"
    if not mc.exists():
        return 0, ["sin fomod/ModuleConfig"]

    root = ET.fromstring(decodificar_fomod(mc))
    flags = {}
    mappings = []

    def add(s, d):
        s = norm_sep(s)
        d = norm_sep(d)
        if s:
            mappings.append((s, d))

    for el in root.findall("requiredInstallFiles/file"):
        add(el.get("source"), el.get("destination"))
    for el in root.findall("requiredInstallFiles/folder"):
        add(el.get("source"), el.get("destination"))

    steps = root.find("installSteps")
    if steps is not None:
        for st in steps:
            vis = st.find("visible")
            if vis is not None:
                deps = vis.find("dependencies")
                if deps is not None and not evaluar_deps(deps, flags, mod_dir):
                    continue
            sn = st.get("name") or ""
            for g in st.findall("optionalFileGroups/group"):
                gname = g.get("name") or ""
                gtype = g.get("type") or "SelectExactlyOne"
                plugins = g.findall("plugins/plugin")
                chosen = []
                if mod_id in FOMOD_CHOICES and (sn, gname) in FOMOD_CHOICES[mod_id]:
                    chosen = FOMOD_CHOICES[mod_id][(sn, gname)]
                elif gtype == "SelectExactlyOne" and plugins:
                    chosen = [plugins[0].get("name")]
                for pname in chosen:
                    pl = next((p for p in plugins if p.get("name") == pname), None)
                    if pl is None:
                        print(f"      ⚠ opción '{pname}' no existe en '{sn}'/'{gname}'")
                        continue
                    dep = pl.find("dependencies")
                    if dep is not None and not evaluar_deps(dep, flags, mod_dir):
                        continue
                    for fl in pl.findall("conditionFlags/flag"):
                        flags[fl.get("name")] = (fl.text or "").strip()
                    for el in pl.findall("files/file"):
                        add(el.get("source"), el.get("destination"))
                    for el in pl.findall("files/folder"):
                        add(el.get("source"), el.get("destination"))

    cond = root.find("conditionalFileInstalls")
    if cond is not None:
        for pat in cond.findall("patterns/pattern"):
            deps = pat.find("dependencies")
            if deps is not None and not evaluar_deps(deps, flags, mod_dir):
                continue
            for el in pat.findall("files/file"):
                add(el.get("source"), el.get("destination"))
            for el in pat.findall("files/folder"):
                add(el.get("source"), el.get("destination"))

    errores = []
    covered = set()
    for s, d in mappings:
        src = mod_dir / s
        if not src.exists():
            errores.append(s)
            continue
        if src.is_dir():
            dst = mod_dir / d if d else mod_dir
            _copiar(src, dst)
        else:
            dst = mod_dir / d if d else mod_dir / src.name
            _copiar(src, dst)
        if not d:
            if src.is_dir():
                for child in src.iterdir():
                    covered.add(child.name.lower())
            else:
                covered.add(src.name.lower())
        elif s == d:
            covered.add(norm_sep(s).split("/")[0].lower())
        else:
            covered.add(norm_sep(d).split("/")[0].lower())

    # limpieza: quitar fomod/ y toda raíz no seleccionada por el FOMOD
    shutil.rmtree(fomod_dir, ignore_errors=True)
    for p in list(mod_dir.iterdir()):
        if p.name in (".metadata", "overwrite"):
            continue
        if p.name.lower() not in covered:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
    arrumar_raizes(mod_dir)
    return len(mappings), errores


def recoger_plugins(mod_dir):
    res = []
    if mod_dir.is_dir():
        for p in mod_dir.iterdir():
            if p.is_file() and p.suffix.lower().lstrip(".") in ("esp", "esm", "esl"):
                res.append(p.name)
    return res


def nombre_mod(m):
    return re.sub(r'[\\/:*?"<>|]+', "_", (m.get("nombre") or f"mod-{m['mod_id']}").strip())


def importar(mo2_dir, args):
    mods = json.load(open(MANIFEST))
    if args.solo:
        mods = [m for m in mods if m["mod_id"] == args.solo]
    mods = [m for m in mods if m.get("file_id")]
    mods_ord = sorted(mods, key=lambda m: ORDEN_SECCIONES.get(m.get("seccion"), 9))

    mods_dir = mo2_dir / "mods"
    profile_dir = mo2_dir / "profiles" / "Default"
    mods_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    if args.reinstalar and mods_dir.exists():
        for p in mods_dir.iterdir():
            if p.is_dir() and not p.name.endswith("_separator"):
                shutil.rmtree(p, ignore_errors=True)

    ok, fail, plugins_orden = 0, [], []
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

        es_fomod = (mod_dir / "fomod" / "ModuleConfig.xml").exists() or \
                   (mod_dir / "fomod" / "ModuleConfig.txt").exists()
        if es_fomod:
            n_map, errs = aplicar_fomod(mod_dir, m["mod_id"])
            if errs:
                print(f"  ⚠ {nombre[:50]} FOMOD: faltan {errs[:3]}")
        else:
            arrumar_raizes(mod_dir)

        valido = tiene_contenido_valido(mod_dir)
        escribir_meta(mod_dir, arch, valido)
        for p in recoger_plugins(mod_dir):
            if p not in plugins_orden:
                plugins_orden.append(p)
        ok += 1
        estado = "✔" if valido else "✘(validated)"
        print(f"  {estado} {nombre[:52]}" + ("" if valido else "  [sin contenido → validated]"), flush=True)

    # separadores + modlist (arriba = mayor prioridad)
    modlist = []
    for sec in SECCIONES_DISPLAY:
        entries = [m for m in mods_ord if m.get("seccion") == sec]
        if not entries:
            continue
        sep_name = f"{NOMBRE_SECCION[sec]}_separator"
        sep_dir = mods_dir / sep_name
        sep_dir.mkdir(exist_ok=True)
        escribir_meta(sep_dir, None, True)
        modlist.append(f"+{sep_name}")
        for m in reversed(entries):
            pref = "-" if m["mod_id"] in ROOT_MODS else "+"
            modlist.append(f"{pref}{nombre_mod(m)}")

    (profile_dir / "modlist.txt").write_text(
        "# This file was automatically generated by Mod Organizer.\n"
        + "\n".join(modlist) + "\n"
        + (f"+Fixed ESMs\n"
           if (mods_dir / "Fixed ESMs").is_dir() else ""))

    # loadorder + plugins (solo los de la guía que realmente se importaron)
    plugins_lower = {p.lower(): p for p in plugins_orden}
    loadorder = list(BASE_ESMS)
    for gp in GUIAS_PLUGINS:
        if gp.lower() in plugins_lower:
            loadorder.append(plugins_lower[gp.lower()])
    (profile_dir / "loadorder.txt").write_text("\n".join(loadorder) + "\n")
    (profile_dir / "plugins.txt").write_text(
        "\n".join(f"*{p}" for p in loadorder) + "\n")

    (mo2_dir / "profiles" / "profiles.ini").write_text(
        "[General]\ncurrent_profile=Default\n")

    print(f"\n✅ {ok}/{len(mods_ord)} mods importados a {mods_dir}")
    print(f"   modlist: {len(modlist)} líneas (separadores incluidos)")
    print(f"   loadorder: {len(loadorder)} plugins")
    if fail:
        print("   Fallos:")
        for mid, err in fail:
            print(f"     ✘ {mid}: {err}")
    return 0 if not fail else 1


def verificar(mo2_dir):
    mods_dir = mo2_dir / "mods"
    if not mods_dir.is_dir():
        print(f"no existe {mods_dir}")
        return 1
    malos = []
    for p in sorted(mods_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name.endswith("_separator"):
            continue
        valido = tiene_contenido_valido(p)
        mi = p / "meta.ini"
        validated = mi.exists() and "validated=true" in mi.read_text(errors="ignore")
        if valido:
            print(f"  ✔ {p.name[:52]}")
        elif validated:
            print(f"  ~ {p.name[:52]}  (validated)")
        else:
            print(f"  ✘ {p.name[:52]}  ¡flag probable!")
            malos.append(p.name)
    if malos:
        print(f"\n{len(malos)} mods sin contenido válido ni validated:")
        for n in malos:
            print("   ", n)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="directorio MO2")
    ap.add_argument("--solo", type=int)
    ap.add_argument("--reinstalar", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    args = ap.parse_args()

    if args.dir:
        mo2_dir = pathlib.Path(args.dir).expanduser()
    else:
        mo2_dir = next((p for p in MO2_CANDIDATOS if p.exists()), MO2_CANDIDATOS[0])
        if not mo2_dir.exists():
            mo2_dir.mkdir(parents=True, exist_ok=True)

    if args.verificar:
        sys.exit(verificar(mo2_dir))
    print(f"📦 Importando a MO2: {mo2_dir}")
    sys.exit(importar(mo2_dir, args))


if __name__ == "__main__":
    main()
