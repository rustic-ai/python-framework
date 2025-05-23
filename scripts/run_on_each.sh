#!/bin/sh
# Runs the passed command in each specified module directory.

# Exit on error, treat unset variables as errors, and print commands
set -x
set -u
set -e

# --- Define Core Paths ---
# Absolute path to the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Project root directory (assuming it's the parent of the script's directory)
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Script directory: ${SCRIPT_DIR}"
echo "Project root: ${PROJECT_ROOT}"

# --- Capture User Command ---
# Ensure at least one argument (the command) is provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 <command to run in each module>" >&2
  echo "Example: $0 pwd" >&2
  echo "Example: $0 'ls -la'" >&2
  exit 1
fi
user_command="$*" # Capture all arguments passed to the script as a single command string
echo "User command to execute: '${user_command}'"

# --- Load Modules ---
# Source the modules.sh file, which is expected to set the MODULES variable.
# It should be located in the same directory as this script.
MODULES_FILE="${SCRIPT_DIR}/modules.sh"

if [ ! -f "${MODULES_FILE}" ]; then
  echo "Error: Modules file not found at '${MODULES_FILE}'" >&2
  exit 1
fi
# Source the file. Any variables it defines will be available here.
. "${MODULES_FILE}"

# Check if MODULES variable is set by the sourced file
if [ -z "${MODULES:-}" ]; then # The :- ensures the script doesn't fail if MODULES is truly unset (due to set -u)
  echo "Error: The 'MODULES' variable was not set or is empty in '${MODULES_FILE}'." >&2
  echo "Please ensure '${MODULES_FILE}' defines a space-separated list in a variable named MODULES." >&2
  exit 1
fi
echo "Modules to process: ${MODULES}"

# --- Process Modules ---
# Use IFS and the 'set' command to split the MODULES string into positional parameters ($1, $2, etc.)
# This effectively simulates an array for iterating in POSIX sh.
_OLD_IFS="$IFS" # Save the current Internal Field Separator
IFS=' '          # Set IFS to space for splitting the MODULES string
set -- $MODULES  # Unquoted $MODULES is intentional here for word splitting by IFS
IFS="$_OLD_IFS"  # Restore IFS to its previous value

echo "Iterating through modules..."
# "$@" now holds the individual module names derived from the MODULES string
for module in "$@"; do
  MODULE_PATH="${PROJECT_ROOT}/${module}"

  echo "" # Add a blank line for better readability per module
  echo "== Processing module: '${module}' =="
  echo "   Target module path: '${MODULE_PATH}'"

  # Change to the module directory.
  # With `set -e`, if cd fails, the script will exit automatically.
  # The `|| { ... }` block provides a more specific error message before exiting if cd were to fail.
  cd "${MODULE_PATH}" || {
    echo "Error: Failed to change directory to '${MODULE_PATH}'. Exiting." >&2
    exit 1 # Script would exit here anyway due to `set -e` if cd failed.
  }
  echo "   Current working directory: '$(pwd)'"

  echo "   Executing command in '${module}': sh -c \"${user_command}\""
  # Execute the user's command within the module directory.
  # The `|| true` ensures that if the user's command fails (exits with non-zero),
  # this script will NOT terminate (due to `set -e`) and will proceed to the next module.
  # This matches the original script's behavior.
  sh -c "${user_command}" || true
  echo "== Finished processing module: '${module}' =="
done

echo ""
echo "All specified modules processed."