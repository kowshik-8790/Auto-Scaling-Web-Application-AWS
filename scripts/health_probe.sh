#!/usr/bin/env bash
# ==============================================================================
# Continuous Health & Multi-AZ Round-Robin Probe for Application Load Balancer
# ==============================================================================
set -euo pipefail

ALB_URL="${1:-}"

if [[ -z "$ALB_URL" ]]; then
    echo "Usage: ./health_probe.sh <ALB_HTTP_URL>"
    exit 1
fi

echo "=========================================================="
echo " Probing AWS Application Load Balancer: $ALB_URL"
echo " Press Ctrl+C to terminate probe."
echo "=========================================================="

while true; do
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    RESPONSE=$(curl -s --connect-timeout 2 "${ALB_URL}/health" || echo '{"status":"error"}')
    echo "[$TIMESTAMP] Health Status: $RESPONSE"
    sleep 1
done
