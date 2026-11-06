#!/usr/bin/env bash
# =============================================================================
# Flujo completo de Docker: BUILD -> RUN -> TEST -> PUSH  (Linux / macOS / Git Bash)
#
# Uso:
#   ./scripts/docker_flow.sh <usuario_dockerhub> [version] [--push]
#   ./scripts/docker_flow.sh martaarias 1.0.0 --push
#
# Variables opcionales: IMAGE_NAME (tienda-online-api), HOST_PORT (8000)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."   # raíz del repositorio

DOCKERHUB_USER="${1:?Indica tu usuario de Docker Hub: ./scripts/docker_flow.sh <usuario> [version] [--push]}"
VERSION="${2:-1.0.0}"
PUSH="${3:-}"
IMAGE_NAME="${IMAGE_NAME:-tienda-online-api}"
HOST_PORT="${HOST_PORT:-8000}"

IMAGE="$(echo "$DOCKERHUB_USER" | tr '[:upper:]' '[:lower:]')/${IMAGE_NAME}"
SHA="$(git rev-parse --short HEAD)"
CONTAINER="tienda-api-smoke"
PYTHON="$(command -v python3 || command -v python)"

paso() { printf '\n\033[36m==> %s\033[0m\n' "$1"; }
limpiar() {
  echo; echo "--- Últimas líneas del log del contenedor ---"
  docker logs --tail 15 "$CONTAINER" 2>/dev/null || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}

# ---------------------------------------------------------------------- BUILD
paso "1/4 BUILD  -> ${IMAGE}:${VERSION}, ${IMAGE}:latest, ${IMAGE}:sha-${SHA}"
docker build --build-arg APP_VERSION="$VERSION" \
  -t "${IMAGE}:${VERSION}" -t "${IMAGE}:latest" -t "${IMAGE}:sha-${SHA}" .
docker image ls "$IMAGE"

# ---------------------------------------------------------------------- RUN
paso "2/4 RUN    -> contenedor '${CONTAINER}' en http://localhost:${HOST_PORT}"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" -p "${HOST_PORT}:8000" "${IMAGE}:${VERSION}" >/dev/null
trap limpiar EXIT

ESTADO=""
for _ in $(seq 1 30); do
  sleep 1
  ESTADO="$(docker inspect --format '{{.State.Health.Status}}' "$CONTAINER")"
  [ "$ESTADO" = "healthy" ] && break
done
echo "Estado de salud del contenedor: ${ESTADO}"
[ "$ESTADO" = "healthy" ] || { echo "El contenedor no llegó a estado healthy"; exit 1; }

# ---------------------------------------------------------------------- TEST
paso "3/4 TEST   -> smoke test + usuario no root"
"$PYTHON" scripts/smoke_test.py "http://localhost:${HOST_PORT}"
USUARIO="$(docker exec "$CONTAINER" whoami)"
echo "El proceso se ejecuta como: ${USUARIO}"
[ "$USUARIO" != "root" ] || { echo "El contenedor no debería ejecutarse como root"; exit 1; }

# ---------------------------------------------------------------------- PUSH
if [ "$PUSH" = "--push" ]; then
  paso "4/4 PUSH   -> Docker Hub (requiere 'docker login' previo)"
  docker push --all-tags "$IMAGE"
  echo "Imagen publicada: https://hub.docker.com/r/${IMAGE}"
else
  echo; echo "4/4 PUSH omitido. Añade --push para publicar en Docker Hub."
fi
echo; echo "Flujo completado correctamente."
