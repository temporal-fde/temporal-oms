#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOL_VERSIONS_FILE="${TOOL_VERSIONS_FILE:-$ROOT_DIR/.tool-versions}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command '$1'. Install it before running this script."
}

plugin_installed() {
  local plugin="$1"
  asdf plugin list | grep -Fxq "$plugin"
}

main() {
  require_command asdf
  [[ -f "$TOOL_VERSIONS_FILE" ]] || die "Missing tool versions file: $TOOL_VERSIONS_FILE"

  echo "Installing asdf plugins from $TOOL_VERSIONS_FILE"
  echo ""

  local plugin version
  while read -r plugin version _; do
    if [[ -z "${plugin:-}" || "$plugin" == \#* ]]; then
      continue
    fi

    if plugin_installed "$plugin"; then
      echo "OK: $plugin already installed"
      continue
    fi

    echo "Adding asdf plugin: $plugin"
    asdf plugin add "$plugin"
  done < "$TOOL_VERSIONS_FILE"

  echo ""
  echo "asdf plugins are ready."
  echo "Next: asdf install"
}

main "$@"
