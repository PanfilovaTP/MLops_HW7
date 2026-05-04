#!/usr/bin/env bash
set -euo pipefail

echo "v1 health:"
curl -s http://localhost:8001/health && echo

echo "v2 health:"
curl -s http://localhost:8002/health && echo

echo "nginx canary health:"
curl -s http://localhost:18080/health && echo

echo "predict via nginx:"
curl -s -X POST http://localhost:18080/predict \
  -H "Content-Type: application/json" \
  -d '{"x": [1, 2, 3]}' && echo
