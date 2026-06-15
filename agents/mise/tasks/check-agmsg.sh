#!/bin/bash

#MISE description="agmsg がインストール済みか / 各 CLI 連携が wiring 済みかを確認する"
#MISE depends=["sqlite3-available"]
#MISE quiet=true
#USAGE flag "--cmd <cmd>" help="確認するコマンド名 (default: agmsg)。install-agmsg と揃える"

# install-agmsg.sh が必ず置く `.agmsg` マーカー (cmd 名を変えても固定名) を正準シグナルに
# 「入っているか」を判定する。status.sh の external 判定と同じ基準。
# install されていれば exit 0、未 install なら exit 1 を返すので guard/CI 兼用で使える。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

CMD="${usage_cmd:-agmsg}"
SKILL_DIR="${HOME}/.agents/skills/${CMD}"
SKILL_MARKER="${SKILL_DIR}/.agmsg"

# install-agmsg.sh の pin SHA を再利用 (二重管理を避ける)。
PINNED_REF="$(rg -o 'DEFAULT_AGMSG_REF="([0-9a-f]+)"' -r '$1' "${ROOT_DIR}/mise/tasks/install-agmsg.sh" 2>/dev/null || true)"

green() { printf "\033[1;32m%s\033[0m" "$1"; }
red() { printf "\033[1;31m%s\033[0m" "$1"; }
dim() { printf "\033[2m%s\033[0m" "$1"; }

ok() { printf "  %s %s\n" "$(green "✓")" "$1"; }
ng() { printf "  %s %s\n" "$(red "✘")" "$1"; }

printf "%s\n" "🛰️  agmsg status (cmd: ${CMD})"
printf "%s\n" "   $(dim "pin (install-agmsg): ${PINNED_REF:-不明}")"
printf "\n"

if [ ! -f "$SKILL_MARKER" ]; then
  ng "未インストール: ${SKILL_MARKER} が見つかりません"
  printf "\n%s\n" "   → 導入するには: mise run install-agmsg"
  exit 1
fi

ok "インストール済み: ${SKILL_DIR}"

# 同梱 VERSION (agmsg 1.0.0 以降が持つ)。あれば表示する。
if [ -f "${SKILL_DIR}/VERSION" ]; then
  ok "version: $(cat "${SKILL_DIR}/VERSION")"
fi

# Claude Code slash command
if [ -f "${HOME}/.claude/commands/${CMD}.md" ]; then
  ok "Claude command: ~/.claude/commands/${CMD}.md (/${CMD})"
else
  ng "Claude command 未配置: ~/.claude/commands/${CMD}.md"
fi

# Copilot CLI skill (~/.copilot がある環境のみ)
if [ -d "${HOME}/.copilot" ]; then
  if [ -f "${HOME}/.copilot/skills/${CMD}/SKILL.md" ]; then
    ok "Copilot skill: ~/.copilot/skills/${CMD}/SKILL.md"
  else
    ng "Copilot skill 未配置: ~/.copilot/skills/${CMD}/SKILL.md"
  fi
fi

# Codex sandbox の writable_roots に skill db が登録されているか
CODEX_CONFIG="${HOME}/.codex/config.toml"
if [ -f "$CODEX_CONFIG" ]; then
  if rg -q "${SKILL_DIR}/db" "$CODEX_CONFIG" 2>/dev/null; then
    ok "Codex writable_roots: 登録済み (~/.codex/config.toml)"
  else
    ng "Codex writable_roots: 未登録 → mise run install-agmsg で追記される"
  fi
else
  printf "  %s %s\n" "$(dim "·")" "$(dim "Codex 未検出 (~/.codex/config.toml なし) — スキップ")"
fi

printf "\n%s\n" "   起動: Claude では /${CMD}, Codex/Gemini では \$${CMD}"
