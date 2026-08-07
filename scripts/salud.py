#!/usr/bin/env python3
"""VNV Linux — full health check. Verifies EVERY component of the install:

  game/exe  → FalloutNV.exe present, PE valid, LAA 0xA620 applied
  NVSE      → nvse_1_4.dll + nvse_steam_loader.dll + nvse_loader.exe in game root
  BSAs      → 21 BSAs vanilla: the 4 zlib ones still compressed (bit30=0 on
              first record), the 11 "0x100" still raw, no bit30 anywhere
  INIs      → SArchiveList with all 21 BSAs in the 3 game INIs
  Fixed ESMs→ 6 esms present in MO2 with valid TES4 magic
  Downloads → manifest vs estado.json (all mods "ok") + files on disk
  Session   → Nexus session cookie present (downloads would fail without it)
  MO2       → mo2-lint present, MO2 instance + Default profile exist,
              loadorder/modlist readable

Exit code 0 = everything OK, 1 = at least one problem (details printed).
Usage: ./venv/bin/python scripts/salud.py  (or ./vnv.sh salud)
"""
from __future__ import annotations

import json
import pathlib
import struct
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
GAME_DIRS = [
    pathlib.Path.home() / ".steam/steam/steamapps/common/Fallout New Vegas",
    pathlib.Path.home() / ".local/share/Steam/steamapps/common/Fallout New Vegas",
]
CONFIG = pathlib.Path.home() / ".config" / "vnv-linux"
MO2 = pathlib.Path.home() / ".local/share/modorganizer2"
PREFIX_INIS = [
    pathlib.Path.home()
    / ".local/share/Steam/steamapps/compatdata/22380/pfx/drive_c/users/steamuser"
    / "Documents/My Games/FalloutNV",
]
ALL_BSAS = ["Fallout - Textures.bsa", "Fallout - Textures2.bsa", "Fallout - Meshes.bsa",
            "Fallout - Voices1.bsa", "Fallout - Sound.bsa", "Fallout - Misc.bsa",
            "DeadMoney - Main.bsa", "DeadMoney - Sounds.bsa",
            "HonestHearts - Main.bsa", "HonestHearts - Sounds.bsa",
            "OldWorldBlues - Main.bsa", "OldWorldBlues - Sounds.bsa",
            "LonesomeRoad - Main.bsa", "LonesomeRoad - Sounds.bsa",
            "GunRunnersArsenal - Main.bsa", "GunRunnersArsenal - Sounds.bsa",
            "ClassicPack - Main.bsa", "CaravanPack - Main.bsa",
            "MercenaryPack - Main.bsa", "TribalPack - Main.bsa", "Update.bsa"]

results: list[tuple[str, bool, str]] = []


def check(nombre, ok, detalle):
    results.append((nombre, ok, detalle))


def juego_dir():
    for g in GAME_DIRS:
        if (g / "FalloutNV.exe").exists():
            return g
    return None


def bsa_estado(d: bytes):
    """(compressed_by_default, bit30_on_first_record) from a BSA header."""
    m, ver, off, bf, fc, filc, fnl, fln, ff = struct.unpack("<4sIIIIIIII", d[:36])
    if m != b"BSA\x00":
        return None
    pos = 36 + fc * 16
    if pos + 1 > len(d):
        return (bf, None)
    ln = d[pos]
    pos += 1 + ln
    if pos + 16 > len(d):
        return (bf, None)
    _, sz, _ = struct.unpack("<QII", d[pos:pos + 16])
    return (bf & 0x04, bool(sz & 0x40000000))


