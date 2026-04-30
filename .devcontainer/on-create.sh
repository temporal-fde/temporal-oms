#!/usr/bin/env bash

set -euo pipefail

cp -n .env.codespaces .env.local

JAVAC_EXECUTABLE="$(command -v javac)"

echo "Prebuilding Java artifacts with ${JAVAC_EXECUTABLE}..."
(cd java && mvn -DskipTests -Djavac.executable="${JAVAC_EXECUTABLE}" install)

echo "Syncing Python dependencies..."
(cd python && uv sync)

echo "Codespaces dependency setup complete."
