#!/usr/bin/env bash

# Serve temporary workshop API keys behind Basic Auth and a Cloudflare quick tunnel.
#
# This script is intended for short-lived instructor use. It reads API keys from
# local files, writes a temporary dotenv payload, exposes only that payload through
# Caddy Basic Auth, and publishes it via `cloudflared tunnel --url`.

set -euo pipefail

ANTHROPIC_KEY_FILE="${ANTHROPIC_KEY_FILE:-$HOME/.config/anthropic/tmp-replay-26-partners-day.key}"
OPENAI_KEY_FILE="${OPENAI_KEY_FILE:-$HOME/.config/openai/tmp-replay-26-partners-day.key}"
PORT="${WORKSHOP_SECRET_PORT:-7001}"
WORKSHOP_USER="${WORKSHOP_SECRET_USER:-workshop}"
WORKSHOP_PASS="${WORKSHOP_SECRET_PASSWORD:-}"
WORKSHOP_SECRET_PATH="${WORKSHOP_SECRET_PATH:-/replay26.env}"
WORKSHOP_SECRET_FILE=""
PIN_OUTPUT="${WORKSHOP_PIN_OUTPUT:-auto}"
PIN_LINES=26
PINNED_OUTPUT_ACTIVE=0

TMP_DIR=""
CADDY_PID=""
CLOUDFLARED_PID=""
TAIL_PID=""

die() {
  echo "error: $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command '$1'"
}

read_key_file() {
  local path="$1"
  local name="$2"

  [ -r "$path" ] || die "$name file is not readable: $path"

  local value
  value="$(tr -d '\r\n' < "$path")"
  [ -n "$value" ] || die "$name file is empty: $path"

  printf '%s' "$value"
}

can_pin_output() {
  case "$PIN_OUTPUT" in
    0|false|no) return 1 ;;
  esac

  [ -t 1 ] || return 1
  [ "${TERM:-}" != "dumb" ] || return 1
  command -v tput >/dev/null 2>&1 || return 1

  local rows
  rows="$(tput lines 2>/dev/null || echo 0)"
  [ "${rows:-0}" -ge 34 ] || return 1
}

enable_pinned_output() {
  can_pin_output || return 1

  # Reserve the top of the terminal for connection details. The access log
  # scrolls only in the region below it until cleanup resets the terminal.
  printf '\033[2J\033[H'
  printf '\033[%s;%sr' "$((PIN_LINES + 1))" "$(tput lines)"
  printf '\033[%s;1H' "$((PIN_LINES + 1))"
  PINNED_OUTPUT_ACTIVE=1
  return 0
}

reset_terminal_scroll_region() {
  if [ "$PINNED_OUTPUT_ACTIVE" -eq 1 ]; then
    printf '\033[r\033[%s;1H' "$(tput lines 2>/dev/null || echo 999)"
    PINNED_OUTPUT_ACTIVE=0
  fi
}

print_share_block() {
  local mode="${1:-plain}"

  if [ "$mode" = "pinned" ]; then
    printf '\033[H'
  fi

  cat <<EOF
================================================================================
Workshop API key service is running.

Share these with attendees:

  URL:      $TUNNEL_URL$WORKSHOP_SECRET_PATH
  Username: $WORKSHOP_USER
  Password: $WORKSHOP_PASS

Attendee command:

  curl -fsSL -u '$WORKSHOP_USER:$WORKSHOP_PASS' \\
    '$TUNNEL_URL$WORKSHOP_SECRET_PATH' \\
    -o /tmp/workshop.env && \\
  cp -n .env.codespaces .env.local && \\
  cat /tmp/workshop.env >> .env.local && \\
  rm /tmp/workshop.env

Logs are below. Press Ctrl-C to stop the tunnel and remove the temporary payload.
Revoke the Anthropic/OpenAI provider keys after the workshop.
================================================================================
EOF

  if [ "$mode" = "pinned" ]; then
    printf '\033[%s;1H' "$((PIN_LINES + 1))"
  fi
}

cleanup() {
  set +e
  reset_terminal_scroll_region
  if [ -n "${CLOUDFLARED_PID:-}" ]; then
    kill "$CLOUDFLARED_PID" >/dev/null 2>&1
    wait "$CLOUDFLARED_PID" >/dev/null 2>&1
  fi
  if [ -n "${CADDY_PID:-}" ]; then
    kill "$CADDY_PID" >/dev/null 2>&1
    wait "$CADDY_PID" >/dev/null 2>&1
  fi
  if [ -n "${TAIL_PID:-}" ]; then
    kill "$TAIL_PID" >/dev/null 2>&1
    wait "$TAIL_PID" >/dev/null 2>&1
  fi
  if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}

trap cleanup EXIT INT TERM

need_cmd caddy
need_cmd cloudflared
need_cmd curl
need_cmd lsof
need_cmd openssl
need_cmd tail
need_cmd tr