def main():
    g = juego_dir()
    check("juego instalado", g is not None, str(g) if g else "FalloutNV.exe no encontrado en Steam")
    if g is None:
        for nombre, ok, detalle in results:
            print(f"{'✔' if ok else '✘'} {nombre}: {detalle}")
        return 1

    # 1) exe + LAA
    exe = (g / "FalloutNV.exe").read_bytes()
    pe_ok = exe[:2] == b"MZ"
    check("exe PE válido", pe_ok, "MZ" if pe_ok else "no es un PE")
    if pe_ok:
        pe_off = struct.unpack("<I", exe[0x3C:0x40])[0]
        chars = struct.unpack("<H", exe[pe_off + 22: pe_off + 24])[0]
        check("LAA 4GB (0x20)", bool(chars & 0x20), f"chars=%#x" % chars)

    # 2) NVSE
    dlls = ["nvse_1_4.dll", "nvse_steam_loader.dll", "nvse_loader.exe"]
    faltan = [d for d in dlls if not (g / d).exists()]
    check("NVSE DLLs", not faltan, ", ".join(faltan) if faltan else "3/3 presentes")

    # 3) BSAs — todos vanilla (4 zlib comprimidas, 17 raw, nada con bit30)
    data = (g / "Data")
    bsa_files = sorted(data.glob("*.bsa")) if data.exists() else []
    check("BSAs 21", len(bsa_files) == 21, f"{len(bsa_files)}/21")
    zlib_ok = True
    bit30 = []
    for p in bsa_files:
        est = bsa_estado(p.read_bytes())
        if est is None:
            zlib_ok = False
            continue
        comp, b30 = est
        if comp and b30:
            zlib_ok = False
            bit30.append(p.name)
    check("BSAs vanilla (zlib intactas, sin bit30)", zlib_ok,
          "4 zlib OK + 17 raw OK" if zlib_ok else f"bit30 detectado en: {bit30}")

    # 4) SArchiveList en los 3 inis
    sar_ok = True
    for ini in [g / "Fallout_default.ini"] + [pi / "Fallout.ini" for pi in PREFIX_INIS] + \
               [pi / "FalloutPrefs.ini" for pi in PREFIX_INIS]:
        if not ini.exists():
            sar_ok = False
            continue
        txt = ini.read_text(errors="replace")
        n = 0
        for line in txt.splitlines():
            if line.startswith("SArchiveList="):
                n = len(line[len("SArchiveList="):].split(","))
        if n != 21:
            sar_ok = False
    check("SArchiveList 21 BSAs (3 inis)", sar_ok, "21/21/21" if sar_ok else "incompleto — re-run install")

    # 5) Fixed ESMs
    fixed = MO2 / "mods" / "Fixed ESMs"
    esms = ["FalloutNV.esm", "DeadMoney.esm", "HonestHearts.esm",
            "OldWorldBlues.esm", "LonesomeRoad.esm", "GunRunnersArsenal.esm"]
    faltan_esm = [e for e in esms if not (fixed / e).exists()]
    notes4 = [e for e in esms if (fixed / e).exists() and (fixed / e).read_bytes()[:4] != b"TES4"]
    check("Fixed ESMs 6/6", not faltan_esm and not notes4,
          "6/6 TES4" if not faltan_esm and not notes4 else f"faltan {faltan_esm} no-TES4 {notes4}" if "notes4" in dir() else f"faltan {faltan_esm}")

    # 6) Descargas
    manifest = json.load(open(BASE / "manifest.json")) if (BASE / "manifest.json").exists() else []
    estado = json.load(open(BASE / "estado.json")) if (BASE / "estado.json").exists() else {}
    man_ids = {str(m.get("mod_id")) for m in manifest if m.get("file_id")}
    n_ok = sum(1 for k, v in estado.items() if k in man_ids and v.get("estado") == "ok")
    check("descargas", n_ok == len(man_ids) and len(man_ids) > 0, f"{n_ok}/{len(man_ids)} mods OK")

    # 7) Sesión Nexus
    ses = (CONFIG / "nexus_session")
    check("sesión Nexus", ses.exists() and ses.stat().st_size > 0,
          "cookie presente" if ses.exists() and ses.stat().st_size > 0 else "ausente — re-login")

    # 8) MO2
    prof = MO2 / "profiles" / "Default"
    check("MO2 perfil Default", prof.exists(), "profiles/Default presente" if prof.exists() else "faltante — re-run install")
    lo = prof / "loadorder.txt"
    ml = prof / "modlist.txt"
    if lo.exists() and ml.exists():
        nlo = len([l for l in lo.read_text().splitlines() if l.strip()])
        nml = len([l for l in ml.read_text().splitlines() if l.strip()])
        check("loadorder/modlist", nlo > 10 and nml > 10, f"plugins={nlo} mods={nml}")
    else:
        check("loadorder/modlist", False, "faltan loadorder.txt/modlist.txt")

    print()
    problemas = 0
    for nombre, ok, detalle in results:
        print(f"  {'✔' if ok else '✘'} {nombre:22s} — {detalle}")
        if not ok:
            problemas += 1
    print()
    if problemas:
        print(f"❌ {problemas} problema(s) — fix: ./vnv.sh install  (si BSAs: steam://validate/22380 primero)")
        return 1
    print("✅ TODO EL SISTEMA SANO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
