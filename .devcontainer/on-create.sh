#!/usr/bin/env bash

set -euo pipefail

cp -n .env.codespaces .env.local

echo "Prebuilding Java artifacts..."
(cd java && mvn -DskipTests install)

echo "Syncing Python dependencies..."
(cd python && uv sync)

echo "Codespaces dependency setup complete."
