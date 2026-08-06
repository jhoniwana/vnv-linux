---
tags: [bitacora]
---
# Cronología

## 5 agosto 2026 — Fase 2: Root mods + plan nativo

- **Commit `08ca4d5`**: `importar_mo2.py` con raíces de datos válidas FNV + motor FOMOD + loadorder de la guía (20 plugins); `vnv.sh` con MO2-LINT; reimport completo 53/53 mods válidos.
- **`scripts/root_mods.py`** (paso "root mods" de la guía): xnvse + 4GB probados en juego real OK; epic omitido correctamente en Steam; bsa/uefix rotos con `wine` plano (ver BRAIN.md).
- **Descubrimiento**: `wine` no corre GUIs en el prefix Proton (errores setupapi) → hay que usar `protontricks-launch 22380`.
- **Decisión del usuario**: reimplementar nativo en Linux el BSA Decompressor y el extractor del `.mpi` de UE ESM Fixes (formato BSA v105) + **crear un git repo por cada root mod** (xnvse, 4gb, epic, bsa, uefix).
- **Lección shell**: `pkill -f` con patrón presente en la propia línea de comando se mata a sí mismo → timeout.

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
