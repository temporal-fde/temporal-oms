#!/usr/bin/env bash

set -euo pipefail

cp -n .env.codespaces .env.local

if [[ -d .devcontainer/k9s ]]; then
  echo "Installing k9s config..."
  mkdir -p "$HOME/.config/k9s"
  cp -R .devcontainer/k9s/. "$HOME/.config/k9s/"
fi

. scripts/_lib/java-tools.sh

JAVAC_EXECUTABLE="$(resolve_javac_executable)"

echo "Prebuilding Java artifacts with ${JAVAC_EXECUTABLE}..."
(cd java && mvn -DskipTests -Djavac.executable="${JAVAC_EXECUTABLE}" install)

echo "Syncing Python dependencies..."
(cd python && uv sync)

echo "Codespaces dependency setup complete."
