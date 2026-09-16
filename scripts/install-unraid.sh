#!/usr/bin/env bash
# Installatiescript voor Unraid.
#
# Gebruik: log in op Unraid via SSH (of de "User Scripts"-plugin) en draai:
#   bash install-unraid.sh
#
# Het script kan gewoon opnieuw gedraaid worden om te updaten naar de laatste
# commit: het haalt de nieuwste code op, bouwt een nieuwe image en herstart de
# container. Je data (database, sessies, thema-voorkeur) blijft altijd staan
# in $INSTALL_DIR/data, los van de broncode/image.
#
# Geen .env of omgevingsvariabelen nodig: inloggegevens (admin/admin) en de
# sessie-secret-key worden door de applicatie zelf beheerd. Wijzig het
# wachtwoord na de eerste keer inloggen via de "Account"-pagina in de app.

set -euo pipefail

# ---- Configuratie (pas aan indien gewenst) ---------------------------------
REPO_URL="${REPO_URL:-https://github.com/jayvenco/productivity-suite.git}"
INSTALL_DIR="${INSTALL_DIR:-/mnt/user/appdata/productivity-suite}"
CONTAINER_NAME="${CONTAINER_NAME:-productivity-suite}"
HOST_PORT="${HOST_PORT:-8887}"
IMAGE_TAG="${IMAGE_TAG:-productivity-suite:latest}"
# -----------------------------------------------------------------------------

SRC_DIR="$INSTALL_DIR/src"
DATA_DIR="$INSTALL_DIR/data"

echo "==> Installatiemap: $INSTALL_DIR"
mkdir -p "$DATA_DIR"

if [ -d "$SRC_DIR/.git" ]; then
  echo "==> Bestaande checkout gevonden, code bijwerken..."
  git -C "$SRC_DIR" fetch --depth 1 origin main
  git -C "$SRC_DIR" reset --hard origin/main
else
  echo "==> Repo clonen naar $SRC_DIR..."
  rm -rf "$SRC_DIR"
  git clone --depth 1 "$REPO_URL" "$SRC_DIR"
fi

echo "==> Docker image bouwen ($IMAGE_TAG)..."
docker build -t "$IMAGE_TAG" "$SRC_DIR"

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  echo "==> Bestaande container stoppen en verwijderen..."
  docker stop "$CONTAINER_NAME" >/dev/null
  docker rm "$CONTAINER_NAME" >/dev/null
fi

echo "==> Container starten op poort $HOST_PORT..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p "$HOST_PORT:8000" \
  -v "$DATA_DIR:/app/data" \
  "$IMAGE_TAG"

echo ""
echo "==> Klaar. Open http://<unraid-ip>:$HOST_PORT"
echo "    Standaard login: admin / admin — wijzig dit meteen via de Account-pagina."
