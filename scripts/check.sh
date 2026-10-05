#!/usr/bin/env bash
# EyeSite quality check script for Linux / macOS
# Runs pytest then ruff

set -e

echo "=== Running pytest ==="
pytest

echo ""
echo "=== Running ruff check ==="
ruff check .

echo ""
echo "[SUCCESS] All checks passed!"
