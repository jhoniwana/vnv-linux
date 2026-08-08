#!/usr/bin/env python3
"""Downloader for FREE Nexus accounts: 'Slow Download' flow with cookies.

The Nexus API only gives download links to Premium (403). For free accounts
the SAME flow as the "Slow Download" button of the site is used, automated with
the user's session (the `sid` cookie). It is legal: your account, your downloads.

How to get the `sid` cookie:
  1. Log in to https://www.nexusmods.com with your browser
  2. F12 -> Application -> Cookies -> https://www.nexusmods.com
  3. Copy the value of the cookie called `sid`
  4. ./vnv.sh config-cookies   (or export NEXUS_SID=...)

Usage:
    export NEXUS_SID="..."
    ./scripts/descargar_nexus_cookies.py --resume
"""
import argparse, json, os, pathlib, re, sys, time, urllib.request

SITE = "https://www.nexusmods.com"
ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"
DEST = ROOT / "downloads"
GAME_ID = 130  # newvegas on Nexus

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def cookie_header(sesion, cf):
    c = f"nexusmods_session={sesion}"
    if cf:
        c += f"; cf_clearance={cf}"
    return c

def open_url(url, sesion, cf, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Cookie": cookie_header(sesion, cf),
        "Referer": SITE,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return urllib.request.urlopen(req, timeout=timeout)

def download_popup(file_id, sesion, cf):
    """Opens the DownloadPopUp widget and extracts the 'Slow Download' link."""
    url = f"{SITE}/Core/Libs/Common/Widgets/DownloadPopUp?id={file_id}&nmm=0&game_id={GAME_ID}"
    with open_url(url, sesion, cf) as r:
        html = r.read().decode("utf-8", "ignore")
    # the slow link is usually in an href or an onclick
    m = re.search(r'href="(https?://[^"]*(?:slow|download)[^"]*)"', html, re.I)
    if not m:
        # alternate pattern: button with data-*
        m = re.search(r'data-(?:download|slow)[^=]*="([^"]+)"', html, re.I)
    if not m:
        raise RuntimeError(f"could not find a slow download link (file {file_id}) — valid session? {html[:200]}")
    return m.group(1)

def descargar(url, destino, sesion, cf):
    with open_url(url, sesion, cf, timeout=600) as r:
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
                    print(f"\r    {escrito//1024//1024}MB/{total//1024//1024}MB ({escrito*100//total}%)", end="", flush=True)
        print()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="manifest section")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--mod", type=int, help="only one mod_id (testing)")
    args = ap.parse_args()

    # session cookies saved by ./scripts/login_camoufox.py
    cfg = pathlib.Path.home() / ".config" / "vnv-linux"
    sesion = ""
    if (cfg / "nexus_session").exists():
        sesion = (cfg / "nexus_session").read_text().strip()
    cf = ""
    if (cfg / "cf_clearance").exists():
        cf = (cfg / "cf_clearance").read_text().strip()
    if not sesion:
        sys.exit("[ERROR] No session. Run first: NEXUS_USER=... NEXUS_PASS=... ./venv/bin/python scripts/login_camoufox.py")

    mods = json.load(open(MANIFEST))
    if args.mod:
        mods = [m for m in mods if m["mod_id"] == args.mod]
    elif args.solo:
        mods = [m for m in mods if m["seccion"] == args.solo]
    DEST.mkdir(exist_ok=True)

    ok, fail = 0, []
    for i, m in enumerate(mods, 1):
        mid = m["mod_id"]
        # file_id is set by actualizar.py; if missing, warn
        if not m.get("file_id"):
            print(f"[{i}/{len(mods)}] mod {mid}: no file_id — run scripts/actualizar.py first")
            fail.append((mid, "no file_id"))
            continue
        nombre = (m["nombre"] or f"mod_{mid}").replace("/", "_")
        destino = DEST / f"{mid}_{nombre}.zip"
        print(f"[{i}/{len(mods)}] mod {mid} ({m['seccion']}) file {m['file_id']}")
        if args.resume and destino.exists() and destino.stat().st_size > 1000:
            print("    already downloaded, skipping")
            ok += 1
            continue
        try:
            link = download_popup(m["file_id"], sesion, cf)
            print(f"    -> link: {link[:110]}")
            descargar(link, destino, sesion, cf)
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"    [FAIL] HTTP {e.code}")
            fail.append((mid, f"HTTP {e.code}"))
        except Exception as e:
            print(f"    [FAIL] {type(e).__name__}: {str(e)[:110]}")
            fail.append((mid, str(e)[:80]))
        time.sleep(8)  # wait between slow downloads

    print(f"\n[OK] {ok}/{len(mods)} downloaded. Failures: {len(fail)}")
    for mid, e in fail[:10]:
        print(f"   mod {mid}: {e}")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
