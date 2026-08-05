---
tags: [guia, setup, multi-distro]
---
# Setup del Entorno

> Prepara la máquina en cualquier distro Linux. Se ejecuta solo desde la UI (paso 1) o con `./vnv.sh setup`.

## Qué hace `setup.sh`

1. **Detecta la distro** (`/etc/os-release`)
2. **Dependencias del sistema**: muestra (o instala con sudo si está disponible) los paquetes para GTK3, NSS, cairo, pixman, protontricks...
   - Debian/Ubuntu: `apt install ... protontricks`
   - Arch: `pacman -S ... protontricks`
   - Fedora: `dnf install ... protontricks`
3. **Venv + Camoufox + Flask**
4. **Smoke test**: ¿Camoufox arranca con las libs del sistema?
   - Si falla (libs rotas, típico de Arch con update parcial): **fallback automático** → micromamba user-space (sin sudo) con pixman → wrapper `venv/camoufox-python` que resuelve las librerías
5. **Verifica la sesión de Nexus** (cookies)

## El wrapper `venv/camoufox-python`

Es el intérprete de Python del proyecto: exporta el `LD_LIBRARY_PATH` correcto (limpia el contaminado) y ejecuta el python del venv. **Todos los scripts usan el wrapper.**

## Requisitos mínimos

- Python 3.10+
- ~4 GB de disco
- Steam con Fallout New Vegas

## Referencias

- [[Login Nexus]] — siguiente paso
- [[Problemas Comunes]] — si algo falla
