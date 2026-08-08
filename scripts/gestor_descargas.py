#!/usr/bin/env python3
"""VNV download manager — states, retries, integrity verification.

States per mod (persisted in estado.json):
  pending → downloading → ok | fail

Commands:
  gestor.py                      → downloads pending/failed (all)
  gestor.py --solo-fallidos      → retries only the failed ones
  gestor.py --verificar          → verifies files vs manifest (no download)
  gestor.py --solo MOD_ID        → one mod
  gestor.py --seccion utilities  → one section
  gestor.py --forzar             → re-downloads even if ok (if file_id changed)
  gestor.py --max-intentos N     → attempts per mod (default 3)

Any run: if the manifest file_id changed vs the state, re-download.
"""
import argparse
import json
import pathlib
import random
import shutil
import subprocess
import sys
import time

BASE = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = BASE / "manifest.json"
ESTADO = BASE / "estado.json"
DEST = BASE / "downloads"
CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
SITE = "https://www.nexusmods.com"
GAME_ID = "130"

ESTADOS = ("pendiente", "descargando", "ok", "fallo")


def cargar_estado():
    if ESTADO.exists():
        return json.load(open(ESTADO))
    return {}


def guardar_estado(est):
    json.dump(est, open(ESTADO, "w"), indent=2, ensure_ascii=False)


