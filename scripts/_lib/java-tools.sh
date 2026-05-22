#!/usr/bin/env bash

resolve_javac_executable() {
  if [[ -n "${JAVAC_EXECUTABLE:-}" ]]; then
    if [[ -x "$JAVAC_EXECUTABLE" ]]; then
      printf '%s\n' "$JAVAC_EXECUTABLE"
      return 0
    fi

    echo "ERROR: JAVAC_EXECUTABLE is set but is not executable: $JAVAC_EXECUTABLE" >&2
    return 1
  fi

  if [[ -n "${JAVA_HOME:-}" && -x "$JAVA_HOME/bin/javac" ]]; then
    printf '%s\n' "$JAVA_HOME/bin/javac"
    return 0
  fi

  if command -v javac >/dev/null 2>&1; then
    command -v javac
    return 0
  fi

  echo "ERROR: javac not found. Install JDK 21 before running this script." >&2
  return 1
}
