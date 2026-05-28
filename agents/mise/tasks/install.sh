#!/bin/bash

#MISE description="指定プロファイルの apm.yml を ~/.apm/apm.yml にシンクし、APM packages を user scope (~/.claude/skills, ~/.codex/skills 等) に install する"
#MISE depends=["apm-available", "uv-available", "check"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

# ---------------------------------------------------------------------------
# 設計: profile/apm.yml は intent (dotfiles 管理)、~/.apm/apm.yml は live manifest。
# install.sh の責務:
#   1. profile/apm.yml + profile/apm.lock.yaml を ~/.apm/ にシンク
#   2. apm install -g [--frozen] (-g は ~/.apm を直接見る)
#   3. 初回 install で新規生成された lock を profile/ にコピーバック (commit 対象)
#
# 検証済の事実 (apm 0.13):
#   - `apm install -g` (引数無し) は cwd ではなく ~/.apm/apm.yml を読む
#   - ~/.apm/apm.yml が無いと "Run 'apm install -g <org/repo>' to auto-create + install"
#     と表示され非ゼロ終了
# ---------------------------------------------------------------------------

set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PROFILE="${usage_prof:-${DEFAULT_AGENTS_PROFILE:-}}"
PROFILE_PATH="${ROOT_DIR}/$PROFILES_DIR/$PROFILE"
PRIVATE_PATH="${ROOT_DIR}/$PROFILES_DIR/private"
APM_HOME="${HOME}/.apm"

# private overlay: profiles/private/ は .gitignore 配下の任意 dir。
# apm.yml があれば dependencies.{apm,mcp} を active profile に重ねて install する。
PRIVATE_YML="$PRIVATE_PATH/apm.yml"
PRIVATE_LOCK="$PRIVATE_PATH/apm.lock.yaml"
HAS_PRIVATE=false
if [ -f "$PRIVATE_YML" ]; then
  HAS_PRIVATE=true
fi

printf "%s\n" "🦄 Installing APM packages from profile: $PROFILE"
printf "   profile path: \033[36m%s\033[0m\n" "$PROFILE_PATH"
printf "   apm home    : \033[36m%s\033[0m\n" "$APM_HOME"
if [ "$HAS_PRIVATE" = "true" ]; then
  printf "   private overlay: \033[36m%s\033[0m\n" "$PRIVATE_YML"
fi

mkdir -p "$APM_HOME"

# ---------------------------------------------------------------------------
# Step 1: profile/apm.yml [+ private/apm.yml] -> ~/.apm/apm.yml シンク
# ---------------------------------------------------------------------------
TARGET_YML="$APM_HOME/apm.yml"
SOURCE_YML="$PROFILE_PATH/apm.yml"
TMP_YML=$(mktemp -t apm-merged.XXXXXX.yml)
trap 'rm -f "$TMP_YML"' EXIT

if [ "$HAS_PRIVATE" = "true" ]; then
  uv run "${ROOT_DIR}/mise/scripts/merge_apm_yml.py" \
    --base "$SOURCE_YML" --overlay "$PRIVATE_YML" >"$TMP_YML"
else
  cp "$SOURCE_YML" "$TMP_YML"
fi

if [ -f "$TARGET_YML" ] && ! diff -q "$TMP_YML" "$TARGET_YML" >/dev/null 2>&1; then
  backup="${TARGET_YML}.backup.$(date +%Y%m%d_%H%M%S)"
  cp "$TARGET_YML" "$backup"
  printf "%s\n" "   💾 既存 ~/.apm/apm.yml をバックアップ: $backup"
fi
mv "$TMP_YML" "$TARGET_YML"
trap - EXIT
if [ "$HAS_PRIVATE" = "true" ]; then
  printf "%s\n" "   📝 Synced profile + private overlay -> $TARGET_YML"
else
  printf "%s\n" "   📝 Synced profile apm.yml -> $TARGET_YML"
fi

