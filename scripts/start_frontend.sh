#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_ROOT="$PROJECT_ROOT/frontend"
cd "$FRONTEND_ROOT"

for node_bin in /opt/homebrew/opt/node@22/bin /opt/homebrew/bin /usr/local/bin; do
  if [[ -d "$node_bin" && ":$PATH:" != *":$node_bin:"* ]]; then
    export PATH="$node_bin:$PATH"
  fi
done

if ! command -v pnpm >/dev/null 2>&1 && command -v corepack >/dev/null 2>&1; then
  corepack enable >/dev/null 2>&1 || true
  corepack prepare pnpm@10.7.0 --activate >/dev/null 2>&1 || true
fi

if ! command -v pnpm >/dev/null 2>&1; then
  echo "未检测到 pnpm，请先安装并配置 pnpm。" >&2
  exit 1
fi

export FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"
export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://127.0.0.1:${BACKEND_PORT:-8000}}"

exec pnpm dev --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
