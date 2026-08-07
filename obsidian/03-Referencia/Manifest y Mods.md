---
tags: [referencia, mods]
---
# Manifest y Mods

The Viva New Vegas Core = **53 mods** from Nexus (all downloaded and verified).

## Manifest structure

```json
{
  "mod_id": 57174,
  "seccion": "utilities",
  "nombre": "UIO - User Interface Organizer",
  "file_id": 1000080073,
  "version": "2.30"
}
```

## Sections

- **setup** — tools (steam-library-setup-tool, GitHub)
- **utilities** — NVSE, JIP LN, NVTF, xNVSE, UIO...
- **bugfix** — YUP, Stewie Tweaks (66347), mesh fixes...
- **finish** — Stewie Tweaks INIs (GitHub: ModdingLinked/Stewie-Tweaks-INIs)

## Important data

- The correct file_id = **newest MAIN** by `uploaded_timestamp` (bug fixed: it used to pick the first one → 13 mods with an old version)
- **FNV 4GB Patcher**: use the **"FNV4GB for Proton"** file (Linux/Wine version)
- **JIP LN**: the plugin (v57.30) ≠ the INI (v56.24) — the guide needs the PLUGIN
- Stewie Tweaks: mod 66347 (90824 is hidden by the author)

## References

- [[Descarga de Mods]]
- [[Estado Actual]]
