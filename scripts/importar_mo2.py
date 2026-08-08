#!/usr/bin/env python3
"""Automatic importer of mods into MO2 (Mod Organizer 2) for FNV.

Converts the downloaded files (downloads/) into the format MO2 understands:
  mods/<ModName>/        <- extracted mod (fixed roots + meta.ini)
  profiles/Default/      <- modlist.txt, loadorder.txt, plugins.txt

Fixes vs the previous version (the "flatten" bug):
  * A root folder that is already a data folder (meshes/, sound/, NVSE/, ...) is
    NO longer flattened.
  * A root "Data/" folder (or "data/") is PROMOTED (its contents go up to the
    mod root).
  * A root folder that is not data (nvse_6_4_8/, the archive wrapper) is flattened.
  * The case is normalized to the valid names of the FNV checker (e.g.
    "NVSE"->"nvse", "Shaders"->"shaders"), because the MO2 checker
    (falloutnvmoddatachecker.h) is case-sensitive and usvfs matches
    case-insensitively at runtime.
  * meta.ini is written with installationFile= and validated=true for the mods
    left without valid content (the "No valid game data" flag depends on
    !isValid() && !m_Validated).

Generic FOMOD engine (MO2 GamebryoScriptExtender semantics):
  * requiredInstallFiles + installSteps (visibility via <visible>, groups by
    type SelectExactlyOne/SelectAtMostOne/SelectAny, <conditionFlags>,
    <dependencies>) + conditionalFileInstalls (flagDependency/fileDependency).
  * Explicit choice map FOMOD_CHOICES by (mod_id) -> {(step, group): [options]}.
    Unmarked choices use the MO2 default (first option in SelectExactlyOne, none
    in SelectAny/SelectAtMostOne).

Usage:
    importar_mo2.py                     # import into the detected MO2
    importar_mo2.py --dir ~/mo2-test    # another directory (testing)
    importar_mo2.py --solo 81933        # a single mod
    importar_mo2.py --reinstalar        # wipe and reimport everything
    importar_mo2.py --verificar         # only check the roots of already-imported mods/
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

# Valid folders of the FNV checker (falloutnvmoddatachecker.h). It compares
# case-sensitive; at runtime usvfs matches regardless of case.
FNV_FOLDERS = {
    "fonts", "interface", "menus", "meshes", "music", "scripts", "shaders",
    "sound", "strings", "textures", "trees", "video", "facegen", "materials",
    "nvse", "distantlod", "asi", "Tools", "MCM", "distantland", "mits",
    "dllplugins", "CalienteTools", "shadersfx", "config", "KEYWORDS",
    "BaseObjectSwapper", "RaceMenuPresets", "Devkit",
}
FNV_FOLDERS_LOWER = {f.lower() for f in FNV_FOLDERS}
FNV_EXTS = {"esp", "esm", "esl", "bsa", "ba2", "modgroups", "ini"}

# "Root" mods: installed into the game directory (not through MO2).
# In MO2 they stay imported but disabled (-) and with validated=true.
ROOT_MODS = {62552, 65854, 67883, 81281, 92289}

# Explicit FOMOD choices: mod_id -> {(stepName, groupName): [options]}
# Unmarked items use the MO2 default (first option in SelectExactlyOne, none in
# SelectAny/SelectAtMostOne). For ISA only the YUP patch is marked (guide
# instruction: "1. Yukichigai's Unofficial Patch, 2. Install"); the remaining
# steps (NVAO/kNVSE/weapon replacers) stay unselected and hide themselves.
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

# Base esms (always in the loadorder) + guide plugins (files/loadorder.txt)
# filtered to the mods we install. The loadorder is filtered by the plugins that
# were actually imported (missing ones, e.g. YUPDate.esm, are omitted).
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
    "FNV FaceGen Fix.esp",
    "Strip Lights Region Fix.esm",
    "Landscape Disposition Fix.esm",
    "Landscape Texture Improvements.esm",
    "Landscape Texture Improvements - YUP Patch.esm",
    "fixy crap ue.esp",
    "Placement Fixes.esm",
]

# Display order of the modlist (top = highest priority). In the guide the
# Utilities are installed first (stay at the bottom) and Base Finish last (top).
ORDEN_SECCIONES = {"setup": 0, "utilities": 1, "bugfix": 2, "basefinish": 3, "finish": 4}
NOMBRE_SECCION = {
    "setup": "Setup", "utilities": "Utilities", "bugfix": "Bug Fixes",
    "basefinish": "Base Finish", "finish": "Finish",
}
SECCIONES_DISPLAY = ["basefinish", "bugfix", "utilities"]


def descomprimir(archivo, destino):
    """Extracts an archive (7z/zip/rar) into dest. Returns True if it could."""
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
    """Removes junk (__MACOSX, .DS_Store, ._* files) and empty folders."""
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
    """Promotes a top-level Data/ folder (its contents go up to the mod root)."""
    for p in list(mod_dir.iterdir()):
        if p.is_dir() and p.name.lower() == "data" and p.name != ".metadata":
            for q in list(p.iterdir()):
                shutil.move(str(q), str(mod_dir / q.name))
            p.rmdir()
            return True
    return False


def normalizar_case(mod_dir):
    """Renames top-level folders to the canonical case of the FNV checker."""
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
    """Fixes the root structure of the mod (without breaking data folders).

    - Cleans junk.
    - Promotes Data/ (always).
    - If only ONE root remains that is NOT a data folder (archive wrapper), it
      is flattened. If the only root is already data (meshes/, sound/, ...), it
      is kept.
    - Normalizes the case of valid folder names.
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
    """Same rule as ModDataChecker::dataLooksValid from FNV (case-insensitive)."""
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
    """Writes meta.ini. validated=true suppresses the 'No valid game data' flag."""
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
    """Applies a FOMOD. Returns (n_mappings, error_list)."""
    fomod_dir = mod_dir / "fomod"
    mc = fomod_dir / "ModuleConfig.xml"
    if not mc.exists():
        mc = fomod_dir / "ModuleConfig.txt"
    if not mc.exists():
        return 0, ["no fomod/ModuleConfig"]

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
                        print(f"      [WARN] option '{pname}' does not exist in '{sn}'/'{gname}'")
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

    # cleanup: remove fomod/ and every root not selected by the FOMOD
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


