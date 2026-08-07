#!/usr/bin/env python3
"""Core Viva New Vegas mod downloader via the Nexus API.

Usage:
    export NEXUS_API_KEY="your-personal-key"
    ./scripts/descargar_nexus.py [--solo utilities] [--resume]

The key is generated for free at: https://www.nexusmods.com/users/myaccount?tab=developer

API used:
    GET /v1/games/newvegas/mods/{id}/files/latest_link.json
    (header: apikey)  ->  returns a single-use file_id + download_link
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
    """Download link via API — PREMIUM ONLY (403 for free accounts)."""
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
    ap.add_argument("--solo", help="manifest section (utilities, bugfix...)")
    ap.add_argument("--resume", action="store_true", help="do not re-download existing files")
    args = ap.parse_args()

    # key: env var or ~/.config/vnv-linux/api_key (saved with ./vnv.sh config)
    api_key = os.environ.get("NEXUS_API_KEY")
    if not api_key:
        keyfile = pathlib.Path.home() / ".config" / "vnv-linux" / "api_key"
        if keyfile.exists():
            api_key = keyfile.read_text().strip()
    if not api_key:
        sys.exit("❌ Missing the API key. Use `./vnv.sh config` or export NEXUS_API_KEY=...")
    if not MANIFEST.exists():
        sys.exit("❌ manifest.json does not exist in the project root.")

    mods = json.load(open(MANIFEST))
    todos = mods  # keep a reference to the FULL list (fix bug --solo)
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
            print("    already downloaded, skipping")
            ok += 1
            continue
        try:
            # 1) get the file_id of the newest MAIN
            files = get_files(mid, api_key)
            mains = [f for f in files.get("files", []) if f.get("category_name") == "MAIN"]
            if not mains:
                raise RuntimeError("no MAIN files")
            ultimo = max(mains, key=lambda f: (f.get("version") or "", f.get("file_id") or 0))
            fid = ultimo["file_id"]
            print(f"    → {ultimo.get('file_name', '?')} (file_id {fid})")
            # 2) request the download link (PREMIUM ONLY)
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
        time.sleep(5)  # respect free-account rate limits

    json.dump(todos, open(MANIFEST, "w"), indent=2)
    print(f"\n✅ {ok}/{len(mods)} downloaded. Failures: {len(fail)}")
    if fail:
        print("   ⚠ If they are 403 errors: API download links require Nexus Premium.")
        print("   For free accounts, the 'slow download' flow with cookies is in development (roadmap).")
    for mid, e in fail[:8]:
        print(f"   mod {mid}: {e}")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
