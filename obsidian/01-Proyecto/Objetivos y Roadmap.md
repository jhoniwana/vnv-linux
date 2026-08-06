---
tags: [proyecto, roadmap]
---
# Objetivos y Roadmap

## Objetivo final

**Un solo comando → jugar**: `./vnv.sh ui` y el wizard lleva de la mano hasta lanzar Fallout New Vegas con Viva New Vegas Core.

## Roadmap

- [x] Manifest 53 mods con file_ids exactos
- [x] Login automático (Camoufox headless)
- [x] Descarga FREE completa + verificación
- [x] Gestor robusto (estados, retries, re-login)
- [x] Setup multi-distro
- [x] UI web sin terminal
- [x] Importador MO2 automático
- [x] Diagnóstico Steam/Proton (`vnv.sh steam`)
- [x] Root mods xNVSE + 4GB (nativos, probados en juego real)
- [ ] Root mods nativos: BSA Decompressor + extractor UE ESM Fixes (sin Wine) + `_wine()`→protontricks
- [ ] Git repo por cada root mod (xnvse, 4gb, epic, bsa, uefix)
- [ ] Integrar root mods en `vnv.sh install` + commit
- [ ] Probar `install` real (MO2-LINT en máquina con el juego)
- [ ] LOOT + primer lanzamiento validado
- [ ] Probar en Debian
- [ ] Publicar repo en GitHub

## Ideas futuras

- Soporte de VNV Extended (Wabbajack vía Jackify)
- Colecciones de otros juegos (Fallout 4, Skyrim) con el mismo framework
- Instalador de la UI como app (Electron/Tauri) o .desktop
