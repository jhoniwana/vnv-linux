---
tags: [bitacora]
---
# Cronología

## 5 August 2026 — Big day

- **FREE download solved**: `/Download/` endpoint discovered (after the user insisted on "Manual download")
- 53/53 mods downloaded and verified (1.1 GB)
- **Exact verification**: file_ids bug fixed (13 mods), newest MAIN
- **Robust manager**: states, retries, automatic re-login (tested: session deleted → it recovered by itself)
- **Multi-distro setup** + library wrapper (smoke test + micromamba fallback)
- **Web UI**: 6-step wizard with live SSE — no terminal
- **Automatic MO2 importer**: 53/53 imported
- **Steam connection**: `steam` command + protontricks + launch theory
- **Obsidian vault** created

## Key discoveries (5 Aug)

| Discovery | Impact |
|---|---|
| Camoufox passes the Turnstile headless | Automatic login ✅ |
| The real cookie is `nexusmods_session` (not `sid`) | Downloads ✅ |
| Free `/Download/?id=...` endpoint | 53 mods without Premium ✅ |
| "Log in" ≠ "Sign in" | Automatic re-login ✅ |
| Newest MAIN by timestamp | Exact file_ids ✅ |

## Previous phase (2-4 August)

- Exploration: Playwright, Selenium UC, LightPanda (none passed the Turnstile)
- Xvfb/conda: dead end (broken libs) → solved with the wrapper
- "Wabbajack-style" login (real window) documented as an alternative

## See also

- [[Estado Actual]]
- [[Objetivos y Roadmap]]
