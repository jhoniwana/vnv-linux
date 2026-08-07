#!/usr/bin/env python3
"""Automatic login to Nexus Mods (real flow: /register → Sign in → form).

Credentials via env NEXUS_USER/NEXUS_PASS (not saved).
Saves the sid cookie in ~/.config/vnv-linux/nexus_sid (600).
Handles Turnstile: if the captcha blocks, it warns (may require a real window).
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
        sys.exit("❌ Missing NEXUS_USER / NEXUS_PASS")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            "/tmp/vnv-login-auto", channel="chrome", headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            user_agent=UA,
        )
        page = ctx.new_page()
        # 1) /register → click Sign in → form
        page.goto("https://users.nexusmods.com/register", timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        try:
            page.locator("a:has-text('Sign in')").first.click(timeout=5000)
            print("✔ Entered the login form")
        except Exception:
            print("⚠ Could not find the Sign in link — trying directly")
        page.wait_for_timeout(4000)

        # 2) fill in credentials
        try:
            page.locator("#user_login").fill(user, timeout=8000)
            page.locator("#password").fill(pw, timeout=8000)
            print("✔ Credentials filled in")
        except Exception as e:
            print("✘ Could not fill in:", str(e)[:100])
            ctx.close(); sys.exit(1)

        # 3) submit
        try:
            page.locator("input[name='commit']").first.click(timeout=5000)
            print("✔ Submit clicked")
        except Exception as e:
            print("⚠ Submit:", str(e)[:80])

        # 4) wait for the result
        print("→ Waiting for the result (Turnstile may take a while)...")
        fin = time.time() + 50
        estado = "unknown"
        while time.time() < fin:
            page.wait_for_timeout(3000)
            try:
                body = page.locator("body").inner_text(timeout=2000)
            except Exception:
                body = ""
            b = body.lower()
            if guardar_sid(ctx):
                estado = "ok"; break
            if "verification" in b or "code" in b or "authenticator" in b or "2fa" in b:
                estado = "2fa"; break
            if "incorrect" in b or "invalid" in b or "wrong" in b or "doesn't match" in b:
                estado = "credentials"; break
            if "turnstile" in b or "captcha" in b or "verify you are human" in b or "security check" in b:
                estado = "captcha"; break

        if estado == "ok":
            print(f"✔ LOGIN SUCCESSFUL! sid saved in {SID_FILE}")
            print("  Next: python3 scripts/descargar_nexus_cookies.py --resume")
        elif estado == "2fa":
            print("⚠ Nexus asks for 2FA. Paste the code:")
            codigo = input("   code: ").strip()
            try:
                el = page.locator("input[name='code'], input[type='text'], input[type='number']").first
                el.fill(codigo, timeout=4000)
                page.locator("button[type='submit'], input[type='submit']").first.click(timeout=4000)
            except Exception:
                pass
            page.wait_for_timeout(6000)
            if guardar_sid(ctx):
                print(f"✔ Login 2FA OK. sid in {SID_FILE}")
            else:
                print("✘ Could not complete with 2FA")
        elif estado == "captcha":
            print("✘ Cloudflare Turnstile asked us for verification (headless).")
            print("   Options: run in window mode (./vnv.sh login) or grab the cookie manually.")
        elif estado == "credentials":
            print("✘ Credentials rejected.")
        else:
            print("✘ Result not detected. Status:")
            try:
                print("  ", page.locator("body").inner_text(timeout=3000)[:300])
            except Exception:
                pass
        ctx.close()

if __name__ == "__main__":
    main()
