#!/usr/bin/env python3
"""VNV Linux — Local web interface (guided wizard, no terminal).

Starts a server on http://127.0.0.1:8397 and opens the browser.
Each step has a big button and shows live progress.

Usage:
    ./venv/bin/python ui.py            # or:  ./vnv.sh ui
"""
import json
import os
import pathlib
import queue
import shutil
import subprocess
import sys
import threading
import time
import webbrowser

from flask import Flask, Response, jsonify, request

BASE = pathlib.Path(__file__).resolve().parent
VENV_PY = BASE / "venv" / "camoufox-python"
PY = str(VENV_PY) if VENV_PY.exists() else sys.executable
CONFIG_DIR = pathlib.Path.home() / ".config" / "vnv-linux"
DEST = BASE / "downloads"
PORT = 8397

app = Flask(__name__)

# running jobs: id -> {"q": queue, "proc": subprocess, "fin": bool}
jobs = {}
jobs_lock = threading.Lock()


# ============================ helpers ============================
def leer_json(p, default):
    try:
        return json.load(open(p))
    except Exception:
        return default


def estado_actual():
    manifest = leer_json(BASE / "manifest.json", [])
    estado = leer_json(BASE / "estado.json", {})
    n_mods = sum(1 for m in manifest if m.get("file_id"))
    # estado.json also stores the tools/root (4GB, BSA, xNVSE...) — count only
    # the manifest mods so the progress is 55/55 and not 60/55
    man_ids = {str(m.get("mod_id")) for m in manifest}
    n_ok = sum(1 for k, v in estado.items() if k in man_ids and v.get("estado") == "ok")
    n_arch = len([p for p in DEST.iterdir() if p.is_file()]) if DEST.exists() else 0
    sesion = (CONFIG_DIR / "nexus_session").exists() and (CONFIG_DIR / "nexus_session").stat().st_size > 0
    setup = VENV_PY.exists()
    cred = (CONFIG_DIR / "credenciales").exists()
    juego = False
    for lib in ["$HOME/.steam/steam/steamapps", "$HOME/.local/share/Steam/steamapps"]:
        cand = pathlib.Path(os.path.expandvars(lib)) / "common" / "Fallout New Vegas"
        if (cand / "FalloutNV.exe").exists():
            juego = True
            break
    mo2 = shutil.which("mo2-lint") is not None \
        or (pathlib.Path.home() / ".local/bin/mo2-lint").exists()
    return {
        "setup": setup,
        "sesion": {"steam": "ok" if juego else "offline",
                   "nexus": "ok" if sesion else "offline",
                   "user": None},
        "credenciales": cred,
        "mods_total": n_mods,
        "mods_ok": n_ok,
        "archivos": n_arch,
        "juego": "ok" if juego else "offline",
        "mo2": "ok" if mo2 else "offline",
        "paso_actual": 1 if not setup else 2 if not sesion else 3 if n_ok < n_mods else 4 if not mo2 else 5,
    }


def ejecutar(accion, cmd, env_extra=None):
    """Launches a process and records its log in jobs. Returns job_id."""
    jid = f"{accion}-{int(time.time())}"
    q = queue.Queue()
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env=env, cwd=str(BASE))
    jobs[jid] = {"q": q, "proc": proc, "fin": False, "lineas": []}

    def lector():
        for linea in proc.stdout:
            q.put(linea)
            jobs[jid]["lineas"].append(linea)
        proc.wait()
        q.put(None)
        with jobs_lock:
            jobs[jid]["fin"] = True

    threading.Thread(target=lector, daemon=True).start()
    return jid


# ============================ routes ============================
@app.route("/")
def index():
    return HTML_page()


@app.route("/assets/sprites/<path:fname>")
def pipboy_sprite_root(fname):
    """The design uses relative 'assets/sprites/...' paths (resolve to the server
    root) — alias of /assets/pipboy/assets/sprites/."""
    ruta = (BASE / "assets" / "pipboy" / "assets" / "sprites" / fname).resolve()
    if ruta.is_relative_to((BASE / "assets" / "pipboy").resolve()) and ruta.exists():
        return Response(ruta.read_bytes(), mimetype="image/png")
    return ("", 404)


@app.route("/assets/pipboy/<path:fname>")
def pipboy_asset(fname):
    """Sprites/images of the Pip-Boy design (assets/pipboy/assets/...)."""
    # el HTML referencia rutas relativas a su propia carpeta (assets/pipboy/)
    ruta = (BASE / "assets" / "pipboy" / fname).resolve()
    if ruta.is_relative_to((BASE / "assets" / "pipboy").resolve()) and ruta.exists():
        return Response(ruta.read_bytes(), mimetype="image/png")
    return ("", 404)


