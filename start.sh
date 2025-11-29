#!/bin/bash

# Set strict mode
set -euo pipefail

echo
echo '  /$$$$$$  /$$$$$$$  /$$     /$$ /$$$$$$$  /$$$$$$$$ /$$$$$$  /$$   /$$'
echo ' /$$__  $$| $$__  $$|  $$   /$$/| $$__  $$|__  $$__//$$__  $$| $$  / $$'
echo '| $$  \__/| $$  \ $$ \  $$ /$$/ | $$  \ $$   | $$  | $$  \ $$|  $$/ $$/'
echo '| $$      | $$$$$$$/  \  $$$$/  | $$$$$$$/   | $$  | $$$$$$$$ \  $$$$/ '
echo '| $$      | $$__  $$   \  $$/   | $$____/    | $$  | $$__  $$  >$$  $$ '
echo '| $$    $$| $$  \ $$    | $$    | $$         | $$  | $$  | $$ /$$/\  $$'
echo '|  $$$$$$/| $$  | $$    | $$    | $$         | $$  | $$  | $$| $$  \ $$'
echo ' \______/ |__/  |__/    |__/    |__/         |__/  |__/  |__/|__/  |__/'
echo

# Set script directory and export PYTHONPATH
SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
export PYTHONPATH="$SCRIPT_DIR"  # Set the project root as PYTHONPATH

# Generate .env if missing and load it
[[ -e "$SCRIPT_DIR/.env" ]] || cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
source "$SCRIPT_DIR/.env"

# Print current script directory
echo "🛠️ CONFIG: Current script directory: $SCRIPT_DIR"
echo "🛠️ CONFIG: HIDE_CRITICAL_VALUES = $HIDE_CRITICAL_VALUES"
echo "🛠️ CONFIG: PRINT_LOGS = $PRINT_LOGS"

# Detect OS type
OS_TYPE="unknown"
case "$OSTYPE" in
  linux*)   OS_TYPE="linux" ;;
  darwin*)  OS_TYPE="mac" ;;
  cygwin*|msys*|win32*) OS_TYPE="windows" ;;
  *)        echo "❌ ERR: Unsupported OS: $OSTYPE"; exit 1 ;;
esac
echo "🛠️ CONFIG: Detected OS: $OS_TYPE"
echo

# Check for uv and install if missing
if ! command -v uv &> /dev/null; then
    echo "ℹ️ INF: uv is not installed. Installing uv..."
    if [ "$OS_TYPE" == "mac" ] || [ "$OS_TYPE" == "linux" ]; then
       curl -LsSf https://astral.sh/uv/install.sh | sh
    elif [ "$OS_TYPE" == "windows" ]; then
       powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    fi
    # Validate uv installation
    if ! command -v uv &> /dev/null; then
        echo "❌ ERR: uv installation failed. Please install uv manually."
        exit 1
    else
        echo "✅ SUC: uv is installed"
    fi
else
    echo "✅ SUC: uv is already installed"
fi

# Setup Python virtual environment and dependencies
echo "ℹ️ INF: Setting up virtual environment with uv..."
uv sync
echo "✅ SUC: Setup virtual environment"

# Start the application
echo
echo "ℹ️ INF: Starting the application..."
echo
uv run main.py