#!/bin/bash

#MISE description="指定プロファイルの apm dependencies を最新 ref に再解決 + user scope に再 deploy (lock 更新)"
#MISE depends=["apm-available", "uv-available", "check"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"
#USAGE flag "-v --verbose" help="詳細なログを表示する"

# ---------------------------------------------------------------------------
# 設計:
# profile の apm.yml を user scope (~/.apm/) に同期したうえで、
# `apm update -g` により dependency graph を最新 ref に再解決する。
#
# `apm update -g` は ~/.apm/apm.yml / apm.lock.yaml を対象にするため、
# profile dir に .claude/ .codex/ 等の deploy artifact を生成しない。
#
#
# 流れ:
#   1. profile/apm.yml [+ private overlay] -> ~/.apm/apm.yml
#   2. 既存 ~/.apm/apm.lock.yaml をバックアップして保持 (stale deployed file の回収情報を維持)
#   3. apm update -g -y --force を2回実行
#   4. 更新された lock を profile/ にコピーバック
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

# Step 2: 既存 lock をバックアップ (削除はしない)
#
# 過去は --refresh 前に lock を削除していたが、これは stale file 回収を破壊する副作用が
# あることが判明した (実測: agent-package-custom の spark-status で追加・削除の両方を
# 検証。lock を保持したまま --refresh --force を実行しても正しく反映され、
# skip メッセージも出なかった)。
#
# apm.lock.yaml の deployed_files には 2 種類ある。
#   - skill (ディレクトリ単位、hash 無し): 毎回ディレクトリ全体を丸ごと置き換えるので
#     lock の有無に関係なく動く。
#   - flat file (commands/rules/agents、個別ファイルの deployed_file_hashes 有り):
#     「前回このファイルを自分が書いたか」を前回 lock との比較で判定するため、
#     前回 lock が無いと stale ファイルの自動回収が機能しない。
#
# lock を消さずに保持することで、パッケージの配備先が変わる移行 (例: prompt primitive の
# 廃止で commands/*.md が消える場合) でも、次回 update で自動的に stale ファイルが
# 回収されるようになる。
TARGET_LOCK="$APM_HOME/apm.lock.yaml"
if [ -f "$TARGET_LOCK" ]; then
  lock_backup="${TARGET_LOCK}.backup.$(date +%Y%m%d_%H%M%S)"
  cp "$TARGET_LOCK" "$lock_backup"
  printf "%s\n" "   💾 既存 ~/.apm/apm.lock.yaml をバックアップ: $lock_backup"
fi

# Step 3: apm install -g --refresh --force で最新 ref を再解決 + 既存ファイルも上書き deploy
#
# NOTE:
# 現行 APM では、mutable ref の親 package が更新された際、1回目で親の SHA が更新され、
# 2回目で新しい親 manifest に追加された transitive dependency が検出されるケースがある。
#
# OpenAPM 仕様上は1回で transitive deps まで再解決されるべきなので、これは APM resolver の収束問題に対する workaround。
UPDATE_ARGS=(-g -y --force)

if [ "${usage_verbose:-false}" = "true" ]; then
  UPDATE_ARGS+=(--verbose)
fi

printf "%s\n" "   📦 Updating APM dependencies (pass 1/2)..."
apm update "${UPDATE_ARGS[@]}"

printf "%s\n" "   📦 Updating APM dependencies (pass 2/2)..."
apm update "${UPDATE_ARGS[@]}"

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