@app.route("/api/estado")
def api_estado():
    return jsonify(estado_actual())


@app.route("/api/mods")
def api_mods():
    """Mods reales para la vista SUPPLY del wizard Pip-Boy:
    [{id, name, version, size_mb, section, status}] — lee manifest.json +
    estado.json (status: done/downloading/fail/pending)."""
    manifest = leer_json(BASE / "manifest.json", [])
    estado = leer_json(BASE / "estado.json", {})
    mods = []
    for m in manifest:
        if not m.get("file_id"):
            continue
        mid = str(m["mod_id"])
        st = estado.get(mid, {})
        if st.get("estado") == "ok":
            status = "done"
        elif st.get("estado") == "fallo":
            status = "fail"
        elif st.get("estado") == "descargando":
            status = "downloading"
        else:
            status = "pending"
        size_mb = 0.0
        archivo = st.get("archivo")
        if archivo and (BASE / "downloads" / archivo).exists():
            size_mb = round((BASE / "downloads" / archivo).stat().st_size / 1048576, 1)
        mods.append({
            "id": m["mod_id"],
            "name": m["nombre"],
            "version": m.get("version") or "?",
            "size_mb": size_mb,
            "section": m.get("seccion") or "otros",
            "status": status,
        })
    return jsonify(mods)


@app.route("/api/accion/<accion>", methods=["POST"])
def api_accion(accion):
    body = request.get_json(silent=True) or {}
    env_extra = None
    if accion == "credenciales":
        user = (body.get("user") or "").strip()
        pwd = (body.get("pass") or "").strip()
        if not user or not pwd:
            return jsonify({"error": "Fill in email and password"}), 400
        os.makedirs(CONFIG_DIR, exist_ok=True)
        umask = os.umask(0o077)
        try:
            (CONFIG_DIR / "credenciales").write_text(f"{user}\n{pwd}\n")
        finally:
            os.umask(umask)
        return jsonify({"ok": True, "msg": "Credentials saved"})

    if accion == "setup":
        jid = ejecutar(accion, ["bash", str(BASE / "setup.sh")])
    elif accion == "login":
        env_extra = {"NEXUS_USER": body.get("user", ""), "NEXUS_PASS": body.get("pass", "")}
        jid = ejecutar(accion, [PY, str(BASE / "scripts" / "login_camoufox.py")], env_extra)
    elif accion == "descargar":
        jid = ejecutar(accion, [PY, str(BASE / "scripts" / "gestor_descargas.py")])
    elif accion == "verificar":
        jid = ejecutar(accion, [PY, str(BASE / "scripts" / "gestor_descargas.py"), "--verificar"])
    elif accion == "steam":
        jid = ejecutar(accion, ["bash", str(BASE / "vnv.sh"), "steam", "--si"])
    elif accion == "instalar":
        jid = ejecutar(accion, ["bash", str(BASE / "vnv.sh"), "install"])
    elif accion == "jugar":
        jid = ejecutar(accion, ["bash", str(BASE / "vnv.sh"), "run"])
    else:
        return jsonify({"error": f"Unknown action: {accion}"}), 400
    return jsonify({"job_id": jid})


@app.route("/api/log/<jid>")
def api_log(jid):
    """SSE: stream of the job log. Late reconnects replay the buffered lines."""
    def gen():
        job = jobs.get(jid)
        if job is None:
            yield "data: {\"fin\": true, \"linea\": \"job not found\"}\n\n"
            return
        # job already finished: replay the buffered lines + fin (a reconnected
        # reconectado a un job viejo no debe quedarse en pings infinitos)
        if job["fin"]:
            for l in job["lineas"]:
                yield f"data: {json.dumps({'linea': l.rstrip()})}\n\n"
            yield "data: {\"fin\": true}\n\n"
            return
        q = job["q"]
        while True:
            try:
                linea = q.get(timeout=1)
            except queue.Empty:
                yield ": ping\n\n"
                continue
            if linea is None:
                yield "data: {\"fin\": true}\n\n"
                return
            yield f"data: {json.dumps({'linea': linea.rstrip()})}\n\n"
    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ============================ UI ============================
PIPBOY_HTML = BASE / "assets" / "pipboy" / "index.html"