case "$WORKSHOP_SECRET_PATH" in
  /*) ;;
  *) die "WORKSHOP_SECRET_PATH must start with '/'" ;;
esac

if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  die "port $PORT is already in use; set WORKSHOP_SECRET_PORT to another port"
fi

ANTHROPIC_API_KEY_VALUE="$(read_key_file "$ANTHROPIC_KEY_FILE" "ANTHROPIC_API_KEY")"
OPENAI_API_KEY_VALUE="$(read_key_file "$OPENAI_KEY_FILE" "OPENAI_API_KEY")"

if [ -z "$WORKSHOP_PASS" ]; then
  WORKSHOP_PASS="replay26-$(openssl rand -hex 2)"
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/replay-26-workshop-secrets.XXXXXX")"
mkdir -p "$TMP_DIR/public"
chmod 700 "$TMP_DIR"
WORKSHOP_SECRET_FILE="$TMP_DIR/public$WORKSHOP_SECRET_PATH"
mkdir -p "$(dirname "$WORKSHOP_SECRET_FILE")"

cat > "$WORKSHOP_SECRET_FILE" <<EOF
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY_VALUE
OPENAI_API_KEY=$OPENAI_API_KEY_VALUE
EOF
chmod 600 "$WORKSHOP_SECRET_FILE"

PASSWORD_HASH="$(caddy hash-password --plaintext "$WORKSHOP_PASS")"

cat > "$TMP_DIR/Caddyfile" <<EOF
:$PORT {
  log {
    output file $TMP_DIR/access.log {
      mode 0600
      roll_disabled
    }
    format console
  }

  log_append auth_user {http.auth.user.id}

  header $WORKSHOP_SECRET_PATH Cache-Control "no-store, no-cache, max-age=0"

  basic_auth $WORKSHOP_SECRET_PATH {
    $WORKSHOP_USER $PASSWORD_HASH
  }

  handle $WORKSHOP_SECRET_PATH {
    root * $TMP_DIR/public
    file_server
  }

  handle {
    respond 404
  }
}
EOF

echo "Starting local Caddy server on http://127.0.0.1:$PORT ..."
caddy run --config "$TMP_DIR/Caddyfile" > "$TMP_DIR/caddy.log" 2>&1 &
CADDY_PID="$!"

echo "Waiting for local Caddy to serve $WORKSHOP_SECRET_PATH ..."
for attempt in $(seq 1 30); do
  if curl --max-time 2 -fsS -u "$WORKSHOP_USER:$WORKSHOP_PASS" "http://127.0.0.1:$PORT$WORKSHOP_SECRET_PATH" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$CADDY_PID" >/dev/null 2>&1; then
    echo ""
    echo "caddy log:"
    sed -n '1,160p' "$TMP_DIR/caddy.log" >&2
    die "Caddy exited before serving the key payload; see $TMP_DIR/caddy.log"
  fi
  if [ "$attempt" -eq 5 ] || [ "$attempt" -eq 10 ] || [ "$attempt" -eq 20 ]; then
    echo "  still waiting for Caddy (${attempt}s elapsed)"
  fi
  sleep 1
done

if ! curl --max-time 2 -fsS -u "$WORKSHOP_USER:$WORKSHOP_PASS" "http://127.0.0.1:$PORT$WORKSHOP_SECRET_PATH" >/dev/null; then
  echo ""
  echo "caddy log:"
  sed -n '1,160p' "$TMP_DIR/caddy.log" >&2
  die "Caddy did not become ready for $WORKSHOP_SECRET_PATH; see $TMP_DIR/caddy.log"
fi

echo "Starting Cloudflare quick tunnel ..."
cloudflared tunnel --url "http://127.0.0.1:$PORT" > "$TMP_DIR/cloudflared.log" 2>&1 &
CLOUDFLARED_PID="$!"

TUNNEL_URL=""
echo "Waiting for Cloudflare to assign a trycloudflare.com URL ..."
for attempt in $(seq 1 45); do
  TUNNEL_URL="$(grep -Eo 'https://[-a-zA-Z0-9.]+\.trycloudflare\.com' "$TMP_DIR/cloudflared.log" | head -n 1 || true)"
  if [ -n "$TUNNEL_URL" ]; then
    break
  fi
  if ! kill -0 "$CLOUDFLARED_PID" >/dev/null 2>&1; then
    echo ""
    echo "cloudflared log:"
    sed -n '1,160p' "$TMP_DIR/cloudflared.log" >&2
    die "cloudflared exited before creating a tunnel; see $TMP_DIR/cloudflared.log"
  fi
  if [ "$attempt" -eq 10 ] || [ "$attempt" -eq 20 ] || [ "$attempt" -eq 30 ]; then
    echo "  still waiting for tunnel URL (${attempt}s elapsed)"
  fi
  sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
  echo ""
  echo "cloudflared log:"
  sed -n '1,160p' "$TMP_DIR/cloudflared.log" >&2
  die "timed out waiting for tunnel URL; see $TMP_DIR/cloudflared.log"
fi

touch "$TMP_DIR/access.log"

if enable_pinned_output; then
  print_share_block pinned
else
  print_share_block
fi

echo "Instructor files:"
echo "  Local Caddy log:      $TMP_DIR/caddy.log"
echo "  Access log:           $TMP_DIR/access.log"
echo "  Cloudflared log:      $TMP_DIR/cloudflared.log"
echo "  Local key payload:    $WORKSHOP_SECRET_FILE"
echo ""
echo "Live access log:"
tail -f "$TMP_DIR/access.log" &
TAIL_PID="$!"

wait "$CLOUDFLARED_PID"
