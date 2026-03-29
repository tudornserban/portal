# GameSeeds portal (static catalog)

Manifest-driven landing pages for games and apps, deployed to `/var/www/portal` on the Hetzner host.

- **Remote:** `git@gitlab.com:gamedev4680743/gameseeds-portal.git`
- **Workspace path:** clone as **`Separate/portal/`** (sibling of `GameSeeds/`, `tools/`, …).
- **Docs (paths, nginx, manifest schema):** [docs/PORTAL_AND_PAGES.md](docs/PORTAL_AND_PAGES.md)
- **Build:** `python3 tools/generate_site.py`
- **Deploy:** `bash tools/deploy-portal-production.sh` (requires SSH key; see docs)
