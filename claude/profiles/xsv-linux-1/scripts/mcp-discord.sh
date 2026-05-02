#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${HOME}/.config/claude-discord-mcp/.env"
BIN="${HOME}/.npm-global/bin/mcp-discord"

if [[ ! -r "$ENV_FILE" ]]; then
  echo "mcp-discord wrapper: $ENV_FILE not readable" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

if [[ -z "${DISCORD_TOKEN:-}" ]]; then
  echo "mcp-discord wrapper: DISCORD_TOKEN not set in $ENV_FILE" >&2
  exit 1
fi

exec "$BIN"