def _cargar_html() -> str:
    if PIPBOY_HTML.exists():
        return PIPBOY_HTML.read_text()
    return HTML  # fallback: classic embedded HTML


def HTML_page() -> str:
    return _cargar_html()


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VNV Linux — Installer</title>
<style>
  :root { --bg:#0f1115; --card:#181b22; --card2:#1e222c; --txt:#e8eaf0; --mut:#8b93a7;
          --acc:#6c8cff; --ok:#3ddc84; --err:#ff5f57; --warn:#ffcc00; --borde:#2a2f3a; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--txt); font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
         min-height:100vh; display:flex; flex-direction:column; align-items:center; padding:24px; }
  h1 { font-size:22px; margin-bottom:4px; }
  .sub { color:var(--mut); font-size:14px; margin-bottom:20px; }
  .pasos { display:flex; gap:8px; margin-bottom:24px; flex-wrap:wrap; justify-content:center; }
  .paso { background:var(--card); border:1px solid var(--borde); border-radius:10px; padding:8px 14px;
          font-size:13px; color:var(--mut); display:flex; align-items:center; gap:8px; }
  .paso.activo { border-color:var(--acc); color:var(--txt); }
  .paso.hecho { border-color:var(--ok); color:var(--ok); }
  .dot { width:8px; height:8px; border-radius:50%; background:var(--mut); }
  .paso.activo .dot { background:var(--acc); }
  .paso.hecho .dot { background:var(--ok); }
  .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; width:100%; max-width:1000px; }
  .card { background:var(--card); border:1px solid var(--borde); border-radius:14px; padding:20px; }
  .card h2 { font-size:16px; margin-bottom:6px; display:flex; align-items:center; gap:8px; }
  .card p { color:var(--mut); font-size:13px; line-height:1.5; margin-bottom:12px; }
  .btn { background:var(--acc); color:#fff; border:none; border-radius:10px; padding:12px 20px;
         font-size:15px; font-weight:600; cursor:pointer; width:100%; transition:opacity .15s; }
  .btn:hover { opacity:.88; }
  .btn:disabled { opacity:.35; cursor:not-allowed; }
  .btn.sec { background:var(--card2); border:1px solid var(--borde); color:var(--txt); }
  .check { color:var(--ok); font-weight:700; }
  .x { color:var(--err); }
  .log { background:#0a0c10; border:1px solid var(--borde); border-radius:10px; padding:12px;
         font-family:ui-monospace,monospace; font-size:12px; max-height:260px; overflow-y:auto;
         white-space:pre-wrap; color:#9fe8a8; display:none; }
  .prog { height:8px; background:var(--card2); border-radius:5px; overflow:hidden; margin-bottom:8px; display:none; }
  .prog > div { height:100%; width:0%; background:var(--ok); transition:width .4s; }
  .form { display:flex; flex-direction:column; gap:8px; margin-bottom:10px; }
  .form input { background:var(--card2); border:1px solid var(--borde); border-radius:8px; padding:10px;
                color:var(--txt); font-size:14px; }
  .barra { background:var(--card); border:1px solid var(--borde); border-radius:14px; padding:20px;
           width:100%; max-width:1000px; margin-top:16px; }
  .mini { font-size:12px; color:var(--mut); margin-top:8px; text-align:center; }
</style>
</head>
<body>
  <h1>⚡ Viva New Vegas — Linux Installer</h1>
  <div class="sub">All automatic: environment → account → downloads → install → play</div>
  <div class="pasos" id="pasos"></div>
  <div class="cards">
    <div class="card" id="card-setup">
      <h2>1 · Set up environment</h2>
      <p>Installs Python, Camoufox and the libraries needed for this distro (Debian, Ubuntu, Arch, Fedora...).</p>
      <button class="btn" onclick="correr('setup','card-setup')">Set up environment</button>
    </div>
    <div class="card" id="card-cuenta">
      <h2>2 · Nexus account</h2>
      <p>We need your Nexus session to download the mods (free, only once).</p>
      <div class="form">
        <input id="user" placeholder="Nexus email" autocomplete="off">
        <input id="pass" type="password" placeholder="Nexus password">
      </div>
      <button class="btn sec" onclick="guardarCred()">Save credentials</button>
      <button class="btn" style="margin-top:8px" onclick="correr('login','card-cuenta')">Start automatic login</button>
    </div>
    <div class="card" id="card-descargas">
      <h2>3 · Download mods</h2>
      <p>Downloads the 53 mods of the Viva New Vegas Core (with automatic retries if something fails).</p>
      <div class="prog" id="prog"><div id="progfill"></div></div>
      <button class="btn" onclick="correr('descargar','card-descargas')">Download mods</button>
      <button class="btn sec" style="margin-top:8px" onclick="correr('verificar','card-descargas')">Verify files</button>
    </div>
    <div class="card" id="card-steam">
      <h2>3½ · Connect with Steam</h2>
      <p>Detects Steam and Fallout New Vegas, creates the Proton prefix (appid 22380) and verifies protontricks so MO2 works.</p>
      <button class="btn sec" onclick="correr('steam','card-steam')">🔗 Diagnose / connect Steam</button>
    </div>
    <div class="card" id="card-instalar">
      <h2>4 · Install with MO2</h2>
      <p>Detects the game in Steam, installs Mod Organizer 2, applies the INI tweaks and prepares LOOT.</p>
      <button class="btn" onclick="correr('instalar','card-instalar')">Install everything</button>
    </div>
    <div class="card" id="card-jugar">
      <h2>5 · Play</h2>
      <p>Launches Fallout New Vegas with all the mods loaded.</p>
      <button class="btn" onclick="correr('jugar','card-jugar')">🎮 Launch the game</button>
    </div>
  </div>
  <div class="barra">
    <div style="font-weight:600;margin-bottom:8px">📋 Live progress</div>
    <div class="log" id="log"></div>
  </div>
  <div class="mini" id="mini"></div>

<script>
const PASOS = ['setup','cuenta','descargas','instalar','jugar'];
let evSource = null;

function actualizar() {
  fetch('/api/estado').then(r => r.json()).then(e => {
    const defs = {
      setup:   { t:'Environment',        ok: e.setup },
      cuenta:  { t:'Nexus account',      ok: e.sesion },
      descargas:{t:'Downloads',          ok: e.mods_ok >= e.mods_total && e.mods_total > 0 },
      instalar:{ t:'MO2 + INIs',         ok: e.mo2 },
      jugar:   { t:'Play',               ok: e.juego }
    };
    const html = PASOS.map((k,i) => {
      const d = defs[k];
      const cls = d.ok ? 'hecho' : (i+1 === e.paso_actual ? 'activo' : '');
      const mark = d.ok ? '✔' : '';
      return `<div class="paso ${cls}"><span class="dot"></span>${i+1}. ${d.t} ${mark}</div>`;
    }).join('');
    document.getElementById('pasos').innerHTML = html;
    document.getElementById('mini').textContent =
      `Mods: ${e.mods_ok}/${e.mods_total} downloaded · Files on disk: ${e.archivos}` +
      (e.credenciales ? ' · Credentials saved' : '');
  });
}

function guardarCred() {
  const user = document.getElementById('user').value;
  const pass = document.getElementById('pass').value;
  fetch('/api/accion/credenciales', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({user, pass})})
    .then(r => r.json()).then(d => { alert(d.msg || d.error || 'OK'); actualizar(); });
}

