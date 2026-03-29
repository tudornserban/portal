# Portal and per-project pages (89.167.105.97)

This document is the **hand-off for infra agents** (workspace `AgentWorkflowAdaptations/agents/infra-agent.md` and per-project `.cursor/agents/infra-agent.md`). It describes how the **GameSeeds catalog site** (`portal/` repo) is built, what defaults apply to each **game/app page**, and how production nginx and deploy scripts fit together.

## Canonical locations

| Piece | Path |
|-------|------|
| Manifest (titles, copy, URLs, status) | `portal/data/manifest.json` |
| Shared CSS | `portal/templates/assets/portal.css` (copied into `www/assets/` on build) |
| Site generator | `portal/tools/generate_site.py` |
| Generated static output (deploy artifact) | `portal/www/` |
| Portal deploy script | `portal/tools/deploy-portal-production.sh` |
| DynamicGO web client deploy (existing) | `GameSeeds/DynamicGO/tools/deploy-www-production.sh` |
| Example nginx (IP + portal + DynamicGO) | `portal/deploy/nginx-ip-portal-default.conf.example` |

**Do not edit HTML under `www/` by hand** unless it is an emergency hotfix. Change `data/manifest.json` (or the generator) and re-run `generate_site.py`.

## URL layout (intended)

Production on the Hetzner IP is expected to **redirect HTTP → HTTPS** and serve the catalog on **TLS** using the existing **self-signed** cert at `/etc/ssl/certs/dynamicgo-selfsigned.crt` (browsers show a warning until you replace it with a proper certificate, e.g. Let’s Encrypt once DNS is ready).

When nginx uses `root /var/www/portal` on **443** (see `deploy/nginx-ip-portal-default.conf.example`):

| URL | Content |
|-----|---------|
| `http://89.167.105.97/…` | `301` → `https://89.167.105.97/…` |
| `https://89.167.105.97/` | Portal index (all games + apps) |
| `https://89.167.105.97/games/<id>/` | Project landing for that game |
| `https://89.167.105.97/apps/<id>/` | Project landing for that app |
| `https://89.167.105.97/games/dynamicgo/play/` | DynamicGO Phaser build (rsync from `GameSeeds/DynamicGO/www/`) |
| `/ws`, `/ws/ai/*` | Proxied to `DynamicGOServer` (unchanged) |

`<id>` is the `id` field in `manifest.json` (kebab-case).

## Manifest schema

Top level:

- **`site`** — strings: `title`, `header_label`, `tagline`, `footer_left`, `footer_right`.
- **`defaults`** — merged into every **`projects[]`** entry; any key on a project overrides the default.
- **`projects[]`** — one object per game or app.

Per-project fields:

| Field | Required | Purpose |
|-------|----------|---------|
| `id` | yes | URL slug (`dynamicgo`, `mouthpiece`, …). |
| `type` | yes | `game` or `app` (drives `/games/` vs `/apps/`). |
| `workspace_path` | yes | Where the repo lives in **Separate** (e.g. `GameSeeds/DynamicGO`, `Apps/MouthPiece`). Shown on the detail page for agents. |
| `title` | yes | HTML `<title>` and accessibility. |
| `short_title_html` | yes | Hero line breaks allowed (`<br>`). |
| `genre` | yes | Short subtitle (plain text; HTML-escaped). |
| `description_html` | yes | Body blurb; may include `<br>`. |
| `status` | no | `live`, `dev`, `soon`, or default **placeholder** — controls badge + card emphasis. |
| `accent` | no | `amber` or `teal` (buttons + card accent). |
| `listing_href` | no | Card link override (default: `/games/<id>/` or `/apps/<id>/`). |
| `play_url` | no | If set, “Play in browser” links here (e.g. `/games/dynamicgo/play/`). |
| `play_unavailable_message` | no | Shown under a disabled play control when `play_url` is empty. |
| `desktop_download_url` | no | If set, primary desktop download link (DMG/ZIP/AppImage URL, GitHub releases, etc.). |
| `desktop_download_label` | no | CTA label (default: “Download desktop app”). |
| `desktop_unavailable_message` | no | Shown when `desktop_download_url` is empty. |
| `repo_url` | no | Optional public repo link on the detail page. |

### Defaults (`defaults` in manifest)

Use **`defaults`** for shared placeholder copy so new rows stay small. Override per project when a title ships.

- Every project page includes a **desktop** CTA row: either a real link or a disabled button plus `desktop_unavailable_message` (e.g. Android-only apps should override the message).
- **`play_url`** is optional; games without a web build leave it empty and rely on `play_unavailable_message`.

## Individual page template (conceptual)

Each generated project page includes:

1. Back link to `/`.
2. Status line + hero (`short_title_html`, `genre`).
3. `description_html`.
4. **Actions:** “Play in browser” (link or disabled + note) and “Download desktop app” (link or disabled + note).
5. **Infra note:** `workspace_path` for humans/agents.
6. Optional **repo** link.
7. Shared footer from `site`.

The HTML is produced in `tools/generate_site.py` (`project_page_html`). When changing layout, update that function and run the generator.

## Build and deploy

From workspace (or portal root):

```bash
python3 portal/tools/generate_site.py
```

Deploy portal tree:

```bash
bash portal/tools/deploy-portal-production.sh
```

This runs the generator unless `SKIP_GENERATE=1`. It uses `rsync` to `REMOTE_WWW` (default `/var/www/portal` on `root@89.167.105.97`). SSH key default: `GameSeeds/DynamicGO/game`; override with `PORTAL_SSH_KEY`.

## DynamicGO web client (Phaser)

Legacy target: **`REMOTE_WWW=/var/www/dynamicgo`** (site root = game only).

**Portal-integrated target** (after nginx uses the example vhost):

```bash
cd GameSeeds/DynamicGO/client && npm run build
REMOTE_WWW=/var/www/portal/games/dynamicgo/play bash GameSeeds/DynamicGO/tools/deploy-www-production.sh
```

Ensure `manifest.json` keeps `play_url` as `/games/dynamicgo/play/` so the portal points at the same tree.

## nginx

See `deploy/nginx-ip-portal-default.conf.example` for a **default_server** on the IP that:

- Redirects **port 80** → **HTTPS** on the same host.
- Serves the portal from `/var/www/portal` on **443** with the self-signed cert (same paths as above).
- Aliases the Phaser build from `/var/www/dynamicgo` under `/games/dynamicgo/play/`.
- Preserves `/ws` proxying to `127.0.0.1:8080`.

If an older vhost still has `listen 443 ssl` with `server_name _` and `root /var/www/dynamicgo`, **disable** that site (`sites-enabled`) so it does not compete with the portal SSL server.

After changing vhosts: `nginx -t && systemctl reload nginx`.

## Adding a new game or app

1. Add a **`projects[]`** object (minimal row + overrides from `defaults`).
2. Run `generate_site.py` and confirm `www/games/<id>/index.html` or `www/apps/<id>/index.html`.
3. Deploy the portal.
4. If the title has a static web build, document its rsync target and add an nginx `location` or subpath consistent with `play_url`.

## Rollback

Portal: re-run deploy from a known-good commit’s `www/` (`SKIP_GENERATE=1` if you check out an older generated tree), or restore `/var/www/portal` from backup.

DynamicGO client: previous `www/` rsync; keep a tarball on the server if you need one-command rollback.
