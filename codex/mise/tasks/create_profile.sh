#!/usr/bin/env bash

#MISE description="新しいプロファイルを作成 (Usage: mise run create_profile <profile-name>)"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE arg "[prof]" help="新しく作成するプロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source "${ROOT_DIR}/mise/common.sh"

PROFILE="${usage_prof:-}"
if [ -z "$PROFILE" ]; then
  {
    printf "%s\n" "❌ Error: profile name is required."
    printf "%s\n" "   Usage: mise run create_profile <profile-name>"
  } >&2
  exit 1
fi

PROFILE_PATH="$(codex_profile_path "$ROOT_DIR" "$PROFILE")"
if [ -d "$PROFILE_PATH" ]; then
  printf "%s\n" "❌ Error: Profile '$PROFILE' already exists" >&2
  exit 1
fi

printf "🦄 Creating new Codex profile: %s\n" "$PROFILE"
mkdir -p "$PROFILE_PATH"

cat >"$PROFILE_PATH/config.base.toml" <<'EOF'
model = "gpt-5.1-codex"
model_reasoning_effort = "high"
hide_agent_reasoning = true
network_access = true

EOF

cat >"$PROFILE_PATH/AGENTS.md" <<'EOF'
# Instructions for this Profile

## Project Context
<!-- Describe the type of projects this profile is used for -->

## Preferred Tools and Libraries
<!-- List commonly used tools, frameworks, or libraries for this environment -->

## Code Style Guidelines
<!-- Specify any coding standards or preferences -->

## Environment-Specific Notes
<!-- Add any machine-specific or environment-specific instructions -->

## Restrictions
<!-- Note any specific restrictions or security considerations -->
EOF

# custom-config のみ作成。
# NOTE: prompts/ と skills/ は APM 管理 (dotfiles/agents/) に移行済のため作成しない。
#   `mise run install`@agents/ で ~/.codex/{prompts,skills}/ に直接配備される。
mkdir -p "$PROFILE_PATH/custom-config"

printf "%s\n" "✅ Created profile '$PROFILE' at $PROFILE_PATH"
printf "%s\n" "📝 Edit settings in:"
printf "%s\n" "   - $PROFILE_PATH/config.base.toml"
printf "%s\n" "   - $PROFILE_PATH/config.local.toml (optional, git-ignored)"
printf "%s\n" "   - $PROFILE_PATH/AGENTS.md"
printf "%s\n" "   - $PROFILE_PATH/custom-config/"
