#!/usr/bin/env bash
# Deploy generated portal static site to production nginx document root.
# Server: root@89.167.105.97 — SSH key: sibling repo GameSeeds/DynamicGO/game unless overridden.
#
# Usage (from workspace root):
#   bash portal/tools/deploy-portal-production.sh
#
# Optional:
#   SKIP_GENERATE=1           — do not run generate_site.py (deploy existing www/)
#   PORTAL_SSH_KEY=/path/key  — override private key
#   REMOTE_USER_HOST=user@host
#   REMOTE_WWW=/var/www/portal
#
# Binaries under www/downloads/** (e.g. DynamicGO *.zip from deploy-www-production.sh) are not
# in the git-generated tree; rsync --delete would remove them unless excluded.
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORTAL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_KEY="$PORTAL_ROOT/../GameSeeds/DynamicGO/game"
KEY="${PORTAL_SSH_KEY:-$DEFAULT_KEY}"
REMOTE_USER_HOST="${REMOTE_USER_HOST:-root@89.167.105.97}"
REMOTE_WWW="${REMOTE_WWW:-/var/www/portal}"

if [[ ! -f "$KEY" ]]; then
  echo "deploy-portal-production: missing SSH private key: $KEY" >&2
  echo "Set PORTAL_SSH_KEY or use the DynamicGO deploy key at GameSeeds/DynamicGO/game (sibling of portal/)" >&2
  exit 1
fi

if [[ "${SKIP_GENERATE:-0}" != "1" ]]; then
  python3 "$SCRIPT_DIR/generate_site.py"
fi

if [[ ! -d "$PORTAL_ROOT/www" ]]; then
  echo "deploy-portal-production: missing $PORTAL_ROOT/www — run generate_site.py" >&2
  exit 1
fi

echo "Deploying $PORTAL_ROOT/www/ → $REMOTE_USER_HOST:$REMOTE_WWW/"
rsync -avz --delete \
  --exclude='downloads/*/*.zip' \
  --exclude='downloads/*/*.dmg' \
  --exclude='downloads/*/*.AppImage' \
  --exclude='downloads/*/*.appimage' \
  -e "ssh -i \"$KEY\" -o IdentitiesOnly=yes" \
  "$PORTAL_ROOT/www/" "$REMOTE_USER_HOST:$REMOTE_WWW/"
echo "Done."
