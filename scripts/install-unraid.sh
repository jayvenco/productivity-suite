#!/usr/bin/env bash
# Productivity Suite installeren/updaten op Unraid (beheerbaar vanuit de Docker-tab).
#
# Haalt de image op uit GHCR, maakt de container aan met Unraid-labels (icoon, WebUI-knop)
# en schrijft een gebruikerstemplate zodat "Edit" in de Docker-tab werkt.
# Opnieuw draaien = updaten; je data in <appdata>/data blijft staan.
#
# Overschrijfbaar via omgevingsvariabelen, bv.:  HOST_PORT=9000 bash install-unraid.sh
set -euo pipefail

NAME="${CONTAINER_NAME:-productivity-suite}"
IMAGE="${IMAGE:-ghcr.io/jayvenco/productivity-suite}"
TAG="${IMAGE_TAG:-latest}"
HOST_PORT="${HOST_PORT:-8887}"
CONTAINER_PORT=8000
APPDATA="${APPDATA:-/mnt/user/appdata/${NAME}}"
RAW="${RAW_URL:-https://raw.githubusercontent.com/jayvenco/productivity-suite/main/unraid}"
TEMPLATE_DIR="${TEMPLATE_DIR:-/boot/config/plugins/dockerMan/templates-user}"
# Optionele app-instellingen. Staan ze al op de bestaande container (bv. via de Docker-tab), dan
# worden ze bij een update overgenomen; een waarde die je hier meegeeft wint.
OPTIONAL_VARS="WHISPER_SERVICE_URL WHISPER_MODEL SNIPPETS_GIT_REPO SNIPPETS_GIT_TOKEN SNIPPETS_GIT_BRANCH SNIPPETS_GIT_AUTO MONTHLY_BACKUP_KEEP BACKUP_ENABLED BACKUP_KEEP DEFAULT_THEME"

log() { printf '==> %s\n' "$*"; }

command -v docker >/dev/null 2>&1 || { echo "Docker niet gevonden. Draai dit script op de Unraid-server." >&2; exit 1; }

# 1. Appdata-mappen (Unraid-standaard eigenaar nobody:users = 99:100)
log "Mappen aanmaken in ${APPDATA}"
mkdir -p "${APPDATA}/data"
chown -R 99:100 "${APPDATA}" 2>/dev/null || true

# 2. Optioneel inloggen bij GHCR (alleen nodig als het package privé is)
if [ -n "${GHCR_USER:-}" ] && [ -n "${GHCR_TOKEN:-}" ]; then
  log "Inloggen bij ghcr.io als ${GHCR_USER}"
  printf '%s' "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USER}" --password-stdin
fi

# 3. Image ophalen
if [ "${SKIP_PULL:-0}" = "1" ]; then
  log "Pull overgeslagen (SKIP_PULL=1), lokale image ${IMAGE}:${TAG} wordt gebruikt"
else
  log "Image ophalen: ${IMAGE}:${TAG}"
  docker pull "${IMAGE}:${TAG}"
fi

# 4. Bestaande container vervangen (data staat op het volume en blijft behouden)
if docker inspect "${NAME}" >/dev/null 2>&1; then
  OLD_ENV="$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "${NAME}" 2>/dev/null || true)"
  for v in ${OPTIONAL_VARS}; do
    if [ -z "${!v:-}" ]; then
      old="$(printf '%s\n' "${OLD_ENV}" | sed -n "s/^${v}=//p" | head -n 1)"
      [ -n "${old}" ] && printf -v "${v}" '%s' "${old}" && log "Bestaande instelling ${v} overgenomen"
    fi
  done
  log "Bestaande container '${NAME}' stoppen en verwijderen (data blijft staan)"
  docker stop "${NAME}" >/dev/null 2>&1 || true
  docker rm "${NAME}" >/dev/null
fi

ENV_ARGS=()
for v in ${OPTIONAL_VARS}; do
  [ -n "${!v:-}" ] && ENV_ARGS+=(-e "${v}=${!v}")
done

# 5. Container starten, met labels zodat Unraid 'm als eigen container toont
log "Container '${NAME}' starten op poort ${HOST_PORT}"
docker run -d \
  --name "${NAME}" \
  --restart unless-stopped \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  -v "${APPDATA}/data:/app/data" \
  ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} \
  --label "net.unraid.docker.managed=dockerman" \
  --label "net.unraid.docker.webui=http://[IP]:[PORT:${CONTAINER_PORT}]/" \
  --label "net.unraid.docker.icon=${RAW}/icon.png" \
  "${IMAGE}:${TAG}" >/dev/null

# 6. Gebruikerstemplate schrijven zodat Edit in de Docker-tab de juiste waarden toont
if [ -d "${TEMPLATE_DIR}" ]; then
  log "Template opslaan in ${TEMPLATE_DIR}/my-${NAME}.xml"
  TMP="$(mktemp)"
  if command -v curl >/dev/null 2>&1 && curl -fsSL "${RAW}/productivity-suite.xml" -o "${TMP}"; then
    # Waarden veilig maken voor gebruik in sed (& \ | / escapen) en in XML (& < >)
    esc() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' -e 's/[\\&|]/\\&/g'; }
    setcfg() { sed -i -E "s|(Target=\"$1\"[^>]*>)[^<]*(</Config>)|\1$(esc "$2")\2|" "${TMP}"; }
    sed -i -E "s|<Name>[^<]*</Name>|<Name>$(esc "${NAME}")</Name>|" "${TMP}"
    setcfg "8000" "${HOST_PORT}"
    setcfg "/app/data" "${APPDATA}/data"
    for v in ${OPTIONAL_VARS}; do
      [ -n "${!v:-}" ] && setcfg "${v}" "${!v}"
    done
    install -m 600 "${TMP}" "${TEMPLATE_DIR}/my-${NAME}.xml"
  else
    echo "Waarschuwing: template kon niet worden gedownload; sla ik over (de container werkt wel)." >&2
  fi
  rm -f "${TMP}"
else
  log "Geen dockerMan-map gevonden (geen Unraid?); template overgeslagen"
fi

# 7. Wachten tot de healthcheck groen is
log "Wachten tot de app gezond is..."
STATUS="starting"
for _ in $(seq 1 60); do
  STATUS="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${NAME}" 2>/dev/null || echo missing)"
  case "${STATUS}" in healthy|running) break ;; unhealthy|exited|dead|missing) break ;; esac
  sleep 2
done
if [ "${STATUS}" != "healthy" ] && [ "${STATUS}" != "running" ]; then
  echo "Container is niet gezond (status: ${STATUS}). Laatste logregels:" >&2
  docker logs --tail 30 "${NAME}" >&2 || true
  exit 1
fi

IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
log "Klaar! Open http://${IP:-<unraid-ip>}:${HOST_PORT}/"
echo "    Eerste login: admin / admin (wijzig dit direct via Account)."
echo "    Beheer vanaf nu ook via de Docker-tab (Edit, logs, autostart, updaten)."
