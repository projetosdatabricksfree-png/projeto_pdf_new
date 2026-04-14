#!/bin/bash
# Pre-Flight Validator — Quality Utility Script
# Wraps Ruff execution inside the Docker worker container.

CONTAINER_NAME="projeto_validador-worker-1"

print_usage() {
    echo "Usage: ./scripts/setup_quality.sh [check|fix|format]"
    echo ""
    echo "Commands:"
    echo "  check   Run ruff linter check (read-only)"
    echo "  fix     Run ruff linter and auto-fix violations"
    echo "  format  Run ruff formatter"
}

if [ "$1" == "check" ]; then
    echo "🚀 Running Ruff Linter (Check)..."
    docker exec $CONTAINER_NAME ruff check /app/
elif [ "$1" == "fix" ]; then
    echo "🔨 Running Ruff Linter (Fix)..."
    docker exec $CONTAINER_NAME ruff check /app/ --fix
elif [ "$1" == "format" ]; then
    echo "🎨 Running Ruff Formatter..."
    docker exec $CONTAINER_NAME ruff format /app/
else
    print_usage
fi
