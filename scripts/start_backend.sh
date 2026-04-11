#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  echo "未找到 venv，请先在项目根目录创建 Python 虚拟环境。" >&2
  exit 1
fi

source "$PROJECT_ROOT/venv/bin/activate"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2:///pro_script_ai}"
export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"

if [[ "${UVICORN_RELOAD:-1}" == "1" ]]; then
  reload_flag=(--reload)
else
  reload_flag=()
fi

"$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/scripts/prepare_postgres.py"

exec "$PROJECT_ROOT/venv/bin/uvicorn" backend.main:app \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT" \
  "${reload_flag[@]}"
