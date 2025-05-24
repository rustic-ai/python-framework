#!/bin/sh
# Script to set up Poetry and install dependencies for the project

set -x # Print commands and their arguments as they are executed
set -u # Treat unset variables and parameters as an error
set -e # Exit immediately if a command exits with a non-zero status

# Determine the absolute path to the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"

# Determine the project root directory (assuming it's the parent of the script's directory)
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo "Project root identified as: ${PROJECT_ROOT}"
echo "Navigating to project root to execute Poetry commands..."

# Change to the project root directory. All subsequent commands
# that depend on being in the project root will work correctly.
cd "${PROJECT_ROOT}" || { echo "Failed to navigate to project root: ${PROJECT_ROOT}"; exit 1; }

echo "Currently in directory: $(pwd)"

echo "Adding poetry-plugin-mono-repo-deps to Poetry..."
poetry self add poetry-plugin-mono-repo-deps

echo "Installing project dependencies with Poetry..."
poetry install --without dev --all-extras --sync

echo "Poetry setup and dependency installation complete in ${PROJECT_ROOT}."