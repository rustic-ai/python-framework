#!/bin/bash

# Exit on error, treat unset variables as errors, and print commands
set -eu # 'e' for exit on error, 'u' for unset variables

# --- Define Core Paths ---
# Absolute path to the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root directory (assuming it's the parent of the script's directory)
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo "🚀 Initializing Test Environment"
echo "SCRIPT_DIR: ${SCRIPT_DIR}"
echo "PROJECT_ROOT: ${PROJECT_ROOT}"

# --- Cleanup Function ---
# This function will be called on script exit, interrupt, or termination
cleanup() {
    echo "🧹 Cleaning up..."
    # Note: pwd here will be PROJECT_ROOT if the cd command below succeeded
    echo "Current directory during cleanup: $(pwd)"
    if [ -n "${UVICORN_PID:-}" ]; then
        echo "Attempting to terminate Uvicorn server (PID: ${UVICORN_PID})..."
        kill "${UVICORN_PID}" 2>/dev/null || echo "Uvicorn server (PID: ${UVICORN_PID}) was not running or already stopped."
        wait "${UVICORN_PID}" 2>/dev/null # Wait for the process to actually terminate
    else
        echo "UVICORN_PID not set, skipping kill."
    fi
    echo "Uvicorn server shutdown process complete."

    DB_FILE="${PROJECT_ROOT}/integration_testing_app.db"
    if [ -f "${DB_FILE}" ]; then
        echo "Removing database file: ${DB_FILE}"
        rm -f -- "${DB_FILE}"
    else
        echo "Database file not found, skipping removal: ${DB_FILE}"
    fi
    echo "Cleanup finished."
}

# Set trap to call cleanup function
# This is set after PROJECT_ROOT is defined so cleanup() can use it
trap cleanup EXIT INT TERM

# --- Pre-flight Checks & Setup ---
echo "Ensuring no orphaned Uvicorn server is running..."
# The command string for pkill should match how Uvicorn is started
pkill -f "uvicorn rustic_ai.api_server.main:app" || true # Allow to fail if no process found

COVERAGE_DIR="${PROJECT_ROOT}/coverage"
echo "Setting up coverage directory: ${COVERAGE_DIR}"
rm -rf "${COVERAGE_DIR}"
mkdir -p "${COVERAGE_DIR}" # Use -p to avoid error if it somehow exists and is a dir

# --- Change to Project Root ---
# All subsequent project-specific commands will be run from here
echo "Changing working directory to PROJECT_ROOT: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}" || { echo "❌ FATAL: Failed to navigate to PROJECT_ROOT. Exiting."; exit 1; }
echo "Current working directory: $(pwd)"

# --- Start Uvicorn Server ---
UVICORN_DB_PATH="sqlite:///integration_testing_app.db" # Relative to PROJECT_ROOT now
UVICORN_COVERAGE_FILE="${COVERAGE_DIR}/coverage-int" # Absolute path
UVICORN_OUTPUT_FILE="${PROJECT_ROOT}/uvicorn_output.txt" # Absolute path

echo "Starting Uvicorn server in background..."
echo "DB Path: ${UVICORN_DB_PATH}"
echo "Coverage File: ${UVICORN_COVERAGE_FILE}"
echo "Output Log: ${UVICORN_OUTPUT_FILE}"

export OTEL_TRACES_EXPORTER=console
export OTEL_SERVICE_NAME=GuildCommunicationService
# Note: RUSTIC_METASTORE uses a relative path from PROJECT_ROOT
# coverage run's data-file uses an absolute path
# Output redirection also uses an absolute path
# The '-m rustic_ai.api_server.main' relies on being in PROJECT_ROOT
RUSTIC_METASTORE="${UVICORN_DB_PATH}" \
opentelemetry-instrument coverage run --source=. --context=INTEGRATION --data-file="${UVICORN_COVERAGE_FILE}" -m rustic_ai.api_server.main > "${UVICORN_OUTPUT_FILE}" 2>&1 &
UVICORN_PID=$!

echo "Uvicorn server started with PID ${UVICORN_PID}."

# Wait for the server to start (adjust as needed)
SERVER_WAIT_TIME=5
echo "Waiting ${SERVER_WAIT_TIME} seconds for the server to initialize..."
sleep "${SERVER_WAIT_TIME}"

# --- Run Tests ---
PYTEST_COVERAGE_FILE="${COVERAGE_DIR}/coverage-tests" # Absolute path

echo "🧪 Running tests..."
echo "Coverage File: ${PYTEST_COVERAGE_FILE}"

# PYTHONFAULTHANDLER is good for debugging crashes
# coverage run's data-file uses an absolute path
# pytest is run with '-m pytest', relying on being in PROJECT_ROOT
PYTHONFAULTHANDLER=true coverage run --source=. --context=TESTS --data-file="${PYTEST_COVERAGE_FILE}" -m pytest -vvvv --showlocals "$@"
# "$@" passes any arguments passed to this script directly to pytest

echo "✅ Test execution complete."
# The trap set earlier ensures that the cleanup function is called when the script exits normally here