# ---------------------------------------------------------------------------
# Step 2: lock シンク
#   - private overlay 有効時: profiles/private/apm.lock.yaml が正 (gitignored)
#   - 無効時                 : profile/apm.lock.yaml が正 (git-tracked)
# ---------------------------------------------------------------------------
TARGET_LOCK="$APM_HOME/apm.lock.yaml"
if [ "$HAS_PRIVATE" = "true" ]; then
  SOURCE_LOCK="$PRIVATE_LOCK"
else
  SOURCE_LOCK="$PROFILE_PATH/apm.lock.yaml"
fi

if [ -f "$SOURCE_LOCK" ]; then
  if [ -f "$TARGET_LOCK" ] && ! diff -q "$SOURCE_LOCK" "$TARGET_LOCK" >/dev/null 2>&1; then
    backup="${TARGET_LOCK}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$TARGET_LOCK" "$backup"
    printf "%s\n" "   💾 既存 ~/.apm/apm.lock.yaml をバックアップ: $backup"
  fi
  cp "$SOURCE_LOCK" "$TARGET_LOCK"
  printf "%s\n" "   🔒 Synced lock -> $TARGET_LOCK"
fi

# ---------------------------------------------------------------------------
# Step 3: apm install -g 実行 (-g は ~/.apm を直接見るので cd 不要)
# ---------------------------------------------------------------------------
# --legacy-skill-paths: skill を `~/.codex/skills/`, `~/.gemini/skills/` 等の per-tool
# パスにも配備する。デフォルト (`.agents/skills/` 共有のみ) では Codex/Gemini CLI が
# 読みに行かないため、現状 Claude 以外で skill が機能しない。CLI 側が cross-tool
# 仕様に追いつくまでの互換策。
# default flag 採用 (2026-05-28 検証で Codex/Gemini が cross-tool を読むと確認):
# - Claude: default で per-tool (~/.claude/skills/) に自動配備される (Claude 特別扱い)
# - Codex/Gemini: cross-tool (~/.agents/skills/) を読む → cross-tool 配備のみで OK
# - Cursor/Copilot: cross-tool 読み挙動は未検証だが、現状 skill 機能要求なしと判断
if [ -f "$TARGET_LOCK" ]; then
  printf "%s\n" "   📦 Running: apm install -g --frozen"
  apm install -g --frozen
else
  printf "%s\n" "   📦 Running: apm install -g (no lock yet)"
  apm install -g
fi

# ---------------------------------------------------------------------------
# Step 4: ~/.apm/apm.lock.yaml が新規生成 / 更新された場合は profile 側へコピーバック
#   - private overlay 有効時: profiles/private/apm.lock.yaml に書く (gitignored)。
#     公開 profile の lock を private ref で汚染しないため。
#   - 無効時                 : profile/apm.lock.yaml に書く (git-tracked)。commit 推奨。
# ---------------------------------------------------------------------------
if [ -f "$TARGET_LOCK" ]; then
  mkdir -p "$(dirname "$SOURCE_LOCK")"
  if [ ! -f "$SOURCE_LOCK" ]; then
    cp "$TARGET_LOCK" "$SOURCE_LOCK"
    printf "%s\n" "   ✅ Generated lock copied back to: $SOURCE_LOCK"
    if [ "$HAS_PRIVATE" = "true" ]; then
      printf "%s\n" "      (gitignored — 同 PC 内で --frozen install 用に保持されます)"
    else
      printf "%s\n" "      (git add してコミットすると他 PC で --frozen install できます)"
    fi
  elif ! diff -q "$SOURCE_LOCK" "$TARGET_LOCK" >/dev/null 2>&1; then
    cp "$TARGET_LOCK" "$SOURCE_LOCK"
    printf "%s\n" "   ✅ Updated lock copied back to: $SOURCE_LOCK"
    if [ "$HAS_PRIVATE" = "true" ]; then
      printf "%s\n" "      (gitignored — 同 PC 内で --frozen install 用に保持されます)"
    else
      printf "%s\n" "      (再現性のため diff を確認のうえコミットしてください)"
    fi
  fi
fi

printf "%s\n" "✅ Installed APM packages from profile '$PROFILE' to user scope"
