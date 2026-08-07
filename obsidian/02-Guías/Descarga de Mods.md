---
tags: [guia, descargas, nexus]
---
# Descarga de Mods

The `gestor_descargas.py` manager downloads the 53 Core mods with **states, retries and self-recovery**.

## The key discovery

The Nexus API gives download links **only to Premium**. The "Manual download" button of the site:

- Is in the **shadow DOM** of a web component (`<mod-download-modal>`) — invisible to normal DOM dumps
- The real endpoint (found by reading the Nexus JS bundle): **`/Download/?id={file_id}&game_id=130&source=ModPage`**

That page shows "Your file will be served via CDN" + a **Download** button — and it works for **free accounts**.

## Two page formats

| Text | Behavior |
|---|---|
| "Your download should automatically begin within a few seconds" | **Auto-download** (no button) |
| "Your file will be served via CDN" | **Download button** (it must be clicked) |

The manager handles both: waits 12s for the auto-download → if not, clicks the exact button (anchored to the "served via CDN" text).

## Manager robustness

- **Persisted states** in `estado.json`: `pending → downloading → ok/fail`
- **3 attempts** per mod with backoff (15s/30s)
- **Challenge waits** for Cloudflare (up to 60s)
- **Expired session detection** → automatic re-login → retry
- **Integrity verification** (`file` not-HTML, minimum size)
- Human rate limits (8-15s between mods)

## Commands

```bash
./vnv.sh download          # downloads what is pending
./vnv.sh estado            # verifies the 53 files
./venv/camoufox-python scripts/gestor_descargas.py --solo-fallidos
./venv/camoufox-python scripts/gestor_descargas.py --forzar --solo 57174
```

## References

- [[Login Nexus]] — the session that makes the download possible
- [[Descargas - Troubleshooting]] — solved problems
- [[Importar a MO2]] — next step