def resolver_archivo(est, m):
    """Resolves the main file of a mod (preferably via estado.json)."""
    extras_archivos = {est.get(k, {}).get("archivo")
                       for k, v in est.items() if ":" in k}
    def es_archivo_main(p):
        # the main CANNOT be the file of an extra (historical crossed states)
        return p.exists() and p.name not in extras_archivos
    info = est.get(str(m["mod_id"]))
    if info and info.get("archivo"):
        p = DEST / info["archivo"]
        if es_archivo_main(p):
            return p
    def coincide(p):
        n = p.name
        return f"-{m['mod_id']}-" in n or f" {m['mod_id']} " in n or n.startswith(f"{m['mod_id']}-")
    cand = [p for p in sorted(DEST.glob(f"*{m['mod_id']}*")) if es_archivo_main(p) and coincide(p)]
    if cand:
        return cand[-1]  # the most recent by name (timestamp)
    # last resort: any matching file
    cand = sorted(DEST.glob(f"*{m['mod_id']}*"))
    return cand[-1] if cand else None


def resolver_extra(est, m, x):
    """Resolves the file of an extra (file_id or url) via estado.json."""
    if x.get("file_id"):
        key = f"{m['mod_id']}:{x['file_id']}"
    else:
        key = f"{m['mod_id']}:url:{x['nombre']}"
    info = est.get(key, {})
    nombre = info.get("archivo")
    if not nombre:
        return None
    p = DEST / nombre
    return p if p.exists() else None


def fusionar_extras(mod_dir, m, est):
    """Merges the extra files (INIs, esps, dlls) into the mod folder."""
    for x in (m.get("extra") or []):
        arch = resolver_extra(est, m, x)
        if not arch:
            print(f"      [WARN] extra no downloaded file: {x['nombre']}")
            continue
        tmp = mod_dir / ".extra_tmp"
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
        if not descomprimir(arch, tmp):
            print(f"      [WARN] could not extract extra: {x['nombre']}")
            continue
        arrumar_raizes(tmp)
        for p in tmp.iterdir():
            _copiar(p, mod_dir / p.name)
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"      + extra {x['nombre']}: {arch.name[:55]}")