function correr(accion, cardId) {
  const card = document.getElementById(cardId);
  const btn = card.querySelector('button');
  const log = document.getElementById('log');
  const prog = document.getElementById('prog');
  const fill = document.getElementById('progfill');
  btn.disabled = true;
  log.style.display = 'block';
  prog.style.display = 'block';
  log.textContent = '';
  fill.style.width = '5%';
  const body = {user: document.getElementById('user').value,
                pass: document.getElementById('pass').value};
  fetch('/api/accion/' + accion, {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify(body)})
    .then(r => r.json()).then(d => {
      if (d.error) { log.textContent = 'Error: ' + d.error; btn.disabled = false; return; }
      if (evSource) evSource.close();
      evSource = new EventSource('/api/log/' + d.job_id);
      evSource.onmessage = e => {
        const m = JSON.parse(e.data);
        if (m.linea) {
          log.textContent += m.linea + '\\n';
          log.scrollTop = log.scrollHeight;
          fill.style.width = Math.min(90, fill.style.width.replace('%','')*1 + 0.4) + '%';
        }
        if (m.fin) {
          evSource.close();
          fill.style.width = '100%';
          setTimeout(() => { btn.disabled = false; actualizar(); }, 600);
        }
      };
    });
}

setInterval(actualizar, 4000);
actualizar();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    print(f"🌐 VNV UI at http://127.0.0.1:{port} — browser opening...")
    app.run(host="127.0.0.1", port=port, threaded=True)
