---
tags: [guia, mo2, importar]
---
# Importar a MO2

Convierte los archivos descargados al formato que Mod Organizer 2 entiende — **automáticamente**.

## Formato de MO2

```
~/.local/share/modorganizer2/
├── mods/<NombreMod>/            ← mod descomprimido
├── profiles/Default/
│   ├── modlist.txt              ← orden de mods (activos con +)
│   └── loadorder.txt            ← orden de plugins (lo genera LOOT)
└── downloads/                   ← archivos originales (referencia)
```

## Qué hace `importar_mo2.py`

1. Para cada archivo en `downloads/`: descomprime en `mods/<NombreMod>/`
   - `.7z`/`.rar` → 7z del sistema
   - `.zip` → stdlib de Python (seguro contra path traversal)
2. **Limpia basura**: `__MACOSX`, `.DS_Store`, `Thumbs.db`
3. **Aplana** la carpeta raíz única (muchos mods vienen envueltos)
4. **Borra carpetas vacías**
5. Escribe `modlist.txt` con el orden del manifest (setup → utilities → bugfix → finish), todos activos

## Probado

**53/53 mods importados** con estructura correcta:
- UIO → `nvse/plugins/ui_organizer.dll` + `uio/settings.ini`
- FaceGen (.rar) y MAC-10 (zip grande) también OK

## Comandos

```bash
./venv/camoufox-python scripts/importar_mo2.py              # detecta MO2
./venv/camoufox-python scripts/importar_mo2.py --dir ~/mo2  # directorio custom
```

## Referencias

- [[Descarga de Mods]] — de dónde vienen los archivos
- [[Conexión Steam]] — dónde vive MO2 en el flujo
