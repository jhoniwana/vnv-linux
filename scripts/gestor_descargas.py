#!/usr/bin/env python3
"""Gestor de descargas VNV — estados, retries, verificación de integridad.

Estados por mod (persistidos en estado.json):
  pendiente → descargando → ok | fallo

Comandos:
  gestor.py                      → descarga lo pendiente/fallido (todo)
  gestor.py --solo-fallidos      → reintenta solo los fallidos
  gestor.py --verificar          → verifica archivos vs manifest (sin descargar)
  gestor.py --solo MOD_ID        → un mod
  gestor.py --seccion utilities  → una sección
  gestor.py --forzar             → re-descarga aunque esté ok (si cambió file_id)
  gestor.py --max-intentos N     → intentos por mod (def 3)

Cualquier corrida: si el file_id del manifest cambió vs el estado, re-descarga.
"""
import argparse
import json
import pathlib
import random
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
    """Devuelve True si el archivo parece real (no HTML)."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    r = subprocess.run(["file", "-b", str(path)], capture_output=True, text=True)
    tipo = r.stdout.strip()
    if "HTML" in tipo or "Unicode text" in tipo or "ASCII text" in tipo:
        return False
    return True


def archivo_existente(mid):
    for p in DEST.iterdir():
        if p.is_file() and str(mid) in p.name:
            return p
    return None


def descargar_url(url, destino):
    """Descarga directa (no-Nexus, ej. GitHub). Devuelve (ok, nombre_archivo)."""
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
    """Descarga un mod vía /Download/. Devuelve (ok, nombre_archivo, error, sin_sesion)."""
    url = f"{SITE}/Download/?id={fid}&game_id={GAME_ID}&source=ModPage"
    page.goto(url, timeout=90000, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    # esperar challenge de Cloudflare
    for _ in range(12):
        try:
            body = page.locator("body").inner_text(timeout=2000)
            if "Just a moment" in body:
                page.wait_for_timeout(5000)
                continue
            break
        except Exception:
            page.wait_for_timeout(3000)
    # ¿sesión expirada? (la página muestra el login en vez del contenido)
    try:
        body_txt = page.locator("body").inner_text(timeout=3000)
        if ("Log in" in body_txt or "Sign in" in body_txt) \
                and "served via CDN" not in body_txt \
                and "should automatically begin" not in body_txt:
            return False, None, "sesión expirada (Log in)", True
    except Exception:
        pass
    # consentimiento de cookies (una vez)
    if not consent_ya[0]:
        try:
            b = page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").first
            if b.is_visible(timeout=2000):
                b.click(timeout=3000)
                consent_ya[0] = True
                page.wait_for_timeout(3000)
        except Exception:
            pass
    # esperar auto-descarga, si no click en Download
    dl_event = []
    page.on("download", lambda d: dl_event.append(d))
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
        return False, None, "no arrancó la descarga", False
    d = dl_event[0]
    out = destino / d.suggested_filename
    d.save_as(out)
    if not verificar_archivo(out):
        out.unlink(missing_ok=True)
        return False, None, f"archivo inválido: {d.suggested_filename[:40]}", False
    return True, d.suggested_filename, None, False


def relogin():
    """Re-login a Nexus vía login_camoufox.py. Devuelve True si quedó sesión."""
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
        print("    ✘ no hay credenciales: exportá NEXUS_USER/NEXUS_PASS o corré ./vnv.sh login")
        return False
    wrapper = BASE / "venv" / "camoufox-python"
    py = str(wrapper) if wrapper.exists() else sys.executable
    r = sp.run([py, str(BASE / "scripts" / "login_camoufox.py")], env=env,
               capture_output=True, text=True, timeout=240)
    # recargar cookies (login_camoufox las escribió)
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

    # ===== MODO VERIFICAR (sin descargar) =====
    if args.verificar:
        print("🔍 VERIFICACIÓN vs manifest:")
        ok_v, mal_v = 0, []
        for m in mods:
            mid, fid = m["mod_id"], m["file_id"]
            p = archivo_existente(mid)
            if not p:
                print(f"  ✘ {mid} ({m.get('nombre') or '?'[:30]}): SIN ARCHIVO")
                mal_v.append(mid)
                est[str(mid)] = {"file_id": fid, "estado": "pendiente"}
                continue
            if not verificar_archivo(p):
                print(f"  ✘ {mid}: archivo inválido {p.name[:45]}")
                mal_v.append(mid)
                est[str(mid)] = {"file_id": fid, "estado": "fallo", "error": "archivo inválido"}
                continue
            ok_v += 1
            est[str(mid)] = {"file_id": fid, "estado": "ok", "archivo": p.name}
        guardar_estado(est)
        print(f"\n✅ {ok_v}/{len(mods)} OK | problemas: {len(mal_v)}")
        return

    # ===== MODO DESCARGA =====
    from camoufox.sync_api import Camoufox

    pendientes = []
    for m in mods:
        mid, fid = m["mod_id"], m["file_id"]
        e = est.get(str(mid), {})
        # re-descargar si cambió el file_id
        if e.get("estado") == "ok" and e.get("file_id") == fid and not args.forzar:
            pass
        elif args.solo_fallidos and e.get("estado") != "fallo":
            pass
        else:
            pendientes.append((mid, fid, m.get("nombre") or f"mod-{mid}", False, None))
        # archivos extra del mismo mod
        for x in (m.get("extra") or []):
            key = f"{mid}:{x.get('file_id')}" if x.get('file_id') else f"{mid}:url:{x.get('nombre')}"
            e = est.get(key, {})
            if e.get("estado") == "ok" and not args.forzar:
                continue
            if args.solo_fallidos and e.get("estado") != "fallo":
                continue
            pendientes.append((mid, x.get("file_id"), f"{m.get('nombre')} + {x['nombre']}", True, x))

    if not pendientes:
        print("✅ nada pendiente — todo descargado y al día")
        return

    print(f"🎯 {len(pendientes)} mods pendientes")

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
            # borrar archivo viejo si el file_id cambió (versión equivocada)
            if not es_extra:
                viejo = archivo_existente(mid)
                if viejo:
                    old_est = est.get(str(mid), {})
                    if old_est.get("file_id") != fid or args.forzar:
                        viejo.unlink(missing_ok=True)
                        print(f"    🗑 archivo viejo eliminado: {viejo.name[:50]}", flush=True)
            else:
                # borrar archivo extra viejo si existe (mismo fid, forzar)
                for p in DEST.glob(f"*{fid}*"):
                    if args.forzar:
                        p.unlink(missing_ok=True)
                        print(f"    🗑 extra viejo eliminado: {p.name[:50]}", flush=True)
            print(f"[{i}/{len(pendientes)}] mod {mid} fid {fid} — {nombre}", flush=True)
            est[key] = {"file_id": fid, "estado": "descargando", "intentos": 0}
            guardar_estado(est)
            exito = False
            if es_extra and not fid:
                # extra con URL directa (no-Nexus, ej. GitHub)
                exito, arch = descargar_url(extra["url"], DEST)
                if exito:
                    est[key] = {"file_id": None, "estado": "ok", "archivo": arch,
                                "intentos": 1, "ts": time.time()}
                    print(f"    ✔ {arch[:60]}", flush=True)
                    ok += 1
                else:
                    est[key] = {"file_id": None, "estado": "fallo",
                                "error": "descarga URL falló", "intentos": 1, "ts": time.time()}
                    print(f"    ✘ descarga URL falló", flush=True)
                    fail.append((key, "descarga URL falló"))
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
                        print(f"    ⚠ sesión expirada — re-logueando...", flush=True)
                        guardar_estado(est)
                        # re-login: login_camoufox.py usa NEXUS_USER/NEXUS_PASS del env
                        # o el archivo de credenciales del setup
                        if not relogin():
                            raise RuntimeError("re-login falló")
                        ctx.close()
                        ctx = browser.new_context(accept_downloads=True)
                        if cookies_extra:
                            ctx.add_cookies(cookies_extra)
                        page = ctx.new_page()
                        consent_ya = [False]
                        # seguir con el mismo intento (reintentar descarga)
                        continue
                    raise RuntimeError(err or "fallo")
                except Exception as e:
                    print(f"    ✘ intento {intento}/{args.max_intentos}: {type(e).__name__}: {str(e)[:80]}", flush=True)
                    est[key] = {"file_id": fid, "estado": "fallo", "error": str(e)[:100],
                                "intentos": intento, "ts": time.time()}
                    guardar_estado(est)
                    time.sleep(15 * intento)
            if not exito:
                fail.append((key, str(est[key].get("error", "?"))))
            # rate limit
            time.sleep(random.uniform(8, 15))

    guardar_estado(est)
    print(f"\n📊 RESULTADO: {ok}/{len(pendientes)} OK | fallos: {len(fail)}")
    for mid, err in fail:
        print(f"   ✘ {mid}: {err}")
    print(f"\nEstado guardado en {ESTADO.name}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
