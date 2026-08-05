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

## 🟡 Pendiente (requiere hardware real con el juego)

- Probar `install` completo en máquina con Steam + FNV (MO2-LINT, Wine, LOOT)
- Primer lanzamiento del juego con los mods
- Probar el setup en Debian real (solo probado en Arch)

## 📦 Entregables

- Repo: `/home/shot/vnv-linux/`
- 53 mods en `downloads/` (1.1 GB)
- Bitácora técnica: [[Cronología]] y `BRAIN.md`
- Esta bóveda de Obsidian
