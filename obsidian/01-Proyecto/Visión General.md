---
tags: [proyecto, vnv]
---
# Visión General

Installer that takes the user from **zero to playing** with Viva New Vegas Core on Linux, without touching the terminal:

```
./vnv.sh ui  →  browser with a 6-step wizard
```

## Pipeline

1. **Environment setup** — Python + Camoufox + libraries (Debian/Ubuntu/Arch/Fedora/openSUSE)
2. **Nexus account** — automatic login (Camoufox passes the Cloudflare Turnstile)
3. **Downloads** — 53 mods with a state manager, retries and self-recovery
4. **Connect Steam** — Proton prefix (appid 22380) + protontricks
5. **Install** — MO2-LINT, import mods, INI tweaks, LOOT
6. **Play** — launch FNV with everything loaded

## Principles

- **No terminal** for the end user: everything from the [[Comandos vnv.sh|web UI]]
- **Self-recovery**: if something fails (captcha, session, network), it retries on its own
- **Multi-distro**: detects the system and adapts (with a no-sudo library fallback)
- **Legal**: the mods are downloaded with the user's own session (free, no redistribution)

## Key concepts

- [[Conexión Steam]] — how the modloader connects with Steam
- [[API de Nexus]] — the source of the mods
