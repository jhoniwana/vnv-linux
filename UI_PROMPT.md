# 🎨 UI IMPROVEMENT + ASSETS PROMPT — vnv-linux

> Pegá este bloque completo a tu agente. Es autocontenido.

---

**PROYECTO:** vnv-linux — instalador 100% automático de Viva New Vegas (Core) para Fallout New Vegas en Linux/Steam.
**REPO:** github.com/jhoniwana/vnv-linux (rama main). Código local: /home/shot/vnv-linux/
**TAREA:** Mejorar la interfaz web del wizard + buscar/crear assets libres (íconos, favicon, fuentes, detalles visuales). **Commits y mensajes EN INGLÉS.**

## 1. CONTEXTO TÉCNICO (no romper esto)

- **`ui.py`** = servidor Flask (un solo archivo) que sirve el wizard en http://127.0.0.1:8397 y abre el navegador solo.
- **Backend (NO CAMBIAR la API):**
  - `GET /api/estado` → JSON: setup, sesion, credenciales, juego, mo2, archivos, mods_ok, mods_total, paso_actual
  - `POST /api/accion/<setup|login|credenciales|descargar|verificar|instalar|jugar|steam>` → {job_id}
  - `GET /api/log/<job_id>` → **SSE** (Server-Sent Events) con el log en vivo del proceso
- **Frontend actual:** HTML/CSS/JS embebido en ui.py (dark theme #0f1115, cards por paso, botones grandes, logs en vivo, checkmarks). Traducido al inglés.
- **Logo:** `assets/gecko.png` (render oficial del Green Gecko de FNV, fondo transparente, 512x512).
- **Se ejecuta con:** `./venv/camoufox-python ui.py` (wrapper del venv — nunca python3 directo).
- Los procesos que corre la UI: scripts/gestor_descargas.py, scripts/bsa_decompressor.py, scripts/esm_fixes.py, login_camoufox.py, vnv.sh (setup/install/run/steam).

## 2. OBJETIVO

Hacer que la UI se sienta **profesional y pulida** (nivel app de gaming, no prototipo) y que los **assets** usados tengan licencia libre (MIT/OFL/CC0) o sean derivados del gecko oficial.

## 3. TAREAS DE UI (priorizadas)

### 3.1 Dashboard general (ALTA)
- Header con el **gecko** + título + badge de versión del repo
- **Barra de progreso general** del pipeline (5 pasos) con porcentaje
- Estado en vivo: mods descargados X/Y, sesión OK/expira, disco usado
- Si el paso 4 (instalación) está activo: mostrar también la etapa interna (MO2, INIs, LOOT)

### 3.2 Progreso real de descargas (ALTA)
- Hoy el log SSE es texto plano. Mejorar: cuando corra `descargar`, mostrar **progreso por mod** (nombre + tamaño + estado) — el gestor escribe a estado.json, se puede hacer polling de /api/estado o un endpoint nuevo `/api/mods` que devuelva el estado de cada mod (SIN romper los endpoints existentes — agregar, no modificar).
- Barra de progreso por mod + total con porcentaje real.

### 3.3 Vista de mods (MEDIA)
- Tabla/tarjetas con los 55 mods: nombre, versión, estado (✔/⬇/✘), sección (utilities/bugfix).
- Filtro por sección y búsqueda por nombre. Fuente: manifest.json + estado.json (leerlos, no hardcodear).

### 3.4 Logs pulidos (MEDIA)
- Colores por severidad (info=azul, ok=verde, fail=rojo, warning=amarillo)
- Log colapsable por paso, auto-scroll, botón "clear"
- Timestamps opcionales

### 3.5 Detalles visuales (MEDIA)
- **Favicon**: derivar del gecko (16/32/48 PNG + SVG) → link rel=icon
- **Iconos**: usar Lucide (https://lucide.dev, MIT) o Tabler (MIT) — íconos inline SVG, no librerías externas por CDN (el usuario puede estar offline) — embebelos en el HTML
- **Fuente**: Inter (OFL) + JetBrains Mono (OFL) para logs — si se embebe, usar woff2 local; si no, fallback system-ui
- Animaciones suaves (transiciones de cards, fade de logs), sin ser molesto
- Patrón de fondo sutil (SVG noise CC0 o CSS gradient)

### 3.6 Responsive (MEDIA)
- El usuario usa Android a veces: que el wizard se vea bien en móvil (cards apiladas, botones táctiles ≥44px)

### 3.7 Extra si sobra tiempo
- Tooltips en los pasos, confirmación antes de acciones destructivas (instalar/bsa)
- Empty states lindos (ej. "no hay mods descargados")
- Detección de tema del sistema (prefers-color-scheme) — manteniendo el dark como default

## 4. ASSETS (buscar/crear — SOLO libres)

| Asset | Fuente | Licencia |
|---|---|---|
| Iconos UI | lucide.dev / tabler.io | MIT |
| Favicon gecko | derivar de assets/gecko.png (SVG+PNG) | propio |
| Fuente Inter | rsms.me/inter | OFL |
| JetBrains Mono | jetbrains.com/mono | OFL |
| Pattern/fondo | SVG noise propio o CSS | propio |
| Banner del repo (README) | composición con el gecko | propio |

**PROHIBIDO:** assets de NexusMods/LoversLab con licencia cerrada, arte de otros mods, fuentes con licencia restrictiva, imágenes de terceros sin licencia clara. Si dudás, crealo vos (SVG).

## 5. REGLAS DE TRABAJO

1. **NO romper el backend**: los 3 endpoints existentes deben seguir funcionando idénticos (agregá endpoints si necesitás, no los modifiques).
2. **Un solo archivo ui.py** se puede mantener o dividir en `scripts/ui/` (ui.py + templates/ + static/) SI lo explicás — pero `./vnv.sh ui` debe seguir funcionando igual.
3. **Probar SIEMPRE**: `./venv/camoufox-python ui.py` → curl http://127.0.0.1:8397/api/estado → screenshot con Chrome headless (google-chrome-stable --headless --screenshot) y verificar que se ve bien.
4. **Commits en inglés**, mensajes descriptivos, push a main.
5. No tocar: manifest.json, estado.json, downloads/, scripts de descarga.
6. Reportar al final: qué cambió, qué assets usaste (con licencia), y el screenshot.

## 6. ENTREGABLES

- UI mejorada (dashboard, progreso real, vista de mods, logs pulidos, favicon, responsive)
- Assets en `assets/` (favicon gecko, íconos si son propios)
- Screenshot final (desktop + móvil si podés)
- Commits en inglés + push
