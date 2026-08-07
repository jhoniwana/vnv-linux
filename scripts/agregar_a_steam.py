#!/usr/bin/env python3
"""Agrega la entrada "Fallout New Vegas (VNV)" a Steam como juego no-Steam,
apuntando a lanzar-mo2.sh (abre el gestor Mod Organizer desde Steam).

Edita userdata/<uid>/config/shortcuts.vdf, que es VDF binario:
  - 0x00 = mapa (clave null-terminada, contenido, fin 0x08)
  - 0x01 = string (clave null-terminada, valor null-terminado)
  - 0x02 = int32 LE (clave null-terminada, 4 bytes)

El appid de un juego no-Steam se deriva de forma determinística:
  appid = crc32(exe + nombre) | 0x80000000

REQUIERE Steam cerrado (Steam reescribe shortcuts.vdf al apagar).
Idempotente: si ya existe la entrada con el mismo Exe, la actualiza.

Uso: camoufox-python scripts/agregar_a_steam.py [--nombre N] [--exe /ruta]
     [--start-dir /ruta] [--icono /ruta] [--salida /ruta] [--force]
"""
from __future__ import annotations

import argparse
import struct
import subprocess
import zlib
from pathlib import Path

NOMBRE_DEF = "Fallout New Vegas (VNV)"


def _leer_cstr(data: bytes, off: int) -> tuple[str, int]:
    end = data.index(b"\x00", off)
    return data[off:end].decode("utf-8"), end + 1


def _parse_map(data: bytes, off: int) -> tuple[dict, int]:
    obj = {}
    while off < len(data):
        t = data[off]
        if t == 0x08:
            return obj, off + 1
        off += 1
        name, off = _leer_cstr(data, off)
        if t == 0x00:
            val, off = _parse_map(data, off)
        elif t == 0x01:
            val, off = _leer_cstr(data, off)
        elif t == 0x02:
            val = struct.unpack_from("<I", data, off)[0]
            off += 4
        else:
            raise ValueError(f"tipo VDF desconocido 0x{t:02x}")
        obj[name] = val
    return obj, off


def parse(data: bytes) -> dict:
    obj, off = _parse_map(data, 0)
    if off != len(data):
        raise ValueError(f"sobran {len(data) - off} bytes")
    return obj


def _enc(name: str, val) -> bytes:
    nb = name.encode("utf-8")
    if isinstance(val, dict):
        body = b"".join(_enc(k, v) for k, v in val.items())
        return b"\x00" + nb + b"\x00" + body + b"\x08"
    if isinstance(val, str):
        return b"\x01" + nb + b"\x00" + val.encode("utf-8") + b"\x00"
    if isinstance(val, int):
        return b"\x02" + nb + b"\x00" + struct.pack("<I", val & 0xFFFFFFFF)
    raise TypeError(f"valor inválido para '{name}': {type(val)}")


def encode(root: dict) -> bytes:
    out = b"".join(_enc(k, v) for k, v in root.items())
    return out + b"\x08"


def appid(exe: str, nombre: str) -> int:
    return zlib.crc32((exe + nombre).encode("utf-8")) | 0x80000000


def steam_dir() -> Path:
    for cand in (Path.home() / ".local/share/Steam", Path.home() / ".steam/steam"):
        if cand.is_dir():
            return cand
    raise SystemExit("No encontré la carpeta de Steam (~/.local/share/Steam o ~/.steam/steam)")


def shortcuts_path() -> Path:
    sd = steam_dir()
    users = sorted((sd / "userdata").glob("*/config")) if (sd / "userdata").is_dir() else []
    if not users:
        raise SystemExit(f"No hay userdata en {sd}/userdata")
    return users[-1] / "shortcuts.vdf"


def steam_corriendo() -> bool:
    try:
        return subprocess.run(
            ["pgrep", "-f", "steamwebhelper"], capture_output=True
        ).returncode == 0
    except FileNotFoundError:
        return False


def shortcut(exe: str, nombre: str, start_dir: str, icono: str) -> dict:
    return {
        "appid": appid(exe, nombre),
        "AppName": nombre,
        "Exe": exe,
        "StartDir": start_dir,
        "icon": icono,
        "ShortcutPath": "",
        "LaunchOptions": "",
        "IsHidden": 0,
        "AllowDesktopConfig": 1,
        "AllowOverlay": 1,
        "OpenVR": 0,
        "Devkit": 0,
        "DevkitGameID": "",
        "DevkitOverrideAppID": 0,
        "LastPlayTime": 0,
        "FlatpakAppID": "",
        "sortas": "",
        "tags": {},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default=NOMBRE_DEF)
    ap.add_argument("--exe", default=str(Path(__file__).resolve().parent.parent / "lanzar-mo2.sh"))
    ap.add_argument("--start-dir", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--icono", default=str(Path(__file__).resolve().parent.parent / "assets" / "gecko.png"))
    ap.add_argument("--salida")  # path alternativo (testing)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not Path(args.exe).expanduser().is_file():
        raise SystemExit(f"No existe el ejecutable: {args.exe}")

    # Steam guarda Exe/StartDir con comillas; el appid se deriva de la forma con comillas.
    exe = f'"{args.exe}"'
    start_dir = f'"{args.start_dir}"'

    path = Path(args.salida) if args.salida else shortcuts_path()
    if not args.salida and steam_corriendo() and not args.force:
        raise SystemExit(
            "Steam está corriendo — cerrá Steam (Steam → Salir) y volvé a correr el "
            "comando. Steam reescribe shortcuts.vdf al apagar y pisaría el cambio.\n"
            "Si sabés lo que hacés: --force (se escribe igual)."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raiz = parse(path.read_bytes())
    else:
        raiz = {}

    # root: {"shortcuts": {indice: shortcut}}
    scs = raiz.get("shortcuts") or {}
    if not isinstance(scs, dict):
        scs = {}

    nuevo = shortcut(exe, args.nombre, start_dir, args.icono)
    for key, sc in list(scs.items()):
        if isinstance(sc, dict) and sc.get("Exe") == exe:
            scs[key] = nuevo
            print(f"Entrada existente actualizada (índice {key}).")
            break
    else:
        idx = str(max((int(k) for k in scs if str(k).isdigit()), default=-1) + 1)
        scs[idx] = nuevo
        print(f"Entrada nueva agregada (índice {idx}).")

    raiz = {"shortcuts": scs}

    if path.exists():
        path.with_suffix(".vdf.bak").write_bytes(path.read_bytes())
    tmp = path.with_suffix(".vdf.tmp")
    tmp.write_bytes(encode(raiz))

    # validación round-trip
    verif = parse(tmp.read_bytes())
    sc = verif["shortcuts"][idx if "idx" in locals() else str(list(scs.keys())[-1])]
    assert sc["Exe"] == exe, "round-trip falló"
    tmp.replace(path)
    print(f"OK: {path}")
    print(f"  AppName: {sc['AppName']}")
    print(f"  Exe:     {sc['Exe']}")
    print(f"  appid:   {sc['appid']}  (0x{sc['appid']:08X})")
    print("Reiniciá Steam y la entrada 'Fallout New Vegas (VNV)' aparecerá en la biblioteca.")


if __name__ == "__main__":
    main()
