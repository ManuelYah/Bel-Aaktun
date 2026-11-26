#!/usr/bin/env bash
# Prepara los datos de prueba y corre la suite Selenium contra el sitio desplegado.
# Uso:  ./deploy/run-e2e.sh
# Requiere en .env: E2E_ADMIN_PASSWORD (min. 10) y E2E_ARTESANO_PASSWORD (min. 6)
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; [ -f .env ] && . ./.env; set +a
: "${E2E_ADMIN_PASSWORD:?Define E2E_ADMIN_PASSWORD en .env}"
: "${E2E_ARTESANO_PASSWORD:?Define E2E_ARTESANO_PASSWORD en .env}"

echo ">> Sembrando datos de prueba..."
docker compose exec -T \
  -e E2E_ADMIN_EMAIL -e E2E_ADMIN_PASSWORD -e E2E_ARTESANO_EMAIL -e E2E_ARTESANO_PASSWORD \
  backend python manage.py sembrar-e2e

mkdir -p e2e/reports
echo ">> Ejecutando pruebas Selenium..."
docker compose --profile e2e up -d selenium
docker compose --profile e2e run --rm e2e "$@"
echo ">> Reporte: e2e/reports/reporte.html"
