#!/bin/bash

#MISE description="指定プロファイルの apm dependencies を最新 ref に再解決 + user scope に再 deploy (lock 更新)"
#MISE depends=["apm-available", "uv-available", "check"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

# ---------------------------------------------------------------------------
# 設計: `apm update` には `-g` フラグが無く、project-local モードでしか動かない。
# profile dir で走らせると harness 検出が走り、profile dir に
# `.claude/` `.codex/` `.gemini/` `.github/` 等の deploy artifact が生成される
# (= dotfiles 汚染)。
#
# 解決: `apm install -g --refresh` を使う。
#   --refresh : 永続キャッシュを無視して upstream を再 fetch
#               (== apm update 相当の「最新 ref を取りに行く」効果)
#   -g        : ~/.apm/apm.yml ベースの user-scope 動作 (profile dir を汚染しない)
#
# 流れ:
#   1. profile/apm.yml を ~/.apm/apm.yml にシンク
#   2. ~/.apm/apm.lock.yaml を削除 (--refresh 時に新 lock を生成させるため)
#   3. apm install -g --refresh --legacy-skill-paths
#   4. 新規生成 lock を profile/ にコピーバック (commit 対象)
# ---------------------------------------------------------------------------

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PROFILE="${usage_prof:-${DEFAULT_AGENTS_PROFILE:-}}"
PROFILE_PATH="${ROOT_DIR}/$PROFILES_DIR/$PROFILE"
PRIVATE_PATH="${ROOT_DIR}/$PROFILES_DIR/private"
APM_HOME="${HOME}/.apm"

PRIVATE_YML="$PRIVATE_PATH/apm.yml"
PRIVATE_LOCK="$PRIVATE_PATH/apm.lock.yaml"
HAS_PRIVATE=false
if [ -f "$PRIVATE_YML" ]; then
  HAS_PRIVATE=true
fi

printf "%s\n" "🦄 Refreshing APM packages from profile: $PROFILE"
printf "   profile path: \033[36m%s\033[0m\n" "$PROFILE_PATH"
printf "   apm home    : \033[36m%s\033[0m\n" "$APM_HOME"
if [ "$HAS_PRIVATE" = "true" ]; then
  printf "   private overlay: \033[36m%s\033[0m\n" "$PRIVATE_YML"
fi

mkdir -p "$APM_HOME"

# Step 1: profile/apm.yml [+ private/apm.yml] -> ~/.apm/apm.yml シンク
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

# Step 2: 既存 lock を削除 (--refresh で新 lock を生成させる)
TARGET_LOCK="$APM_HOME/apm.lock.yaml"
if [ -f "$TARGET_LOCK" ]; then
  rm -f "$TARGET_LOCK"
  printf "%s\n" "   🗑️  既存 ~/.apm/apm.lock.yaml を削除 (新 lock を生成)"
fi

# Step 3: apm install -g --refresh --force で最新 ref を再解決 + 既存ファイルも上書き deploy
#
# --force の意義: lock を消して --refresh すると APM の「所有権記録」がリセットされ、
# 既存ファイル (前回 deploy したもの) を「自分が書いたものでない」と判断して上書き拒否
# する (12 PS × 3 location = 36 files skipped が発生)。update は明示的 refresh なので
# 上書きが正しい挙動。--force で「locally-authored files on collision」を上書き許可。
#
# 注意: --force は同時に「deploy despite critical security findings」も意味する。
# 自前 catalog (Caromaf/agent-package-basic) なので security findings は self-induced と
# 判断して許容。サードパーティ catalog を入れる際は要検討。
# default flag 採用 (install.sh と同じ理由、§3 物理制約表参照)
printf "%s\n" "   📦 Running: apm install -g --refresh --force"
apm install -g --refresh --force

# Step 4: 新規生成 lock を profile/ にコピーバック
#   private overlay 有効時は profiles/private/apm.lock.yaml (gitignored) に書く。
if [ "$HAS_PRIVATE" = "true" ]; then
  SOURCE_LOCK="$PRIVATE_LOCK"
else
  SOURCE_LOCK="$PROFILE_PATH/apm.lock.yaml"
fi
if [ -f "$TARGET_LOCK" ]; then
  mkdir -p "$(dirname "$SOURCE_LOCK")"
  cp "$TARGET_LOCK" "$SOURCE_LOCK"
  printf "%s\n" "   ✅ Refreshed lock copied back to: $SOURCE_LOCK"
  if [ "$HAS_PRIVATE" = "true" ]; then
    printf "%s\n" "      (gitignored — 同 PC 内で --frozen install 用に保持されます)"
  else
    printf "%s\n" "      (git diff で確認のうえ commit してください)"
  fi
fi

printf "%s\n" "✅ Refreshed APM dependencies for profile '$PROFILE' (lock + user-scope deploy 完了)"