def importar(mo2_dir, args):
    todos = json.load(open(MANIFEST))
    mods = todos
    if args.solo:
        mods = [m for m in mods if m["mod_id"] == args.solo]
    mods = [m for m in mods if m.get("file_id")]
    mods_ord = sorted(mods, key=lambda m: ORDEN_SECCIONES.get(m.get("seccion"), 9))
    # with --solo only that mod is (re)extracted, but the profile lists are
    # ALWAYS regenerated with the full manifest (otherwise MO2 sees the other
    # mods as "new" and disables them: the profile gets corrupted).
    lista_mods = [m for m in todos if m.get("file_id")]

    mods_dir = mo2_dir / "mods"
    profile_dir = mo2_dir / "profiles" / "Default"
    mods_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)

    if args.reinstalar and mods_dir.exists():
        for p in mods_dir.iterdir():
            if p.is_dir() and not p.name.endswith("_separator"):
                shutil.rmtree(p, ignore_errors=True)

    ok, fail, plugins_orden = 0, [], []
    est = {}
    if (BASE / "estado.json").exists():
        est = json.load(open(BASE / "estado.json"))
    for m in mods_ord:
        arch = resolver_archivo(est, m)
        if not arch:
            fail.append((m["mod_id"], "no downloaded file"))
            continue
        nombre = nombre_mod(m)
        mod_dir = mods_dir / nombre
        if mod_dir.exists():
            shutil.rmtree(mod_dir, ignore_errors=True)
        if not descomprimir(arch, mod_dir):
            fail.append((m["mod_id"], f"could not extract {arch.name[:40]}"))
            continue

        es_fomod = (mod_dir / "fomod" / "ModuleConfig.xml").exists() or \
                   (mod_dir / "fomod" / "ModuleConfig.txt").exists()
        if es_fomod:
            n_map, errs = aplicar_fomod(mod_dir, m["mod_id"])
            if errs:
                print(f"  [WARN] {nombre[:50]} FOMOD: missing {errs[:3]}")
        else:
            arrumar_raizes(mod_dir)

        fusionar_extras(mod_dir, m, est)
        normalizar_case(mod_dir)

        # JAM (66666): el preset oficial de VNV apaga el sprint (JVSEnabled=0);
        # the user asked for sprint ON - force it after each import (re-imports
        # re-extract the preset and would revert it).
        if m["mod_id"] == 66666:
            jam_ini = mod_dir / "config" / "JustMods.ini"
            if jam_ini.exists():
                txt = jam_ini.read_text(errors="ignore")
                if "JVSEnabled=0" in txt:
                    jam_ini.write_text(txt.replace("JVSEnabled=0", "JVSEnabled=1"))
                    print("  + JAM: sprint enabled (JVSEnabled=1)")

        valido = tiene_contenido_valido(mod_dir)
        escribir_meta(mod_dir, arch, valido)
        for p in recoger_plugins(mod_dir):
            if p not in plugins_orden:
                plugins_orden.append(p)
        ok += 1
        estado = "[OK]" if valido else "[FAIL](validated)"
        print(f"  {estado} {nombre[:52]}" + ("" if valido else "  [no content -> validated]"), flush=True)

    # separators + modlist (top = highest priority)
    # NOTE: preserve the +/- state of the CURRENT modlist (MO2 and manual
    # toggles are lost if everything is rewritten; e.g. "Fixed ESMs" disabled
    # manually used to get re-enabled on every re-import --solo).
    estado_previo = {}
    modlist_prev = profile_dir / "modlist.txt"
    if modlist_prev.exists():
        for l in modlist_prev.read_text(errors="ignore").splitlines():
            l = l.strip()
            if l.startswith(("+", "-")) and not l.endswith("_separator"):
                estado_previo[l[1:].strip()] = l[0]
    modlist = []
    for sec in SECCIONES_DISPLAY:
        entries = [m for m in lista_mods if m.get("seccion") == sec]
        if not entries:
            continue
        sep_name = f"{NOMBRE_SECCION[sec]}_separator"
        sep_dir = mods_dir / sep_name
        sep_dir.mkdir(exist_ok=True)
        escribir_meta(sep_dir, None, True)
        modlist.append(f"+{sep_name}")
        for m in reversed(entries):
            nombre = nombre_mod(m)
            pref = "-" if m["mod_id"] in ROOT_MODS else "+"
            pref = estado_previo.get(nombre, pref)
            modlist.append(f"{pref}{nombre}")
    fixed = "+Fixed ESMs" if (mods_dir / "Fixed ESMs").is_dir() else None
    if fixed:
        fixed = estado_previo.get("Fixed ESMs", "+") + "Fixed ESMs"
        modlist.append(fixed)

    (profile_dir / "modlist.txt").write_text(
        "# This file was automatically generated by Mod Organizer.\n"
        + "\n".join(modlist) + "\n")

    # loadorder + plugins (only the guide ones that were actually imported).
    # NOTE: MO2 2.5.2 NO LONGER uses the '*' marker in plugins.txt (the file is
    # the list of ACTIVE plugins without asterisk; loadorder.txt keeps the order).
    # A plugins.txt with '*' makes MO2 not recognize ANY plugin
    # ("Plugin not found: *FalloutNV.esm"). Same CRLF header MO2 writes.
    plugins_lower = {p.lower(): p for p in plugins_orden}
    loadorder = list(BASE_ESMS)
    for gp in GUIAS_PLUGINS:
        if gp.lower() in plugins_lower:
            loadorder.append(plugins_lower[gp.lower()])
    # mods outside the guide (JAM, d20Fixes, etc.): preserved from the previous
    # loadorder and appended at the end (the guide: own mods go last).
    if (profile_dir / "loadorder.txt").exists():
        prev = [p.strip("\r") for p in
                (profile_dir / "loadorder.txt").read_text(errors="ignore").splitlines()
                if p.strip() and not p.startswith("#")]
        conocidos = {x.lower() for x in loadorder}
        for p in prev:
            if p.lower() not in conocidos:
                loadorder.append(p)
                conocidos.add(p.lower())
    # with --solo: the profile already has the full loadorder (the other mods
    # are imported). Do NOT rebuild from scratch: preserve the EXACT previous
    # order and only INSERT the new plugins of the imported mod (after their
    # master).
    if args.solo and (profile_dir / "loadorder.txt").exists():
        prev = [p.strip("\r") for p in
                (profile_dir / "loadorder.txt").read_text(errors="ignore").splitlines()
                if p.strip() and not p.startswith("#")]
        if prev:
            loadorder = prev
        for nuevo in [p for p in plugins_orden if p.lower() not in
                      [x.lower() for x in loadorder]]:
            # insert after the master (first esm of the plugin) or at the end
            master = next((m for m in BASE_ESMS if m.lower() == nuevo.lower()), None)
            pos = len(loadorder)
            for i, p in enumerate(loadorder):
                if p.lower() == nuevo.lower():
                    pos = None
                    break
            if pos is not None:
                for m in BASE_ESMS:
                    if m.lower() in nuevo.lower() and m.lower() != nuevo.lower():
                        master = m
                        break
                if master and master in loadorder:
                    pos = loadorder.index(master) + 1
                loadorder.insert(pos, nuevo)
    cabecera = "# This file was automatically generated by Mod Organizer.\r\n"
    (profile_dir / "loadorder.txt").write_text(cabecera + "\r\n".join(loadorder) + "\r\n")
    (profile_dir / "plugins.txt").write_text(cabecera + "\r\n".join(loadorder) + "\r\n")

    (mo2_dir / "profiles" / "profiles.ini").write_text(
        "[General]\ncurrent_profile=Default\n")

    print(f"\n[OK] {ok}/{len(mods_ord)} mods imported to {mods_dir}")
    print(f"   modlist: {len(modlist)} lines (separators included)")
    print(f"   loadorder: {len(loadorder)} plugins")
    if fail:
        print("   Failures:")
        for mid, err in fail:
            print(f"     [FAIL] {mid}: {err}")
    return 0 if not fail else 1


def verificar(mo2_dir):
    mods_dir = mo2_dir / "mods"
    if not mods_dir.is_dir():
        print(f"does not exist: {mods_dir}")
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
            print(f"  [OK] {p.name[:52]}")
        elif validated:
            print(f"  ~ {p.name[:52]}  (validated)")
        else:
            print(f"  [FAIL] {p.name[:52]}  likely flag!")
            malos.append(p.name)
    if malos:
        print(f"\n{len(malos)} mods with no valid content nor validated:")
        for n in malos:
            print("   ", n)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="MO2 directory")
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
    print(f"[PKG] Importing to MO2: {mo2_dir}")
    sys.exit(importar(mo2_dir, args))


if __name__ == "__main__":
    main()
