# 🎁 VNV Linux — Guía para un amigo

Instalador 100% automático del Core de **Viva New Vegas** en Linux + Steam.

## Qué necesitás

- Linux (Arch, Debian/Ubuntu, Fedora, openSUSE)
- Fallout: New Vegas comprado en Steam (instalado)
- Una cuenta gratis de Nexus Mods (para descargar los mods)

## Pasos (en orden)

```bash
# 1. Cloná el repo
git clone https://github.com/jhoniwana/vnv-linux
cd vnv-linux

# 2. Setup del entorno (deps del sistema + Python + Camoufox)
./vnv.sh setup

# 3. Login a Nexus (se abre un navegador anti-detección; entrá con TU cuenta)
./vnv.sh login

# 4. Guardá tu API key de Nexus (https://www.nexusmods.com/settings/api-keys)
./vnv.sh config

# 5. Guardá tu email+contraseña (para el re-login automático)
./vnv.sh credenciales

# 6. Descargá los 55 mods (1.1 GB — tarda un rato, es automático)
./vnv.sh download

# 7. Verificá que todo esté OK
./vnv.sh estado

# 8. Instalá todo (MO2 + mods + root mods + INIs) — necesita Steam cerrado
./vnv.sh install

# 9. ¡A jugar!
./vnv.sh run
```

## Opcional (cómodo)

- **Desde Steam**: `./vnv.sh steam-add` agrega "Fallout New Vegas (VNV)" a tu biblioteca
  (abre el gestor MO2 → botón Run → juego).
- **Interfaz web**: `./vnv.sh ui` (wizard sin terminal).

## Notas importantes

- **Los mods NO están en el repo** (copyright de sus autores). Se descargan con TU
  cuenta de Nexus automáticamente.
- El juego corre en **partida nueva** — los saves de otra instalación no son compatibles.
- Si Steam actualiza el juego (verify), corré `./vnv.sh root` después (re-aplica 4GB,
  BSAs y Fixed ESMs).
- Sprint y QOL: JAM se configura en el juego (ESC → Mod Configuration → Just Assorted Mods).
- Cualquier duda: el log de errores está en `HANDOFF.md` y `BRAIN.md`.
