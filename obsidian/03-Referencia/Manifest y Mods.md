---
tags: [referencia, mods]
---
# Manifest y Mods

El Core de Viva New Vegas = **53 mods** de Nexus (todos descargados y verificados).

## Estructura del manifest

```json
{
  "mod_id": 57174,
  "seccion": "utilities",
  "nombre": "UIO - User Interface Organizer",
  "file_id": 1000080073,
  "version": "2.30"
}
```

## Secciones

- **setup** — herramientas (steam-library-setup-tool, GitHub)
- **utilities** — NVSE, JIP LN, NVTF, xNVSE, UIO...
- **bugfix** — YUP, Stewie Tweaks (66347), mesh fixes...
- **finish** — Stewie Tweaks INIs (GitHub: ModdingLinked/Stewie-Tweaks-INIs)

## Datos importantes

- El file_id correcto = **MAIN más reciente** por `uploaded_timestamp` (bug corregido: antes elegía el primero → 13 mods con versión vieja)
- **FNV 4GB Patcher**: usar el archivo **"FNV4GB for Proton"** (versión Linux/Wine)
- **JIP LN**: el plugin (v57.30) ≠ el INI (v56.24) — la guía necesita el PLUGIN
- Stewie Tweaks: mod 66347 (el 90824 está hidden por el autor)

## Referencias

- [[Descarga de Mods]]
- [[Estado Actual]]
