#!/usr/bin/env python3
"""Descargador de mods del Core de Viva New Vegas vía API de Nexus.

Uso:
    export NEXUS_API_KEY="tu-key-personal"
    ./scripts/descargar_nexus.py [--solo utilities] [--resume]

La key se genera gratis en: https://www.nexusmods.com/users/myaccount?tab=developer

API usada:
    GET /v1/games/newvegas/mods/{id}/files/latest_link.json
    (header: apikey)  ->  devuelve file_id + download_link de un solo uso
"""
import argparse, json, os, pathlib, sys, time, urllib.request

API = "https://api.nexusmods.com/v1/games/newvegas/mods"
ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"
DEST = ROOT / "downloads"

def http(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    return urllib.request.urlopen(req, timeout=60)

def get_files(mod_id, api_key):
    req = urllib.request.Request(f"{API}/{mod_id}/files.json",
                                 headers={"apikey": api_key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def download_link(mod_id, file_id, api_key):
    """Link de descarga vía API — SOLO PREMIUM (403 para cuentas gratis)."""
    req = urllib.request.Request(f"{API}/{mod_id}/files/{file_id}/download_link.json",
                                 headers={"apikey": api_key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())["download_link"]

def descargar(url, destino, espera=8):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300) as r:
        total = int(r.headers.get("Content-Length") or 0)
        escrito = 0
        with open(destino, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                escrito += len(chunk)
                if total:
                    pct = escrito * 100 // total
                    print(f"\r    {escrito//1024//1024}MB/{total//1024//1024}MB ({pct}%)", end="", flush=True)
        print()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="sección del manifest (utilities, bugfix...)")
    ap.add_argument("--resume", action="store_true", help="no re-descargar archivos existentes")
    args = ap.parse_args()

    # key: env var o ~/.config/vnv-linux/api_key (guardada con ./vnv.sh config)
    api_key = os.environ.get("NEXUS_API_KEY")
    if not api_key:
        keyfile = pathlib.Path.home() / ".config" / "vnv-linux" / "api_key"
        if keyfile.exists():
            api_key = keyfile.read_text().strip()
    if not api_key:
        sys.exit("❌ Falta la API key. Usá `./vnv.sh config` o export NEXUS_API_KEY=...")
    if not MANIFEST.exists():
        sys.exit("❌ No existe manifest.json en la raíz del proyecto.")

    mods = json.load(open(MANIFEST))
    todos = mods  # guardamos referencia a la lista COMPLETA (fix bug --solo)
    if args.solo:
        mods = [m for m in mods if m["seccion"] == args.solo]
    DEST.mkdir(exist_ok=True)

    ok, fail = 0, []
    for i, m in enumerate(mods, 1):
        mid = m["mod_id"]
        nombre = (m["nombre"] or f"mod_{mid}").replace("/", "_")
        destino = DEST / f"{mid}_{nombre}.zip"
        print(f"[{i}/{len(mods)}] mod {mid} ({m['seccion']})")
        if args.resume and destino.exists() and destino.stat().st_size > 1000:
            print("    ya descargado, saltando")
            ok += 1
            continue
        try:
            # 1) conseguir el file_id del MAIN más nuevo
            files = get_files(mid, api_key)
            mains = [f for f in files.get("files", []) if f.get("category_name") == "MAIN"]
            if not mains:
                raise RuntimeError("sin archivos MAIN")
            ultimo = max(mains, key=lambda f: (f.get("version") or "", f.get("file_id") or 0))
            fid = ultimo["file_id"]
            print(f"    → {ultimo.get('file_name', '?')} (file_id {fid})")
            # 2) pedir link de descarga (SOLO PREMIUM)
            link = download_link(mid, fid, api_key)
            descargar(link, destino)
            m["file_id"] = fid
            ok += 1
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode()[:150]
            except Exception:
                pass
            print(f"    ✘ HTTP {e.code}: {body}")
            fail.append((mid, f"HTTP {e.code}"))
        except Exception as e:
            print(f"    ✘ {type(e).__name__}: {str(e)[:100]}")
            fail.append((mid, str(e)[:80]))
        time.sleep(5)  # respetar rate limits de cuenta gratis

    json.dump(todos, open(MANIFEST, "w"), indent=2)
    print(f"\n✅ {ok}/{len(mods)} descargados. Fallos: {len(fail)}")
    if fail:
        print("   ⚠ Si son errores 403: los links de descarga por API requieren Nexus Premium.")
        print("   Para cuentas gratis, el flujo 'slow download' con cookies está en desarrollo (roadmap).")
    for mid, e in fail[:8]:
        print(f"   mod {mid}: {e}")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
