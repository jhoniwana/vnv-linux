#!/usr/bin/env python3
"""Manifest updater: checks the latest version of each mod on Nexus.

Usage:
    export NEXUS_API_KEY="your-key"
    ./scripts/actualizar.py            # checks the 54 mods (slow: rate limits)
    ./scripts/actualizar.py --solo 57174   # checks one

For each mod it updates: name, file_id (if the version changed) and leaves the
checksum pending until the next download. It also generates mods/actualizados.md
with the change report.
"""
import argparse, json, os, pathlib, sys, time, urllib.request
from datetime import datetime

API = "https://api.nexusmods.com/v1/games/newvegas/mods"
ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"

def get_mod(mod_id, api_key):
    req = urllib.request.Request(f"{API}/{mod_id}.json", headers={"apikey": api_key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def get_files(mod_id, api_key):
    req = urllib.request.Request(f"{API}/{mod_id}/files.json", headers={"apikey": api_key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", type=int, help="only one mod_id")
    args = ap.parse_args()

    api_key = os.environ.get("NEXUS_API_KEY")
    if not api_key:
        sys.exit("❌ Missing NEXUS_API_KEY")

    mods = json.load(open(MANIFEST))
    todos = mods  # keep a reference to the FULL list (fix bug --solo)
    if args.solo:
        mods = [m for m in mods if m["mod_id"] == args.solo]

    cambios = []
    for i, m in enumerate(mods, 1):
        mid = m["mod_id"]
        print(f"[{i}/{len(mods)}] mod {mid}...", flush=True)
        try:
            info = get_mod(mid, api_key)
            nombre = info.get("name", "")
            version = info.get("version", "")
            if nombre and nombre != m.get("nombre"):
                cambios.append(f"  {mid}: name -> {nombre}")
                m["nombre"] = nombre
            m["version"] = version

            files = get_files(mid, api_key)
            mains = [f for f in files.get("files", []) if f.get("category_name") == "MAIN"]
            if mains:
                ultimo = max(mains, key=lambda f: f.get("uploaded_timestamp") or 0)
                fid = ultimo.get("file_id")
                if fid != m.get("file_id"):
                    cambios.append(f"  {mid}: file_id -> {fid} ({ultimo.get('version', '?')})")
                    m["file_id"] = fid
        except Exception as e:
            print(f"    ✘ {type(e).__name__}: {str(e)[:90]}")
        time.sleep(5)

    json.dump(todos, open(MANIFEST, "w"), indent=2)
    if cambios:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        reporte = ROOT / "mods" / "actualizados.md"
        with open(reporte, "a") as f:
            f.write(f"## {fecha}\n")
            f.write("\n".join(cambios) + "\n\n")
        print(f"\n📝 {len(cambios)} changes -> {reporte}")
    else:
        print("\n✅ All up to date.")

if __name__ == "__main__":
    main()
