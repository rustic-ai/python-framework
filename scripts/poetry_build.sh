#!/bin/sh
# Build all modules in this project

set -x
set -u
set -e

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo "Building all modules in $PROJECT_ROOT"


DIST_DIR="${PROJECT_ROOT}/dist"

mkdir -p "$DIST_DIR"

. ${SCRIPT_DIR}/modules.sh

# Use IFS and set to simulate an array in sh
IFS=' '
set -- $MODULES
unset IFS

# Iterate through the modules
for module in "$@"; do
  # Check if the module should be skipped
  if [ "${SKIP_MODULE:-}" != "" ] && [ "$module" = "${SKIP_MODULE:-}" ]; then
    echo "Skipping module: $module"
    continue
  fi

  echo "Processing module: $module"
  pushd "${PROJECT_ROOT}/$module" || exit

  poetry install --without dev
  # Build package
  poetry build

  cp ./dist/*.whl ${DIST_DIR}/
  cp ./dist/*.tar.gz ${DIST_DIR}/
  popd || exit
done
