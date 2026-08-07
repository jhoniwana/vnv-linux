#!/usr/bin/env python3
"""Login a LoversLab + descarga de archivos (Camoufox pasa Cloudflare).

Uso:
    LL_USER="..." LL_PASS="..." ./venv/camoufox-python scripts/ll_setup.py

Descarga: Sexout Framework Assortment + Sexout Breeder a sexout-setup/descargas/
"""
import os
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
DEST = pathlib.Path.home() / "sexout-setup" / "descargas"
DEST.mkdir(parents=True, exist_ok=True)

USER = os.environ.get("LL_USER", "")
PASS = os.environ.get("LL_PASS", "")

ARCHIVOS = [
    ("Sexout Framework Assortment", "https://www.loverslab.com/files/file/18755-sexout-framework-assortment/"),
    ("Sexout Breeder", "https://www.loverslab.com/files/file/5473-sexout-breeder/"),
]


def main():
    if not USER or not PASS:
        print("✘ faltan LL_USER/LL_PASS")
        sys.exit(1)
    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True) as browser:
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # ===== LOGIN =====
        print("→ yendo al login...")
        page.goto("https://www.loverslab.com/login/", timeout=90000, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        # esperar Cloudflare si aparece
        for _ in range(12):
            try:
                body = page.locator("body").inner_text(timeout=2000)
                if "Just a moment" in body:
                    page.wait_for_timeout(5000)
                    continue
                break
            except Exception:
                page.wait_for_timeout(3000)
        # aceptar age gate si aparece ("Enter / I am 18+")
        for sel in ["input[value='Enter / I am 18+']", "button:has-text('I am 18+')", "input[value='I am 18']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500):
                    el.click(timeout=3000)
                    print("  ✔ age gate aceptado")
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                continue
        # campos del login (Invision Community: #auth + #password)
        for sel, val in [("#auth", USER), ("#password", PASS)]:
            try:
                page.locator(sel).first.fill(val, timeout=8000)
                print(f"  ✔ {sel} completado")
            except Exception as e:
                print(f"  ✘ {sel}: {str(e)[:60]}")
        # click en el botón "Sign In" específico (no el del age gate)
        try:
            page.locator("button:has-text('Sign In'), input[value='Sign In']").first.click(timeout=5000)
            print("  ✔ Sign In clickeado")
        except Exception as e:
            print(f"  ✘ Sign In: {str(e)[:60]}")
            # fallback: submit del form por JS
            try:
                page.evaluate("document.querySelector('form[action*=login]').submit()")
                print("  ✔ form submit por JS")
            except Exception:
                pass
        page.wait_for_timeout(8000)
        body = page.locator("body").inner_text(timeout=5000)
        logueado = "Sign In" not in body or USER.split("@")[0].lower() in body.lower()
        print("¿logueado?", logueado)

        # guardar cookies LL (Invision: ips4_member_id, ips4_pass_hash, ips4_session_id)
        cookies = ctx.cookies()
        ll_cookies = [c for c in cookies if "loverslab.com" in c.get("domain", "")]
        ips = {c["name"]: c["value"] for c in ll_cookies if c["name"].startswith("ips4_")}
        print("cookies ips4:", list(ips.keys()))
        cfg = pathlib.Path.home() / ".config" / "vnv-linux"
        cfg.mkdir(parents=True, exist_ok=True)
        if ips:
            (cfg / "ll_cookies.json").write_text(
                __import__("json").dumps(ips, indent=2))
            print("✔ cookies guardadas en ~/.config/vnv-linux/ll_cookies.json")

        # ===== DESCARGAS =====
        for nombre, url in ARCHIVOS:
            print(f"\n→ {nombre}: {url.split('/')[-2]}")
            page.goto(url, timeout=90000, wait_until="domcontentloaded")
            page.wait_for_timeout(7000)
            # botón de descarga (Invision: botón "Download This File" / a[data-action=download])
            dl_event = []
            page.on("download", lambda d: dl_event.append(d))
            clickeado = False
            for sel in ["a[href*='do=download']", "a[data-action='download']",
                        "span.ipsButton_primary:has-text('Download')", "a:has-text('Download This File')"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=2000):
                        el.click(timeout=5000)
                        clickeado = True
                        print("  ✔ botón Download clickeado")
                        break
                except Exception:
                    continue
            if not clickeado:
                # fallback: buscar cualquier link con do=download
                hrefs = page.locator("a[href*='do=download']").evaluate_all("els => els.map(e => e.href)")
                if hrefs:
                    page.goto(hrefs[0], timeout=90000, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)
                    print("  ✔ navegado al link directo")
            for _ in range(30):
                if dl_event:
                    break
                page.wait_for_timeout(1000)
            if dl_event:
                d = dl_event[0]
                destino = DEST / d.suggested_filename
                d.save_as(destino)
                print(f"  ✔✔ {d.suggested_filename} ({destino.stat().st_size//1024} KB)")
            else:
                print(f"  ✘ no arrancó descarga para {nombre}")
        ctx.close()


if __name__ == "__main__":
    main()
