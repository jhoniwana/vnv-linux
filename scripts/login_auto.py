#!/usr/bin/env python3
"""Login automático a Nexus Mods (flujo real: /register → Sign in → form).

Credenciales por env NEXUS_USER/NEXUS_PASS (no se guardan).
Guarda cookie sid en ~/.config/vnv-linux/nexus_sid (600).
Maneja Turnstile: si el captcha bloquea, avisa (puede requerir ventana real).
"""
import os, pathlib, sys, time
from playwright.sync_api import sync_playwright

CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SID_FILE = CONFIG_DIR / "nexus_sid"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def guardar_sid(ctx):
    cookies = ctx.cookies(["https://www.nexusmods.com", "https://users.nexusmods.com"])
    sid = next((c["value"] for c in cookies if c["name"] == "sid"), None)
    if not sid:
        return False
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SID_FILE.write_text(sid)
    SID_FILE.chmod(0o600)
    return True

def main():
    user = os.environ.get("NEXUS_USER", "")
    pw = os.environ.get("NEXUS_PASS", "")
    if not user or not pw:
        sys.exit("❌ Faltan NEXUS_USER / NEXUS_PASS")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            "/tmp/vnv-login-auto", channel="chrome", headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            user_agent=UA,
        )
        page = ctx.new_page()
        # 1) /register → click Sign in → formulario
        page.goto("https://users.nexusmods.com/register", timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        try:
            page.locator("a:has-text('Sign in')").first.click(timeout=5000)
            print("✔ Entré al formulario de login")
        except Exception:
            print("⚠ No encontré el link Sign in — intento directo")
        page.wait_for_timeout(4000)

        # 2) llenar credenciales
        try:
            page.locator("#user_login").fill(user, timeout=8000)
            page.locator("#password").fill(pw, timeout=8000)
            print("✔ Credenciales completadas")
        except Exception as e:
            print("✘ No pude llenar:", str(e)[:100])
            ctx.close(); sys.exit(1)

        # 3) submit
        try:
            page.locator("input[name='commit']").first.click(timeout=5000)
            print("✔ Submit clickeado")
        except Exception as e:
            print("⚠ Submit:", str(e)[:80])

        # 4) esperar resultado
        print("→ Esperando resultado (Turnstile puede tardar)...")
        fin = time.time() + 50
        estado = "desconocido"
        while time.time() < fin:
            page.wait_for_timeout(3000)
            try:
                body = page.locator("body").inner_text(timeout=2000)
            except Exception:
                body = ""
            b = body.lower()
            if guardar_sid(ctx):
                estado = "ok"; break
            if "verification" in b or "código" in b or "code" in b or "authenticator" in b or "2fa" in b:
                estado = "2fa"; break
            if "incorrect" in b or "invalid" in b or "wrong" in b or "doesn't match" in b:
                estado = "credenciales"; break
            if "turnstile" in b or "captcha" in b or "verify you are human" in b or "security check" in b:
                estado = "captcha"; break

        if estado == "ok":
            print(f"✔ ¡LOGIN EXITOSO! sid guardada en {SID_FILE}")
            print("  Siguiente: python3 scripts/descargar_nexus_cookies.py --resume")
        elif estado == "2fa":
            print("⚠ Nexus pide 2FA. Pegá el código:")
            codigo = input("   código: ").strip()
            try:
                el = page.locator("input[name='code'], input[type='text'], input[type='number']").first
                el.fill(codigo, timeout=4000)
                page.locator("button[type='submit'], input[type='submit']").first.click(timeout=4000)
            except Exception:
                pass
            page.wait_for_timeout(6000)
            if guardar_sid(ctx):
                print(f"✔ Login 2FA OK. sid en {SID_FILE}")
            else:
                print("✘ No completó con 2FA")
        elif estado == "captcha":
            print("✘ Cloudflare Turnstile nos pidió verificación (headless).")
            print("   Opciones: correr en modo ventana (./vnv.sh login) o sacar la cookie a mano.")
        elif estado == "credenciales":
            print("✘ Credenciales rechazadas.")
        else:
            print("✘ Resultado no detectado. Estado:")
            try:
                print("  ", page.locator("body").inner_text(timeout=3000)[:300])
            except Exception:
                pass
        ctx.close()

if __name__ == "__main__":
    main()