def verificar_archivo(path):
    """Returns True if the file looks real (not HTML)."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    # python puro: rechazar HTML/páginas de error sin depender del binario
    # 'file' (ausente en distros minimales/containers → FileNotFoundError)
    try:
        with open(path, "rb") as f:
            head = f.read(512)
        stripped = head.lstrip()
        if head[:3] in (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff"):
            stripped = stripped[3:]
        if stripped.startswith((b"<!DOCTYPE", b"<html", b"<script", b"<head")) \
                or (b"<html" in head[:64] and b"{" not in head):
            return False
        # binario (7z/zip/rar/dds/nif...) o texto no-HTML (JSON etc.)
        if b"<" not in head[:64]:
            return True
    except Exception:
        pass
    # fallback: el binario 'file' si existe
    if shutil.which("file"):
        r = subprocess.run(["file", "-b", str(path)], capture_output=True, text=True)
        tipo = r.stdout.strip()
        if "HTML" in tipo or "Unicode text" in tipo or "ASCII text" in tipo:
            return False
        return True
    return True


def archivo_existente(mid):
    for p in DEST.iterdir():
        if p.is_file() and str(mid) in p.name:
            return p
    return None


def descargar_url(url, destino):
    """Direct download (non-Nexus, e.g. GitHub). Returns (ok, filename)."""
    try:
        import requests
    except ImportError:
        return False, None
    try:
        r = requests.get(url, stream=True, timeout=(30, 300),
                         headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
        r.raise_for_status()
    except Exception:
        return False, None
    fname = pathlib.Path(url.split("?")[0]).name or "download"
    out = destino / fname
    with open(out, "wb") as fh:
        for chunk in r.iter_content(131072):
            fh.write(chunk)
    if not verificar_archivo(out):
        out.unlink(missing_ok=True)
        return False, None
    return True, fname


def descargar_uno(page, mid, fid, destino, consent_ya):
    """Downloads a mod via /Download/. Returns (ok, filename, error, no_session)."""
    url = f"{SITE}/Download/?id={fid}&game_id={GAME_ID}&source=ModPage"
    # handler ANTES del goto: si la descarga arranca durante la navegación
    # (download directo), el evento se pierde si nos registramos después
    dl_event = []
    page.on("download", lambda d: dl_event.append(d))
    page.goto(url, timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    # wait for the Cloudflare challenge
    for _ in range(12):
        try:
            body = page.locator("body").inner_text(timeout=2000)
            if "Just a moment" in body:
                page.wait_for_timeout(5000)
                continue
            break
        except Exception:
            page.wait_for_timeout(3000)
    # session expired? (the page shows the login instead of the content)
    try:
        body_txt = page.locator("body").inner_text(timeout=3000)
        if ("Log in" in body_txt or "Sign in" in body_txt) \
                and "served via CDN" not in body_txt \
                and "should automatically begin" not in body_txt:
            return False, None, "session expired (Log in)", True
    except Exception:
        pass
    # cookie consent (once) — Cookiebot cambió a TCFv2.3 (nov 2025): el id
    # exacto ya no existe; probar varios selectores (shadow DOM incluido)
    if not consent_ya[0]:
        for sel in ["#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
                    "[id*='OptinAllowAll']",
                    "button:has-text('Accept all')",
                    "button:has-text('Accept')"]:
            try:
                b = page.locator(sel).first
                if b.count() and b.is_visible(timeout=1500):
                    b.click(timeout=3000)
                    consent_ya[0] = True
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                continue
    # wait for the auto-download, otherwise click Download
    for _ in range(12):
        if dl_event:
            break
        page.wait_for_timeout(1000)
    if not dl_event:
        page.evaluate("""() => {
            const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let n, h = null;
            while (n = w.nextNode()) {
                const t = n.textContent || '';
                if (t.includes('served via CDN') || t.includes('should automatically begin')) {
                    h = n.parentElement; break;
                }
            }
            if (!h) return;
            let el = h;
            for (let k = 0; k < 6 && el; k++) el = el.parentElement;
            const btns = el ? el.querySelectorAll('a, button') : [];
            for (const a of btns) { if ((a.innerText||'').trim() === 'Download') { a.click(); return; } }
            if (btns.length) btns[0].click();
        }""")
        for _ in range(40):
            if dl_event:
                break
            page.wait_for_timeout(1000)
    if not dl_event:
        return False, None, "download did not start", False
    d = dl_event[0]
    out = destino / d.suggested_filename
    d.save_as(out)
    if not verificar_archivo(out):
        out.unlink(missing_ok=True)
        return False, None, f"invalid file: {d.suggested_filename[:40]}", False
    return True, d.suggested_filename, None, False


def relogin():
    """Re-login to Nexus via login_camoufox.py. Returns True if a session was left."""
    global cookies_extra
    import os
    import subprocess as sp
    cred = CONFIG_DIR / "credenciales"
    env = dict(os.environ)
    if not env.get("NEXUS_USER") and cred.exists():
        lines = cred.read_text().splitlines()
        if len(lines) >= 2:
            env["NEXUS_USER"] = lines[0].strip()
            env["NEXUS_PASS"] = lines[1].strip()
    if not env.get("NEXUS_USER"):
        print("    ✘ no credentials: export NEXUS_USER/NEXUS_PASS or run ./vnv.sh login")
        return False
    wrapper = BASE / "venv" / "camoufox-python"
    py = str(wrapper) if wrapper.exists() else sys.executable
    r = sp.run([py, str(BASE / "scripts" / "login_camoufox.py")], env=env,
               capture_output=True, text=True, timeout=240)
    # reload cookies (login_camoufox wrote them)
    cookies_extra.clear()
    for name, f in [("nexusmods_session", "nexus_session"), ("cf_clearance", "cf_clearance")]:
        p = CONFIG_DIR / f
        if p.exists():
            cookies_extra.append({"name": name, "value": p.read_text().strip(),
                                  "domain": ".nexusmods.com", "path": "/"})
    return bool(cookies_extra)


def main():
    global cookies_extra
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-fallidos", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--solo", type=int)
    ap.add_argument("--seccion")
    ap.add_argument("--max-intentos", type=int, default=3)
    args = ap.parse_args()

    mods = json.load(open(MANIFEST))
    if args.solo:
        mods = [m for m in mods if m["mod_id"] == args.solo]
    if args.seccion:
        mods = [m for m in mods if m["seccion"] == args.seccion]
    mods = [m for m in mods if m.get("file_id")]
    DEST.mkdir(exist_ok=True)

    est = cargar_estado()

    # ===== VERIFY MODE (no download) =====
    if args.verificar:
        print("🔍 VERIFICATION vs manifest:")
        ok_v, mal_v = 0, []
        for m in mods:
            mid, fid = m["mod_id"], m["file_id"]
            p = archivo_existente(mid)
            if not p:
                print(f"  ✘ {mid} ({m.get('nombre') or '?'[:30]}): NO FILE")
                mal_v.append(mid)
                est[str(mid)] = {"file_id": fid, "estado": "pendiente"}
                continue
            if not verificar_archivo(p):
                print(f"  ✘ {mid}: invalid file {p.name[:45]}")
                mal_v.append(mid)
                est[str(mid)] = {"file_id": fid, "estado": "fallo", "error": "invalid file"}
                continue
            ok_v += 1
            est[str(mid)] = {"file_id": fid, "estado": "ok", "archivo": p.name}
        guardar_estado(est)
        print(f"\n✅ {ok_v}/{len(mods)} OK | problems: {len(mal_v)}")
        return

    # ===== DOWNLOAD MODE =====
    from camoufox.sync_api import Camoufox

    pendientes = []
    for m in mods:
        mid, fid = m["mod_id"], m["file_id"]
        e = est.get(str(mid), {})
        # re-download if the file_id changed
        if e.get("estado") == "ok" and e.get("file_id") == fid and not args.forzar:
            # el estado dice ok — PERO el archivo debe EXISTIR en disco (el
            # estado.json del repo clonado puede mentir en una máquina fresca)
            archivo = e.get("archivo")
            existente = (DEST / archivo) if archivo else None
            if existente is None or not existente.exists() or existente.stat().st_size == 0:
                print(f"    ⚠ {mid}: estado dice ok pero el archivo falta en disco — re-downloading", flush=True)
                pendientes.append((mid, fid, m.get("nombre") or f"mod-{mid}", False, None))
                continue
            # validate that the main file is not one of an extra (historical crossings)
            extra_archivos = [est.get(f"{mid}:{x.get('file_id')}", {}).get("archivo")
                              if x.get("file_id") else None
                              for x in (m.get("extra") or [])]
            if e.get("archivo") in extra_archivos:
                print(f"    ⚠ {mid}: main state crossed with an extra — re-downloading", flush=True)
                pendientes.append((mid, fid, m.get("nombre") or f"mod-{mid}", False, None))
        elif args.solo_fallidos and e.get("estado") != "fallo":
            pass
        else:
            pendientes.append((mid, fid, m.get("nombre") or f"mod-{mid}", False, None))
        # extra files of the same mod
        for x in (m.get("extra") or []):
            key = f"{mid}:{x.get('file_id')}" if x.get('file_id') else f"{mid}:url:{x.get('nombre')}"
            e = est.get(key, {})
            if e.get("estado") == "ok" and not args.forzar:
                continue
            if args.solo_fallidos and e.get("estado") != "fallo":
                continue
            pendientes.append((mid, x.get("file_id"), f"{m.get('nombre')} + {x['nombre']}", True, x))

    if not pendientes:
        print("✅ nothing pending — everything downloaded and up to date")
        return

    print(f"🎯 {len(pendientes)} mods pending")

    cookies_extra = []
    for name, f in [("nexusmods_session", "nexus_session"), ("cf_clearance", "cf_clearance")]:
        p = CONFIG_DIR / f
        if p.exists():
            cookies_extra.append({"name": name, "value": p.read_text().strip(),
                                  "domain": ".nexusmods.com", "path": "/"})
    ok, fail = 0, []

    with Camoufox(headless=True) as browser:
        ctx = browser.new_context(accept_downloads=True)
        if cookies_extra:
            ctx.add_cookies(cookies_extra)
        page = ctx.new_page()
        consent_ya = [False]

        for i, (mid, fid, nombre, es_extra, extra) in enumerate(pendientes, 1):
            nombre = (nombre or f"mod-{mid}")[:45]
            if es_extra:
                key = f"{mid}:{fid}" if fid else f"{mid}:url:{extra['nombre']}"
            else:
                key = str(mid)
            # delete the old file if the file_id changed (wrong version)
            if not es_extra:
                viejo = archivo_existente(mid)
                if viejo:
                    old_est = est.get(str(mid), {})
                    if old_est.get("file_id") != fid or args.forzar:
                        viejo.unlink(missing_ok=True)
                        print(f"    🗑 old file removed: {viejo.name[:50]}", flush=True)
            else:
                # delete the old extra file if it exists (same fid, force)
                for p in DEST.glob(f"*{fid}*"):
                    if args.forzar:
                        p.unlink(missing_ok=True)
                        print(f"    🗑 old extra removed: {p.name[:50]}", flush=True)
            print(f"[{i}/{len(pendientes)}] mod {mid} fid {fid} — {nombre}", flush=True)
            est[key] = {"file_id": fid, "estado": "descargando", "intentos": 0}
            guardar_estado(est)
            exito = False
            if es_extra and not fid:
                # extra with direct URL (non-Nexus, e.g. GitHub)
                exito, arch = descargar_url(extra["url"], DEST)
                if exito:
                    est[key] = {"file_id": None, "estado": "ok", "archivo": arch,
                                "intentos": 1, "ts": time.time()}
                    print(f"    ✔ {arch[:60]}", flush=True)
                    ok += 1
                else:
                    est[key] = {"file_id": None, "estado": "fallo",
                                "error": "URL download failed", "intentos": 1, "ts": time.time()}
                    print(f"    ✘ URL download failed", flush=True)
                    fail.append((key, "URL download failed"))
                guardar_estado(est)
                time.sleep(random.uniform(3, 6))
                continue
            for intento in range(1, args.max_intentos + 1):
                try:
                    okd, arch, err, sin_sesion = descargar_uno(page, mid, fid, DEST, consent_ya)
                    if okd:
                        est[key] = {"file_id": fid, "estado": "ok", "archivo": arch,
                                    "intentos": intento, "ts": time.time()}
                        print(f"    ✔ {arch[:60]}", flush=True)
                        ok += 1
                        exito = True
                        break
                    if sin_sesion:
                        print(f"    ⚠ session expired — re-logging in...", flush=True)
                        guardar_estado(est)
                        # re-login: login_camoufox.py uses NEXUS_USER/NEXUS_PASS
                        # from the env or the credentials file from setup
                        if not relogin():
                            raise RuntimeError("re-login failed")
                        ctx.close()
                        ctx = browser.new_context(accept_downloads=True)
                        if cookies_extra:
                            ctx.add_cookies(cookies_extra)
                        page = ctx.new_page()
                        consent_ya = [False]
                        # continue with the same attempt (retry download)
                        continue
                    raise RuntimeError(err or "failure")
                except Exception as e:
                    print(f"    ✘ attempt {intento}/{args.max_intentos}: {type(e).__name__}: {str(e)[:80]}", flush=True)
                    est[key] = {"file_id": fid, "estado": "fallo", "error": str(e)[:100],
                                "intentos": intento, "ts": time.time()}
                    guardar_estado(est)
                    time.sleep(15 * intento)
            if not exito:
                fail.append((key, str(est[key].get("error", "?"))))
            # rate limit
            time.sleep(random.uniform(8, 15))

    guardar_estado(est)
    print(f"\n📊 RESULT: {ok}/{len(pendientes)} OK | failures: {len(fail)}")
    for mid, err in fail:
        print(f"   ✘ {mid}: {err}")
    print(f"\nState saved in {ESTADO.name}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
