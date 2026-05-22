#!/usr/bin/env bash

load_runtime_secret_env() {
  local project_dir="$1"
  local dotenv_file="${WORKSHOP_ENV_FILE:-$project_dir/.env.local}"
  local existing_anthropic="${ANTHROPIC_API_KEY:-}"
  local existing_openai="${OPENAI_API_KEY:-}"

  if [[ -f "$dotenv_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$dotenv_file"
    set +a
  fi

  if [[ -z "${ANTHROPIC_API_KEY:-}" && -n "$existing_anthropic" ]]; then
    export ANTHROPIC_API_KEY="$existing_anthropic"
  fi
  if [[ -z "${OPENAI_API_KEY:-}" && -n "$existing_openai" ]]; then
    export OPENAI_API_KEY="$existing_openai"
  fi
}

patch_secret_key() {
  local namespace="$1"
  local key="$2"
  local value="$3"
  local encoded

  encoded="$(printf '%s' "$value" | base64 | tr -d '\n')"
  kubectl patch secret temporal-oms-secrets \
    -n "$namespace" \
    --type=merge \
    -p "{\"data\":{\"$key\":\"$encoded\"}}" >/dev/null
}

apply_runtime_api_key_secrets() {
  local project_dir="$1"
  local namespaces=(
    temporal-oms-apps
    temporal-oms-processing
    temporal-oms-fulfillment
    temporal-oms-enablements
  )
  local keys=()

  load_runtime_secret_env "$project_dir"

  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    keys+=(ANTHROPIC_API_KEY)
  fi
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    keys+=(OPENAI_API_KEY)
  fi

  if [[ "${#keys[@]}" -eq 0 ]]; then
    echo "→ No ANTHROPIC_API_KEY or OPENAI_API_KEY found in .env.local/environment; leaving k8s runtime secrets unchanged"
    return 0
  fi

  echo "→ Applying runtime API keys to Kubernetes secrets (${keys[*]})..."
  local namespace key value
  for namespace in "${namespaces[@]}"; do
    for key in "${keys[@]}"; do
      value="${!key}"
      patch_secret_key "$namespace" "$key" "$value"
    done
  done
}
