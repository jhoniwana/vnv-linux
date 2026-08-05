#!/usr/bin/env python3
"""Descargador MASIVO de mods Nexus (cuenta FREE) — flujo /Download/ real.

Descubrimiento: https://www.nexusmods.com/Download/?id={file_id}&game_id=130&source=ModPage
muestra la página de descarga con botón "Download" (junto a "served via CDN").
Click → descarga el archivo real. Funciona para cuentas gratis.

Uso:
    LD_LIBRARY_PATH=/home/shot/xvfb-env/lib ./venv/bin/python scripts/descargar_browser.py [--seccion utilities|bugfix] [--solo MOD_ID] [--resume]
"""
import argparse
import json
import os
import pathlib
import random
import sys
import time

SITE = "https://www.nexusmods.com"
GAME_ID = "130"  # Fallout New Vegas
BASE = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = BASE / "manifest.json"
DEST = BASE / "downloads"
CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seccion", help="solo esa sección del manifest")
    ap.add_argument("--solo", type=int, help="solo ese mod_id")
    ap.add_argument("--resume", action="store_true", help="saltar archivos ya descargados")
    args = ap.parse_args()

    mods = json.load(open(MANIFEST))
    if args.seccion:
        mods = [m for m in mods if m["seccion"] == args.seccion]
    if args.solo:
        mods = [m for m in mods if m["mod_id"] == args.solo]
    mods = [m for m in mods if m.get("file_id")]  # solo los que tienen file_id
    DEST.mkdir(exist_ok=True)

    print(f"🎯 {len(mods)} mods a descargar")
    ok, fail = 0, []

    from camoufox.sync_api import Camoufox

    cookies_extra = []
    for name, f in [("nexusmods_session", "nexus_session"), ("cf_clearance", "cf_clearance")]:
        p = CONFIG_DIR / f
        if p.exists():
            cookies_extra.append({"name": name, "value": p.read_text().strip(),
                                  "domain": ".nexusmods.com", "path": "/"})

    with Camoufox(headless=True) as browser:
        ctx = browser.new_context(accept_downloads=True)
        if cookies_extra:
            ctx.add_cookies(cookies_extra)
            print("✔ cookies de sesión inyectadas")
        page = ctx.new_page()
        consent_done = False

        def goto_y_challenge(url):
            """goto + esperar si Cloudflare nos pone 'Just a moment...'"""
            page.goto(url, timeout=90000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            for _ in range(12):  # hasta 60s esperando que pase el challenge
                try:
                    body = page.locator("body").inner_text(timeout=2000)
                    if "Just a moment" in body or "challenge" in body.lower() and "cf" in page.url:
                        page.wait_for_timeout(5000)
                        continue
                    return True
                except Exception:
                    page.wait_for_timeout(3000)
            return False

        for i, m in enumerate(mods, 1):
            fid = m["file_id"]
            nombre = (m.get("nombre") or f"mod-{m['mod_id']}").replace("/", "-")
            # --resume: saltar si ya existe algún archivo de este mod
            if args.resume:
                existentes = [p.name for p in DEST.iterdir() if str(m["mod_id"]) in p.name]
                if existentes:
                    print(f"[{i}/{len(mods)}] ⏭ ya descargado: {existentes[0][:60]}")
                    ok += 1
                    continue
            url = f"{SITE}/Download/?id={fid}&game_id={GAME_ID}&source=ModPage"
            print(f"[{i}/{len(mods)}] mod {m['mod_id']} ({m['seccion']}) file {fid} — {nombre[:45]}", flush=True)
            exito = False
            for intento in range(3):  # hasta 3 intentos
                try:
                    if not goto_y_challenge(url):
                        raise RuntimeError("Cloudflare challenge persistente")
                    # aceptar consentimiento de cookies (solo la primera vez que aparece)
                    if not consent_done:
                        try:
                            b = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
                            if b.is_visible(timeout=2000):
                                b.click(timeout=3000)
                                consent_done = True
                                page.wait_for_timeout(3000)
                        except Exception:
                            pass
                    # click en el botón Download si existe; si no, la descarga arranca sola
                    dl_event = []
                    def on_dl(dl):
                        dl_event.append(dl)
                    page.on("download", on_dl)
                    # 1) esperar auto-download (hasta 12s)
                    for _ in range(12):
                        if dl_event:
                            break
                        page.wait_for_timeout(1000)
                    # 2) si no arrancó, clickear el botón Download (junto al texto CDN/automaticamente)
                    if not dl_event:
                        res = page.evaluate("""() => {
                            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                            let node, host = null;
                            while (node = walker.nextNode()) {
                                const t = node.textContent || '';
                                if (t.includes('served via CDN') || t.includes('should automatically begin')) {
                                    host = node.parentElement; break;
                                }
                            }
                            if (!host) return false;
                            let el = host;
                            for (let k = 0; k < 6 && el; k++) el = el.parentElement;
                            const btns = el ? el.querySelectorAll('a, button') : [];
                            for (const a of btns) {
                                if ((a.innerText || '').trim() === 'Download') { a.click(); return true; }
                            }
                            if (btns.length) { btns[0].click(); return true; }
                            return false;
                        }""")
                        if res:
                            print("    → click en Download", flush=True)
                        for _ in range(40):  # hasta 40s más
                            if dl_event:
                                break
                            page.wait_for_timeout(1000)
                    if not dl_event:
                        raise RuntimeError("no arrancó descarga")
                    d = dl_event[0]
                    destino = DEST / d.suggested_filename
                    d.save_as(destino)
                    tam = destino.stat().st_size
                    if tam < 1000 and not d.suggested_filename.endswith((".7z", ".zip", ".rar")):
                        raise RuntimeError("descarga sospechosamente chica/HTML")
                    print(f"    ✔ {d.suggested_filename[:60]} ({tam//1024} KB)", flush=True)
                    ok += 1
                    exito = True
                    break
                except Exception as e:
                    print(f"    ✘ intento {intento+1}: {type(e).__name__}: {str(e)[:90]}", flush=True)
                    time.sleep(15 * (intento + 1))  # backoff
            if not exito:
                fail.append((m["mod_id"], "3 intentos fallidos"))
            # rate limit humano (8-15s)
            time.sleep(random.uniform(8, 15))

    print(f"\n✅ {ok}/{len(mods)} descargados. Fallos: {len(fail)}")
    for mid, err in fail:
        print(f"   ✘ {mid}: {err}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
