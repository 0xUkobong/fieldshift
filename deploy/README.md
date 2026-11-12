# Deploy Field Shift on fieldshift.cloud

This repo's recommended production layout serves a crawlable landing page at `https://fieldshift.cloud/` and the interactive Streamlit tool at `https://fieldshift.cloud/explorer/`. Caddy serves `robots.txt`, `sitemap.xml`, `llms.txt`, and brand assets directly, then proxies the explorer to Streamlit. This keeps crawler files and Open Graph metadata available without requiring a crawler to execute the Streamlit app.

## Host requirements

- A Linux host with a public IP and Python 3.11+.
- DNS `A` records for `fieldshift.cloud` and `www.fieldshift.cloud` pointing at that host. Add `AAAA` only if the host has working IPv6.
- TCP ports 80 and 443 reachable so Caddy can issue and renew HTTPS certificates.
- Caddy installed on the host.

## Install the app

1. Put this repository at `/srv/fieldshift`, owned by a dedicated `fieldshift` user. Keep `/srv/fieldshift/data` on persistent storage; it contains the SQLite field records and climate/place caches.
2. Create the environment and install runtime dependencies:

   ```sh
   cd /srv/fieldshift
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

3. Install `deploy/fieldshift.service` as `/etc/systemd/system/fieldshift.service`, then start it:

   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable --now fieldshift
   ```

4. Copy `deploy/Caddyfile` to `/etc/caddy/Caddyfile`. The file expects the checkout at `/srv/fieldshift` and Streamlit on `127.0.0.1:8501`.
5. Validate and reload Caddy:

   ```sh
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   ```

The service sets `FIELDSHIFT_PUBLIC_URL` and `FIELDSHIFT_APP_BASE_PATH` for production canonicals and asset links. Local `streamlit run app.py` remains mounted at `/` when those variables are absent.

## Before announcing the site

- Check `https://fieldshift.cloud/robots.txt`, `/sitemap.xml`, and `/llms.txt` return their plain-text or XML files, not the Streamlit shell.
- Check `/assets/favicon.ico`, `/assets/logo.png`, and `/assets/og.png` return the expected files.
- Check `/explorer/` loads, and its title, canonical, Open Graph image, and description use `fieldshift.cloud`.
- Set a record-retention period and publish a service contact and deletion process for hosted farm records.
- Submit `https://fieldshift.cloud/sitemap.xml` in Google Search Console and Bing Webmaster Tools after verifying domain ownership.
