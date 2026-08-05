#!/usr/bin/env python3
"""Login automático a Nexus Mods y captura de la cookie `sid`.

Patrón Wabbajack: se abre una ventana de Chrome REAL y el usuario se loguea
él mismo (el script NUNCA ve ni guarda la contraseña — así funcionan 2FA,
captcha y Cloudflare). Al detectar el login, se extrae la cookie `sid` y se
guarda local con permisos 600.

Uso:
    ./scripts/login_nexus.py            # abre ventana y espera tu login
    ./scripts/login_nexus.py --timeout 120   # espera hasta 2 min

Requiere: python3 + playwright (pip install playwright) y Chrome instalado.
"""
import argparse, json, pathlib, sys, time
from playwright.sync_api import sync_playwright

CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SID_FILE = CONFIG_DIR / "nexus_sid"
LOGIN_URL = "https://users.nexusmods.com/auth/sign-in"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def detectar_login(page):
    """True cuando la sesión de Nexus quedó iniciada."""
    # indicadores: texto de cuenta logueada en el header
    try:
        body = page.locator("body").inner_text(timeout=2500)
        if "Log out" in body or "Sign out" in body or "My profile" in body:
            return True
    except Exception:
        pass
    # o URL de la página de cuenta
    if "nexusmods.com/users/myaccount" in page.url:
        return True
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=180, help="segundos máx de espera (default 180)")
    args = ap.parse_args()

    # ¿hay display? si no, intentamos headless (funciona sin 2FA/captcha)
    import os
    headless = not bool(os.environ.get("DISPLAY"))

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            "/tmp/vnv-nexus-login-profile", channel="chrome", headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            user_agent=UA,
        )
        page = ctx.new_page()
        print(f"🌐 Abriendo Nexus (modo {'headless' if headless else 'ventana'} — esperando tu login hasta {args.timeout}s)...")
        page.goto(LOGIN_URL, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        logueado = False
        fin = time.time() + args.timeout
        while time.time() < fin:
            if detectar_login(page):
                logueado = True
                break
            time.sleep(2)

        if not logueado:
            # última chance: navegar al home y revisar
            try:
                page.goto("https://www.nexusmods.com", timeout=40000)
                page.wait_for_timeout(3000)
                logueado = detectar_login(page)
            except Exception:
                pass

        if not logueado:
            print("✘ No se detectó login a tiempo. Reintentá (o revisá si hay 2FA pendiente).")
            ctx.close()
            sys.exit(1)

        # extraer cookie sid
        cookies = ctx.cookies(["https://www.nexusmods.com", "https://users.nexusmods.com"])
        sid = next((c["value"] for c in cookies if c["name"] == "sid"), None)
        if not sid:
            print("✘ Logueado pero no encontré la cookie sid.")
            ctx.close()
            sys.exit(1)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(SID_FILE, "w") as f:
            f.write(sid)
        import stat
        SID_FILE.chmod(0o600)
        print(f"✔ Login OK. Cookie sid guardada en {SID_FILE} (permisos 600)")
        print("  Ahora corré: python3 scripts/descargar_nexus_cookies.py --resume")
        ctx.close()

if __name__ == "__main__":
    main()
