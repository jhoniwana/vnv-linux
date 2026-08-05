---
tags: [guia, descargas, nexus]
---
# Descarga de Mods

El gestor `gestor_descargas.py` descarga los 53 mods del Core con **estados, reintentos y auto-recuperación**.

## El descubrimiento clave

La API de Nexus da links de descarga **solo a Premium**. El botón "Manual download" de la web:

- Está en el **shadow DOM** de un web component (`<mod-download-modal>`) — invisible para dumps DOM normales
- El endpoint real (encontrado leyendo el bundle JS de Nexus): **`/Download/?id={file_id}&game_id=130&source=ModPage`**

Esa página muestra "Your file will be served via CDN" + botón **Download** — y funciona para **cuentas gratis**.

## Dos formatos de página

| Texto | Comportamiento |
|---|---|
| "Your download should automatically begin within a few seconds" | **Auto-descarga** (no hay botón) |
| "Your file will be served via CDN" | **Botón Download** (hay que clickearlo) |

El gestor maneja ambos: espera 12s la auto-descarga → si no, clickea el botón exacto (anclado al texto "served via CDN").

## Robustez del gestor

- **Estados persistidos** en `estado.json`: `pendiente → descargando → ok/fallo`
- **3 intentos** por mod con backoff (15s/30s)
- **Espera de challenges** de Cloudflare (hasta 60s)
- **Detección de sesión expirada** → re-login automático → reintenta
- **Verificación de integridad** (`file` no-HTML, tamaño mínimo)
- Rate limits humanos (8-15s entre mods)

## Comandos

```bash
./vnv.sh download          # descarga lo pendiente
./vnv.sh estado            # verifica los 53 archivos
./venv/camoufox-python scripts/gestor_descargas.py --solo-fallidos
./venv/camoufox-python scripts/gestor_descargas.py --forzar --solo 57174
```

## Referencias

- [[Login Nexus]] — la sesión que hace posible la descarga
- [[Descargas - Troubleshooting]] — problemas resueltos
- [[Importar a MO2]] — siguiente paso
