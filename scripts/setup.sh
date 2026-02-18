#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${APP_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-8000}"
WORKERS="${WORKERS:-2}"

printf "\n[1/4] Preparing Python environment...\n"
cd "${APP_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

printf "\n[2/4] Installing Python dependencies...\n"
pip install --upgrade pip wheel
pip install -r requirements.txt

printf "\n[3/4] Creating runtime folders...\n"
mkdir -p data data/documents logs

printf "\n[4/4] Setup complete.\n"
echo ""
echo "Run the app with:"
echo "  source ${VENV_DIR}/bin/activate"
echo "  python server.py"
echo ""
echo "Production command (behind Nginx):"
echo "  source ${VENV_DIR}/bin/activate"
echo "  gunicorn --workers ${WORKERS} --bind ${APP_HOST}:${APP_PORT} server:app"
echo ""
echo "Nginx template: config/nginx/docconvert-pro.conf"
