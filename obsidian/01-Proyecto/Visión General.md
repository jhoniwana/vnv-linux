---
tags: [proyecto, vnv]
---
# Visión General

Instalador que lleva al usuario de **cero a jugar** con Viva New Vegas Core en Linux, sin tocar la terminal:

```
./vnv.sh ui  →  navegador con wizard de 6 pasos
```

## Pipeline

1. **Setup del entorno** — Python + Camoufox + librerías (Debian/Ubuntu/Arch/Fedora/openSUSE)
2. **Cuenta Nexus** — login automático (Camoufox pasa el Turnstile de Cloudflare)
3. **Descargas** — 53 mods con gestor de estados, reintentos y auto-recuperación
4. **Conectar Steam** — prefix de Proton (appid 22380) + protontricks
5. **Instalar** — MO2-LINT, importar mods, INI tweaks, LOOT
6. **Jugar** — lanzar FNV con todo cargado

## Principios

- **Sin terminal** para el usuario final: todo desde la [[Comandos vnv.sh|UI web]]
- **Auto-recuperación**: si algo falla (captcha, sesión, red), reintenta solo
- **Multi-distro**: detecta el sistema y se adapta (con fallback de librerías sin sudo)
- **Legal**: los mods se descargan con la sesión del propio usuario (gratis, sin redistribuir)

## Conceptos clave

- [[Conexión Steam]] — cómo se conecta el modloader con Steam
- [[API de Nexus]] — la fuente de los mods
