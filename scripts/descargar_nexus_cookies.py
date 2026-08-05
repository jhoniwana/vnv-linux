#!/usr/bin/env python3
"""Descargador para CUENTAS GRATIS de Nexus: flujo 'Slow Download' con cookies.

La API de Nexus solo da links de descarga a Premium (403). Para cuentas gratis
se usa el MISMO flujo del botón "Slow Download" del sitio, automatizado con la
sesión del usuario (cookie `sid`). Es legal: tu cuenta, tus descargas.

Cómo sacar la cookie `sid`:
  1. Logueate en https://www.nexusmods.com con tu navegador
  2. F12 → Application → Cookies → https://www.nexusmods.com
  3. Copiá el valor de la cookie llamada `sid`
  4. ./vnv.sh config-cookies   (o export NEXUS_SID=...)

Uso:
    export NEXUS_SID="..."
    ./scripts/descargar_nexus_cookies.py --resume
"""
import argparse, json, os, pathlib, re, sys, time, urllib.request

SITE = "https://www.nexusmods.com"
ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"
DEST = ROOT / "downloads"
GAME_ID = 130  # newvegas en Nexus

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
    """Abre el widget DownloadPopUp y extrae el link 'Slow Download'."""
    url = f"{SITE}/Core/Libs/Common/Widgets/DownloadPopUp?id={file_id}&nmm=0&game_id={GAME_ID}"
    with open_url(url, sesion, cf) as r:
        html = r.read().decode("utf-8", "ignore")
    # el link lento suele estar en un href o en un onclick
    m = re.search(r'href="(https?://[^"]*(?:slow|download)[^"]*)"', html, re.I)
    if not m:
        # patrón alternativo: botón con data-*
        m = re.search(r'data-(?:download|slow)[^=]*="([^"]+)"', html, re.I)
    if not m:
        raise RuntimeError(f"no encontré link de descarga lenta (file {file_id}) — ¿sesión válida? {html[:200]}")
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
    ap.add_argument("--solo", help="sección del manifest")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--mod", type=int, help="solo un mod_id (pruebas)")
    args = ap.parse_args()

    # cookies de sesión guardadas por ./scripts/login_camoufox.py
    cfg = pathlib.Path.home() / ".config" / "vnv-linux"
    sesion = ""
    if (cfg / "nexus_session").exists():
        sesion = (cfg / "nexus_session").read_text().strip()
    cf = ""
    if (cfg / "cf_clearance").exists():
        cf = (cfg / "cf_clearance").read_text().strip()
    if not sesion:
        sys.exit("❌ No hay sesión. Corré primero: NEXUS_USER=... NEXUS_PASS=... ./venv/bin/python scripts/login_camoufox.py")

    mods = json.load(open(MANIFEST))
    if args.mod:
        mods = [m for m in mods if m["mod_id"] == args.mod]
    elif args.solo:
        mods = [m for m in mods if m["seccion"] == args.solo]
    DEST.mkdir(exist_ok=True)

    ok, fail = 0, []
    for i, m in enumerate(mods, 1):
        mid = m["mod_id"]
        # file_id lo deja actualizar.py; si falta, avisar
        if not m.get("file_id"):
            print(f"[{i}/{len(mods)}] mod {mid}: sin file_id — corré primero scripts/actualizar.py")
            fail.append((mid, "sin file_id"))
            continue
        nombre = (m["nombre"] or f"mod_{mid}").replace("/", "_")
        destino = DEST / f"{mid}_{nombre}.zip"
        print(f"[{i}/{len(mods)}] mod {mid} ({m['seccion']}) file {m['file_id']}")
        if args.resume and destino.exists() and destino.stat().st_size > 1000:
            print("    ya descargado, saltando")
            ok += 1
            continue
        try:
            link = download_popup(m["file_id"], sesion, cf)
            print(f"    → link: {link[:110]}")
            descargar(link, destino, sesion, cf)
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"    ✘ HTTP {e.code}")
            fail.append((mid, f"HTTP {e.code}"))
        except Exception as e:
            print(f"    ✘ {type(e).__name__}: {str(e)[:110]}")
            fail.append((mid, str(e)[:80]))
        time.sleep(8)  # espera entre descargas lentas

    print(f"\n✅ {ok}/{len(mods)} descargados. Fallos: {len(fail)}")
    for mid, e in fail[:10]:
        print(f"   mod {mid}: {e}")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
