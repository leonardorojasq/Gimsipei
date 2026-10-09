#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/Gimsipei"
APP_NAME="gimsipei-app"
CONTAINER_NAME="Gimsipei"
PORT="5010"
BRANCH="main"
UPLOADS_DIR="/opt/Gimsipei/uploads"
APP_UPLOADS_PATH="/app/src/static/uploads"
ENV_FILE="/opt/Gimsipei/.env"

cd "$APP_DIR"

ENV_BACKUP="$(mktemp)"
[[ -f "$ENV_FILE" ]] && cp "$ENV_FILE" "$ENV_BACKUP"

echo "📥 Obteniendo últimos cambios de $BRANCH..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

[[ -f "$ENV_BACKUP" ]] && mv "$ENV_BACKUP" "$ENV_FILE"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ No se encontró $ENV_FILE. Crea el archivo con tus variables de entorno y vuelve a correr el script."
  exit 1
fi

SHORT_SHA="$(git rev-parse --short HEAD)"
TAG="${SHORT_SHA}-$(date +%Y%m%d%H%M%S)"

echo "🔨 Construyendo imagen $APP_NAME:$TAG..."
docker build -t "$APP_NAME:$TAG" -t "$APP_NAME:latest" .

echo "🛑 Deteniendo contenedor actual..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "🚀 Iniciando nuevo contenedor..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart always \
  -p "${PORT}:${PORT}" \
  --env-file "$ENV_FILE" \
  -v "${UPLOADS_DIR}:${APP_UPLOADS_PATH}" \
  "$APP_NAME:$TAG"

echo "🧹 Limpiando imágenes dangling..."
docker image prune -f

echo ""
echo "✅ Despliegue completado"
echo "   Imagen actual: $APP_NAME:$TAG"
echo "   Para rollback: docker run -d --name $CONTAINER_NAME -p ${PORT}:${PORT} --env-file $ENV_FILE -v ${UPLOADS_DIR}:${APP_UPLOADS_PATH} $APP_NAME:<tag-anterior>"
echo ""
docker ps --filter "name=$CONTAINER_NAME"

if [[ ! -f "$ENV_FILE" && -f "$APP_DIR/.env.example" ]]; then
  cp "$APP_DIR/.env.example" "$ENV_FILE"
  echo "⚠️ .env creado desde .env.example. Edíta los valores y vuelve a correr el script."
fi