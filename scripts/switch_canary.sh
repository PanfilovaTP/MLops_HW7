#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-90-10}"

case "$MODE" in
  90-10)
    cp nginx/canary-90-10.conf nginx/current.conf
    ;;
  50-50)
    cp nginx/canary-50-50.conf nginx/current.conf
    ;;
  100)
    cp nginx/canary-100.conf nginx/current.conf
    ;;
  rollback)
    cp nginx/rollback.conf nginx/current.conf
    ;;
  *)
    echo "Unknown mode: $MODE"
    echo "Use one of: 90-10, 50-50, 100, rollback"
    exit 1
    ;;
esac

docker compose -f docker-compose.canary.yml exec nginx nginx -s reload

echo "Canary mode switched to: $MODE"
