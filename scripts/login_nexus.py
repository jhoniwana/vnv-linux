#!/usr/bin/env python3
"""Automatic login to Nexus Mods and capture of the `sid` cookie.

Wabbajack pattern: a REAL Chrome window is opened and the user logs in
themselves (the script NEVER sees or saves the password — that is how 2FA,
captcha and Cloudflare work). When the login is detected, the `sid` cookie is
extracted and saved locally with 600 permissions.

Usage:
    ./scripts/login_nexus.py            # opens a window and waits for your login
    ./scripts/login_nexus.py --timeout 120   # waits up to 2 min

Requires: python3 + playwright (pip install playwright) and Chrome installed.
"""
import argparse, json, pathlib, sys, time
from playwright.sync_api import sync_playwright

CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SID_FILE = CONFIG_DIR / "nexus_sid"
LOGIN_URL = "https://users.nexusmods.com/auth/sign-in"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def detectar_login(page):
    """True when the Nexus session is started."""
    # indicators: logged-in account text in the header
    try:
        body = page.locator("body").inner_text(timeout=2500)
        if "Log out" in body or "Sign out" in body or "My profile" in body:
            return True
    except Exception:
        pass
    # or the account page URL
    if "nexusmods.com/users/myaccount" in page.url:
        return True
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=180, help="max seconds to wait (default 180)")
    args = ap.parse_args()

    # is there a display? if not, try headless (works without 2FA/captcha)
    import os
    headless = not bool(os.environ.get("DISPLAY"))

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            "/tmp/vnv-nexus-login-profile", channel="chrome", headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            user_agent=UA,
        )
        page = ctx.new_page()
        print(f"🌐 Opening Nexus ({'headless' if headless else 'window'} mode — waiting for your login up to {args.timeout}s)...")
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
            # last chance: navigate to the home page and check
            try:
                page.goto("https://www.nexusmods.com", timeout=40000)
                page.wait_for_timeout(3000)
                logueado = detectar_login(page)
            except Exception:
                pass

        if not logueado:
            print("✘ Login not detected in time. Retry (or check if 2FA is pending).")
            ctx.close()
            sys.exit(1)

        # extract the sid cookie
        cookies = ctx.cookies(["https://www.nexusmods.com", "https://users.nexusmods.com"])
        sid = next((c["value"] for c in cookies if c["name"] == "sid"), None)
        if not sid:
            print("✘ Logged in but did not find the sid cookie.")
            ctx.close()
            sys.exit(1)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(SID_FILE, "w") as f:
            f.write(sid)
        import stat
        SID_FILE.chmod(0o600)
        print(f"✔ Login OK. sid cookie saved in {SID_FILE} (permissions 600)")
        print("  Now run: python3 scripts/descargar_nexus_cookies.py --resume")
        ctx.close()

if __name__ == "__main__":
    main()
