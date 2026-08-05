---
tags: [bitacora]
---
# Cronología

## 5 agosto 2026 — Día grande

- **Descarga FREE resuelta**: endpoint `/Download/` descubierto (tras insistencia del usuario con "Manual download")
- 53/53 mods descargados y verificados (1.1 GB)
- **Verificación exacta**: bug de file_ids corregido (13 mods), MAIN más reciente
- **Gestor robusto**: estados, retries, re-login automático (probado: sesión borrada → se recuperó solo)
- **Setup multi-distro** + wrapper de librerías (smoke test + fallback micromamba)
- **UI web**: wizard 6 pasos con SSE en vivo — sin terminal
- **Importador MO2 automático**: 53/53 importados
- **Conexión Steam**: comando `steam` + protontricks + teoría del lanzamiento
- **Bóveda de Obsidian** creada

## Descubrimientos clave (5 ago)

| Descubrimiento | Impacto |
|---|---|
| Camoufox pasa el Turnstile headless | Login automático ✅ |
| Cookie real = `nexusmods_session` (no `sid`) | Descargas ✅ |
| Endpoint `/Download/?id=...` gratis | 53 mods sin Premium ✅ |
| "Log in" ≠ "Sign in" | Re-login automático ✅ |
| MAIN más reciente por timestamp | File_ids exactos ✅ |

## Fase previa (2-4 agosto)

- Exploración: Playwright, Selenium UC, LightPanda (ninguno pasó el Turnstile)
- Xvfb/conda: callejón sin salida (libs rotas) → resuelto con wrapper
- Login "estilo Wabbajack" (ventana real) documentado como alternativa

## Ver también

- [[Estado Actual]]
- [[Objetivos y Roadmap]]
