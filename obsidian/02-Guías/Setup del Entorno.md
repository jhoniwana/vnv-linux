---
tags: [guia, setup, multi-distro]
---
# Setup del Entorno

> Prepares the machine on any Linux distro. It runs only from the UI (step 1) or with `./vnv.sh setup`.

## What `setup.sh` does

1. **Detects the distro** (`/etc/os-release`)
2. **System dependencies**: shows (or installs with sudo if available) the packages for GTK3, NSS, cairo, pixman, protontricks...
   - Debian/Ubuntu: `apt install ... protontricks`
   - Arch: `pacman -S ... protontricks`
   - Fedora: `dnf install ... protontricks`
3. **Venv + Camoufox + Flask**
4. **Smoke test**: does Camoufox start with the system libs?
   - If it fails (broken libs, typical of Arch with a partial update): **automatic fallback** → micromamba user-space (no sudo) with pixman → `venv/camoufox-python` wrapper that resolves the libraries
5. **Verifies the Nexus session** (cookies)

## The `venv/camoufox-python` wrapper

It is the project's Python interpreter: it exports the correct `LD_LIBRARY_PATH` (cleans the contaminated one) and runs the venv python. **All scripts use the wrapper.**

## Minimum requirements

- Python 3.10+
- ~4 GB of disk
- Steam with Fallout New Vegas

## References

- [[Login Nexus]] — next step
- [[Problemas Comunes]] — if something fails
