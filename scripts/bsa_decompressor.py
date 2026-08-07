#!/usr/bin/env python3
"""FNV BSA Decompressor - Linux port (CORREGIDO).

Layout real del BSA v105 FO3/FNV (según xEdit wbBSArchive.pas):
  Header(36) | Folder Records (fc x 16) |
  por folder: [u8 nameLen][folder name][file records: count x 16] |
  File Names ([u8 len][name] x filc, NUL... ) | Data

Semántica de compresión (xEdit):
  ARCHIVE_COMPRESS   = 0x0004  (flag del header: compresión por defecto)
  FILE_SIZE_COMPRESS = 0x40000000 (bit 30 del file size: archivo comprimido)
  Un archivo está comprimido si:  bit30 XOR (header & 0x04)
  (si el header declara compresión por defecto, bit30 = INVERTIDO)

Bug corregido: el port anterior usaba 0x100 como flag de compresión y
escribía los datos crudos SIEMPRE con bit 30. En los BSA de FNV (flags 0x100
sin 0x04) el juego interpreta bit30 = comprimido -> intenta zlib sobre datos
crudos -> texturas rosas y meshes con "!". Ahora la lógica es la de xEdit.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import zlib
from pathlib import Path

GAME_DIR_NAME = "Fallout New Vegas"
STEAM_LIBRARIES = [
    Path.home() / ".steam/steam/steamapps",
    Path.home() / ".local/share/Steam/steamapps",
]
EXTRA_LIBRARY = os.environ.get("VNV_STEAM_LIBRARY")
if EXTRA_LIBRARY:
    STEAM_LIBRARIES.append(Path(EXTRA_LIBRARY))

ARCHIVE_COMPRESS = 0x0004          # flag del header (xEdit)
FILE_SIZE_COMPRESS = 0x40000000    # bit 30 del file size (xEdit)
SIZE_MASK = 0x3FFFFFFF
# máscara para decidir si un BSA "tiene compresión" (procesable)
HAS_COMPRESSION = 0x04 | 0x100
POLY = 0x42F0E1EBA9EA3693


def info(msg):
    print(f"  i {msg}", flush=True)


def ok(msg):
    print(f"  + {msg}", flush=True)


def fail(msg, code=1):
    print(f"  ! {msg}", flush=True)
    return code


def crc64(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (POLY if crc & 1 else 0)
    return crc & 0xFFFFFFFFFFFFFFFF


def parse_bsa(data: bytes):
    magic, ver, fro_off, ffo, fc, filc, fnl, fln, flags = struct.unpack(
        "<4sIIIIIIII", data[:36])
    assert magic == b"BSA\x00", f"not a BSA: {magic}"
    folders = []
    for i in range(fc):
        h, n, _ = struct.unpack("<QII", data[fro_off + i * 16: fro_off + (i + 1) * 16])
        folders.append((h, n))
    # layout FO3/FNV: por folder -> [len][name] + file records
    records = []
    pos = fro_off + fc * 16
    folder_names = []
    for _, n in folders:
        ln = data[pos]
        folder_names.append(data[pos + 1:pos + 1 + ln].decode("utf-8", "replace"))
        pos += 1 + ln
        for _ in range(n):
            fh, sz, off = struct.unpack("<QII", data[pos:pos + 16])
            records.append((fh, sz, off))
            pos += 16
    # file names
    file_names = []
    for _ in range(filc):
        ln = data[pos]
        file_names.append(data[pos + 1:pos + 1 + ln].decode("utf-8", "replace"))
        pos += 1 + ln
    data_off = pos
    assert len(records) == filc
    return dict(version=ver, flags=flags, folders=folders, records=records,
                folder_names=folder_names, file_names=file_names,
                data_off=data_off)


def file_compressed(sz: int, flags: int) -> bool:
    """Lógica xEdit: comprimido = bit30 XOR (header & 0x04)."""
    bit30 = bool(sz & FILE_SIZE_COMPRESS)
    default_compressed = bool(flags & ARCHIVE_COMPRESS)
    return bit30 != default_compressed


def read_file(data: bytes, rec, flags: int) -> bytes:
    """Devuelve los bytes crudos (descomprimidos) del archivo."""
    fh, sz, off = rec
    if sz == 0:
        return b""
    size = sz & SIZE_MASK
    blob = data[off:off + size]
    if file_compressed(sz, flags) and len(blob) >= 4:
        # [u32 uncompressed size][zlib]
        usize = struct.unpack("<I", blob[:4])[0]
        if 0 < usize <= 0x3FFFFFFF:
            try:
                return zlib.decompress(blob[4:])
            except zlib.error:
                return blob
    return blob


def rewrite(data: bytes, bsa: dict) -> bytes:
    """Reescribe el BSA con todos los archivos en crudo (layout FO3/FNV)."""
    out = bytearray(data[:36])  # header intacto (flags incluidos)
    # folder records
    for h, n in bsa["folders"]:
        out += struct.pack("<QII", h, n, 0)
    # file records con nuevos size/offset
    blob_off = bsa["data_off"]
    new_records = []
    for fh, sz, off in bsa["records"]:
        raw = read_file(data, (fh, sz, off), bsa["flags"])
        size = len(raw)
        if bsa["flags"] & ARCHIVE_COMPRESS:
            size |= FILE_SIZE_COMPRESS   # invertir el default comprimido
        new_records.append((fh, size, blob_off))
        blob_off += len(raw)
    # por folder: [len][name] + file records nuevos
    ri = 0
    for idx_f, (_, n) in enumerate(bsa["folders"]):
        fname = bsa["folder_names"][idx_f]
        b = fname.encode("utf-8")
        out += bytes([len(b)]) + b
        for _ in range(n):
            fh, size, off = new_records[ri]
            out += struct.pack("<QII", fh, size, off)
            ri += 1
    # file names
    for name in bsa["file_names"]:
        b = name.encode("utf-8")
        out += bytes([len(b)]) + b
    # data cruda
    for fh, sz, off in bsa["records"]:
        out += read_file(data, (fh, sz, off), bsa["flags"])
    return bytes(out)


def verify_names(bsa: dict) -> tuple:
    """Verifica CRC64 de los nombres vs los hashes del índice (prueba de oro)."""
    okc = 0
    total = 0
    fi = 0
    for fi_folder, (_, n) in enumerate(bsa["folders"]):
        fname = bsa["folder_names"][fi_folder] if fi_folder < len(bsa["folder_names"]) else ""
        for _ in range(n):
            if fi < len(bsa["records"]) and fi < len(bsa["file_names"]):
                fh, _, _ = bsa["records"][fi]
                nombre = bsa["file_names"][fi]
                cand = [f"{fname}\\{nombre}", nombre]
                if any(crc64(c.lower().encode()) == fh for c in cand):
                    okc += 1
                total += 1
            fi += 1
    return okc, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bsa", nargs="*", help="files to decompress")
    ap.add_argument("--game-dir")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="solo verificar hashes, no escribir")
    args = ap.parse_args()

    game_dir = Path(args.game_dir) if args.game_dir else None
    if game_dir is None:
        for lib in STEAM_LIBRARIES:
            cand = lib / "common" / GAME_DIR_NAME
            if (cand / "FalloutNV.exe").exists():
                game_dir = cand
                break
    if game_dir is None:
        return fail("game not found - use --game-dir")

    if args.bsa:
        files = [Path(a) for a in args.bsa]
    else:
        files = sorted((game_dir / "Data").glob("*.bsa"))
    total = 0
    for p in files:
        data = p.read_bytes()
        try:
            bsa = parse_bsa(data)
        except AssertionError as e:
            info(f"{p.name}: {e} - skipping")
            continue
        if args.verify:
            okc, tot = verify_names(bsa)
            estado = "OK" if okc == tot and tot > 0 else "HASHES MAL"
            print(f"  {p.name}: hashes {okc}/{tot} {estado}")
            continue
        if not (bsa["flags"] & HAS_COMPRESSION):
            ok(f"{p.name}: sin compresión (flags={bsa['flags']:#x}) - skipping")
            continue
        before = p.stat().st_size
        new_data = rewrite(data, bsa)
        if args.dry_run:
            info(f"{p.name}: {before:,} -> {len(new_data):,} bytes (dry-run)")
        else:
            p.write_bytes(new_data)
            ok(f"{p.name}: {before:,} -> {len(new_data):,} bytes")
        total += 1
    ok(f"Done: {total} BSA files processed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
