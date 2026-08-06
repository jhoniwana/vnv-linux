---
tags: [proyecto, estado]
---
# Estado Actual

## ✅ Completado (probado en vivo)

| Componente | Estado |
|---|---|
| Manifest con 53 mods (file_id correctos) | ✅ |
| Login Nexus automático (Camoufox pasa Turnstile) | ✅ |
| Descarga FREE de los 53 mods (1.1 GB) | ✅ verificados, 0 HTML |
| Verificación exacta vs API (MAIN más reciente) | ✅ 13 file_ids corregidos |
| Gestor de descargas (estados + retries + re-login) | ✅ |
| Setup multi-distro + wrapper de librerías | ✅ |
| UI web (wizard 6 pasos, logs en vivo SSE) | ✅ |
| Importador automático a MO2 (53/53) | ✅ |
| Comando `steam` (diagnóstico Proton) | ✅ |
| Root mods: xNVSE + 4GB (nativos) en juego real | ✅ |
| Epic Games Patcher (omisión en Steam) | ✅ |
| UE ESM Fixes: port nativo (repo `uefix-linux-port`) | ✅ 6 esm generados |

## 🟡 Pendiente (requiere hardware real con el juego)

- Root mods nativos: BSA Decompressor (rewrite BSAs v105) — único pendiente
- Git repo por cada root mod restante (bsa, xnvse, 4gb, epic)
- Integrar `root_mods.py` con los ports nativos y en `vnv.sh install` + commitear
- Probar `install` completo en máquina con Steam + FNV (MO2-LINT, Wine, LOOT)
- Primer lanzamiento del juego con los mods
- Probar el setup en Debian real (solo probado en Arch)

## 📦 Entregables

- Repo: `/home/shot/vnv-linux/`
- 53 mods en `downloads/` (1.1 GB)
- Bitácora técnica: [[Cronología]] y `BRAIN.md`
- Esta bóveda de Obsidian
