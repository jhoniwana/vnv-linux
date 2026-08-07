#!/usr/bin/env python3
"""Login to Nexus with SeleniumBase UC (undetected) — better against Turnstile.

Usage:
    NEXUS_USER="..." NEXUS_PASS="..." ./venv/bin/python scripts/login_selenium.py [--headless2|--headed]

Saves the sid cookie in ~/.config/vnv-linux/nexus_sid (600).
"""
import argparse, os, pathlib, sys, time

CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SID_FILE = CONFIG_DIR / "nexus_sid"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def guardar_sid(driver):
    try:
        sid = driver.get_cookie("sid")
        if sid and sid.get("value"):
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            SID_FILE.write_text(sid["value"])
            SID_FILE.chmod(0o600)
            return True
    except Exception:
        pass
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true", help="real window (recommended if there is a screen)")
    ap.add_argument("--headless2", action="store_true", help="new Chrome headless (better with UC)")
    args = ap.parse_args()

    user = os.environ.get("NEXUS_USER", "")
    pw = os.environ.get("NEXUS_PASS", "")
    if not user or not pw:
        sys.exit("❌ Missing NEXUS_USER / NEXUS_PASS")

    from seleniumbase import Driver
    kwargs = dict(uc=True, headed=args.headed, headless2=args.headless2,
                  headless=not args.headed and not args.headless2,
                  locale_code="es-CO")
    driver = Driver(**kwargs)
    try:
        print(f"→ Opening login (UC {'headless2' if args.headless2 else 'headless' if not args.headed else 'window'})...")
        driver.open("https://users.nexusmods.com/register")
        time.sleep(3)
        try:
            driver.click("a:has-text('Sign in')")
            print("→ Sign in click OK")
        except Exception as e:
            print(f"  click err: {str(e)[:70]}")
        # wait for the login form (can take a while / navigate to /)
        try:
            driver.wait_for_element("#user_login", timeout=20)
        except Exception:
            # fallback: navigate straight to the root (where the login form lives)
            print("  → fallback: navigating to users.nexusmods.com/")
            driver.open("https://users.nexusmods.com/")
            try:
                driver.wait_for_element("#user_login", timeout=20)
            except Exception:
                print("  → the form does not appear; body:")
                print("   ", driver.get_text("body")[:200].replace("\n", " | "))
                driver.quit()
                sys.exit(1)
        time.sleep(2)
        driver.type("#user_login", user)
        driver.type("#password", pw)
        time.sleep(3)  # let the invisible Turnstile initialize

        exito = False
        for intento in range(3):
            try:
                driver.click("input[name='commit']")
                print(f"→ Submit {intento+1}")
            except Exception as e:
                print(f"  submit err: {str(e)[:70]}")
            # wait and see if there is a captcha checkbox to click
            for _ in range(8):
                time.sleep(3)
                if guardar_sid(driver):
                    exito = True
                    break
                # try clicking the UC captcha (if a Turnstile iframe appears)
                try:
                    if driver.is_element_visible("iframe[src*='turnstile'], iframe[src*='challenges.cloudflare']"):
                        print("   → Turnstile detected, trying UC click...")
                        driver.uc_gui_click_captcha()
                except Exception:
                    pass
            if exito:
                break
        if exito:
            print(f"✔ LOGIN OK! sid saved in {SID_FILE}")
        else:
            print("✘ Could not pass Turnstile. Status:")
            try:
                print("  ", driver.get_text("body")[:250].replace("\n", " | "))
            except Exception:
                pass
            print("  → With a screen: NEXUS_USER=... NEXUS_PASS=... ./venv/bin/python scripts/login_selenium.py --headed")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
