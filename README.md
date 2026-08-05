# ⚡ VNV Linux — Viva New Vegas para Linux/Steam

Instalador **100% automático** del Core de Viva New Vegas (53 mods) para Fallout New Vegas en Linux.

> 🎮 **Un solo comando y te lleva de la mano:**
> ```bash
> ./vnv.sh ui
> ```
> Se abre el navegador con un asistente paso a paso (botones grandes, progreso en vivo).
> **No necesitás usar la terminal.**

---

## ✅ Qué hace por vos

| Paso | Qué pasa |
|---|---|
| 1 · Entorno | Instala Python + Camoufox + librerías (funciona en Debian, Ubuntu, Arch, Fedora, openSUSE) |
| 2 · Cuenta Nexus | Login automático (gratis, una vez) — pasa el captcha solo |
| 3 · Descargas | Baja los 53 mods con reintentos automáticos y verificación de integridad |
| 4 · Instalación | Detecta el juego en Steam, instala MO2, aplica los INI tweaks, prepara LOOT |
| 5 · Jugar | Lanza Fallout New Vegas con todo cargado |

## 🚀 Empezar

```bash
git clone https://github.com/tu-usuario/vnv-linux
cd vnv-linux
./vnv.sh ui
```

Requisitos: Steam con Fallout New Vegas instalado · Python 3.10+ · ~4 GB de espacio.

## 🛠️ Comandos útiles (opcional — la UI ya hace todo)

```bash
./vnv.sh setup          # prepara el entorno (lo hace la UI en el paso 1)
./vnv.sh login          # login a Nexus (paso 2)
./vnv.sh download       # descarga mods con estados y reintentos (paso 3)
./vnv.sh estado         # verifica los 53 archivos
./vnv.sh install        # MO2 + INIs + LOOT (paso 4)
./vnv.sh run            # lanza el juego (paso 5)
```

## 🔑 Cuenta de Nexus

- **Login automático**: la UI (o `./vnv.sh login`) abre Camoufox (Firefox anti-detección) y pasa el Turnstile solo. Solo hay que hacerlo **una vez**.
- **Credenciales**: guardalas con `./vnv.sh credenciales` (permisos 600) — se usan SOLO para re-loguear automáticamente si la sesión expira.
- Las cookies (`nexusmods_session` + `cf_clearance`) viven en `~/.config/vnv-linux/` y permiten descargar gratis sin Premium.

## 🐛 Si algo falla

- El gestor de descargas **reintenta solo** (3 intentos, espera de captchas de Cloudflare, re-login automático).
- `./vnv.sh estado` verifica archivo por archivo.
- La bitácora técnica completa está en **`BRAIN.md`** (APIs, endpoints, bugs resueltos).

## 📜 Legal

Los mods se descargan desde Nexus con TU sesión (gratis). Este proyecto no redistribuye mods — solo los baja y los instala. Requiere tener el juego en Steam.
