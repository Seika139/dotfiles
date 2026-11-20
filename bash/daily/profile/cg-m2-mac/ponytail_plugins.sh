#!/usr/bin/env bash

DAILY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "${DAILY_DIR}/common/update_agent_plugins.sh"
