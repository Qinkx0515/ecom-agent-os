#!/usr/bin/env bash

set -e


BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"


echo
echo "================================="
echo "CommercePilot Demo"
echo "================================="
echo


echo "[1] Health"
curl -s \
  "${BASE_URL}/health"

echo
echo
echo


echo "[2] Analytics"
curl -N \
  -X POST \
  "${BASE_URL}/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "request":
    "最近30天耳机品类GMV是多少？"
  }'

echo
echo