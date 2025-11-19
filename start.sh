#!/bin/bash

# Set strict mode
set -euo pipefail

echo
echo '  /$$$$$$  /$$$$$$$  /$$$$$$$  /$$     /$$ /$$$$$$$$ /$$$$$$  /$$   /$$'
echo ' /$$__  $$| $$__  $$| $$__  $$|  $$   /$$/|__  $$__//$$__  $$| $$  / $$'
echo '| $$  \__/| $$  \ $$| $$  \ $$ \  $$ /$$/    | $$  | $$  \ $$|  $$/ $$/'
echo '| $$      | $$$$$$$/| $$$$$$$/  \  $$$$/     | $$  | $$$$$$$$ \  $$$$/ '
echo '| $$      | $$__  $$| $$____/    \  $$/      | $$  | $$__  $$  >$$  $$ '
echo '| $$    $$| $$  \ $$| $$          | $$       | $$  | $$  | $$ /$$/\  $$'
echo '|  $$$$$$/| $$  | $$| $$          | $$       | $$  | $$  | $$| $$  \ $$'
echo ' \______/ |__/  |__/|__/          |__/       |__/  |__/  |__/|__/  |__/'
echo

# Set script directory and export PYTHONPATH
SCRIPT_DIR=$(cd -- "$(dirname "$0")" && pwd)
export PYTHONPATH="$SCRIPT_DIR"  # Set the project root as PYTHONPATH

# Generate .env if missing and load it
[[ -e "$SCRIPT_DIR/.env" ]] || cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
source "$SCRIPT_DIR/.env"

# Print current script directory
echo "ℹ️ INF: Current script directory: $SCRIPT_DIR"

# Detect OS type
OS_TYPE="unknown"
case "$OSTYPE" in
  linux*)   OS_TYPE="linux" ;;
  darwin*)  OS_TYPE="mac" ;;
  cygwin*|msys*|win32*) OS_TYPE="windows" ;;
  *)        echo "❌ ERR: Unsupported OS: $OSTYPE"; exit 1 ;;
esac
echo "ℹ️ INF: Detected OS: $OS_TYPE"

# Helper function to install packages using available package managers
install_package() {
  local package="$1"
  if [ "$OS_TYPE" == "mac" ]; then
    if command -v brew &> /dev/null; then
      brew install "$package"
    else
      echo "❌ ERR: Homebrew is not installed. Please install Homebrew and retry."
      exit 1
    fi
  elif [ "$OS_TYPE" == "linux" ]; then
    if command -v apt-get &> /dev/null; then
      sudo apt-get update && sudo apt-get install -y "$package"
    elif command -v yum &> /dev/null; then
      sudo yum install -y "$package"
    else
      echo "❌ ERR: Supported package manager not found. Please install $package manually."
      exit 1
    fi
  elif [ "$OS_TYPE" == "windows" ]; then
    if command -v winget &> /dev/null; then
      winget install --id "$package" -e
    else
      echo "❌ ERR: winget not found. Please install $package manually."
      exit 1
    fi
  fi
}

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
if [[ ! -d .venv ]]; then
    echo "ℹ️ INF: Creating virtual environment with uv..."
    uv venv .venv
    echo "✅ SUC: Created virtual environment"
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies from pyproject.toml
echo "ℹ️ INF: Installing dependencies from pyproject.toml file..."
uv pip install --upgrade .

# Start the application
echo
echo "ℹ️ INF: Starting the application..."
echo
uv run main.py