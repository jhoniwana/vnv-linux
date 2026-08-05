#!/usr/bin/env python3
"""Login a Nexus con Camoufox (Firefox anti-detección) — intenta pasar Turnstile headless.

Uso:
    NEXUS_USER="..." NEXUS_PASS="..." ./venv/bin/python scripts/login_camoufox.py

Guarda cookie sid en ~/.config/vnv-linux/nexus_sid (600).
"""
import os, pathlib, sys, time

CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SID_FILE = CONFIG_DIR / "nexus_session"   # cookie real: nexusmods_session (antes 'sid')
CF_FILE = CONFIG_DIR / "cf_clearance"     # cookie de Cloudflare (importante para descargas)

def guardar_sid(context):
    try:
        cookies = context.cookies()
        sid = next((c["value"] for c in cookies if c["name"] == "sid"), None)
        if sid:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            SID_FILE.write_text(sid)
            SID_FILE.chmod(0o600)
            return True
    except Exception:
        pass
    return False

def main():
    user = os.environ.get("NEXUS_USER", "")
    pw = os.environ.get("NEXUS_PASS", "")
    if not user or not pw:
        sys.exit("❌ Faltan NEXUS_USER / NEXUS_PASS")

    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True) as browser:
        ctx = browser.new_context()
        page = ctx.new_page()
        print("→ Abriendo login con Camoufox (headless anti-detección)...")
        page.goto("https://users.nexusmods.com/register", timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        try:
            page.locator("a:has-text('Sign in')").first.click(timeout=5000)
            print("✔ Sign in clickeado")
        except Exception as e:
            print(f"  click err: {str(e)[:70]}")
        try:
            page.wait_for_selector("#user_login", timeout=20000)
        except Exception:
            page.goto("https://users.nexusmods.com/", timeout=45000)
            page.wait_for_selector("#user_login", timeout=20000)
        page.fill("#user_login", user)
        page.fill("#password", pw)
        print("✔ Credenciales completadas. Esperando Turnstile...")
        page.wait_for_timeout(8000)

        exito = False
        for intento in range(3):
            try:
                page.click("input[name='commit']", timeout=15000)
                print(f"→ Submit {intento+1}")
            except Exception as e:
                print(f"  submit err: {str(e)[:60]}")
            for _ in range(10):
                page.wait_for_timeout(3000)
                # 1) detectar login por la página
                try:
                    body = page.locator("body").inner_text(timeout=1500)
                    if "sign out" in body.lower() or "welcome back" in body.lower():
                        print("✔ Detectado: página de cuenta logueada")
                        # extraer cookies: nexusmods_session (sesión) + cf_clearance (Cloudflare)
                        cookies = ctx.cookies()
                        for c in cookies:
                            if c["name"] == "nexusmods_session":
                                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                                SID_FILE.write_text(c["value"])
                                SID_FILE.chmod(0o600)
                                print(f"✔ nexusmods_session guardada → {SID_FILE}")
                                exito = True
                            elif c["name"] == "cf_clearance":
                                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                                CF_FILE.write_text(c["value"])
                                CF_FILE.chmod(0o600)
                                print(f"✔ cf_clearance guardada → {CF_FILE}")
                        if exito:
                            break
                except Exception:
                    pass
                if exito:
                    break
                # si aparece checkbox de Turnstile en iframe, clickearlo
                for fr in page.frames:
                    if "turnstile" in fr.url or "challenges.cloudflare" in fr.url:
                        try:
                            cb = fr.locator("input[type='checkbox'], .ctp-checkbox-label").first
                            if cb.is_visible(timeout=1500):
                                cb.click(timeout=2000)
                                print("   → checkbox Turnstile clickeado")
                        except Exception:
                            pass
            if exito:
                break

        if exito:
            print(f"✔ ¡LOGIN OK CON CAMOUFOX! sid guardada en {SID_FILE}")
            print("  Siguiente: python3 scripts/descargar_nexus_cookies.py --resume")
        else:
            try:
                body = page.locator("body").inner_text(timeout=3000)[:250]
                print("✘ No detecté la cookie. Estado:", body.replace("\n", " | ")[:200])
            except Exception:
                print("✘ No detecté la cookie.")
        ctx.close()

if __name__ == "__main__":
    main()
