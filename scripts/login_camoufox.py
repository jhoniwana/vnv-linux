#!/usr/bin/env python3
"""Login to Nexus with Camoufox (anti-detection Firefox) — tries to pass Turnstile headless.

Usage:
    NEXUS_USER="..." NEXUS_PASS="..." ./venv/bin/python scripts/login_camoufox.py

Saves the session cookie in ~/.config/vnv-linux/nexus_session (600).
"""
import os, pathlib, sys, time

CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SID_FILE = CONFIG_DIR / "nexus_session"   # real cookie: nexusmods_session (formerly 'sid')
CF_FILE = CONFIG_DIR / "cf_clearance"     # Cloudflare cookie (important for downloads)

def main():
    user = os.environ.get("NEXUS_USER", "")
    pw = os.environ.get("NEXUS_PASS", "")
    if not user or not pw:
        sys.exit("[ERROR] Missing NEXUS_USER / NEXUS_PASS")

    from camoufox.sync_api import Camoufox

    with Camoufox(headless=True) as browser:
        ctx = browser.new_context()
        page = ctx.new_page()
        print("-> Opening login with Camoufox (headless anti-detection)...")
        page.goto("https://users.nexusmods.com/register", timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        try:
            page.locator("a:has-text('Sign in')").first.click(timeout=5000)
            print("[OK] Sign in clicked")
        except Exception as e:
            print(f"  click err: {str(e)[:70]}")
        try:
            page.wait_for_selector("#user_login", timeout=20000)
        except Exception:
            page.goto("https://users.nexusmods.com/", timeout=45000)
            page.wait_for_selector("#user_login", timeout=20000)
        page.fill("#user_login", user)
        page.fill("#password", pw)
        print("[OK] Credentials filled in. Waiting for Turnstile...")
        page.wait_for_timeout(8000)

        exito = False
        for intento in range(3):
            try:
                page.click("input[name='commit']", timeout=15000)
                print(f"-> Submit {intento+1}")
            except Exception as e:
                print(f"  submit err: {str(e)[:60]}")
            for _ in range(10):
                page.wait_for_timeout(3000)
                # 1) detect login from the page
                try:
                    body = page.locator("body").inner_text(timeout=1500)
                    if "sign out" in body.lower() or "welcome back" in body.lower():
                        print("[OK] Detected: logged-in account page")
                        # extract cookies: nexusmods_session (session) + cf_clearance (Cloudflare)
                        cookies = ctx.cookies()
                        for c in cookies:
                            if c["name"] == "nexusmods_session":
                                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                                SID_FILE.write_text(c["value"])
                                SID_FILE.chmod(0o600)
                                print(f"[OK] nexusmods_session saved -> {SID_FILE}")
                                exito = True
                            elif c["name"] == "cf_clearance":
                                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                                CF_FILE.write_text(c["value"])
                                CF_FILE.chmod(0o600)
                                print(f"[OK] cf_clearance saved -> {CF_FILE}")
                        if exito:
                            break
                except Exception:
                    pass
                if exito:
                    break
                # if a Turnstile checkbox appears in an iframe, click it
                for fr in page.frames:
                    if "turnstile" in fr.url or "challenges.cloudflare" in fr.url:
                        try:
                            cb = fr.locator("input[type='checkbox'], .ctp-checkbox-label").first
                            if cb.is_visible(timeout=1500):
                                cb.click(timeout=2000)
                                print("   -> Turnstile checkbox clicked")
                        except Exception:
                            pass
            if exito:
                break

        if exito:
            print(f"[OK] LOGIN OK WITH CAMOUFOX! sid saved in {SID_FILE}")
            print("  Next: run ./vnv.sh download to fetch the 55 mods")
        else:
            try:
                body = page.locator("body").inner_text(timeout=3000)[:250]
                print("[FAIL] Cookie not detected. Status:", body.replace("\n", " | ")[:200])
            except Exception:
                print("[FAIL] Cookie not detected.")
        ctx.close()

if __name__ == "__main__":
    main()
