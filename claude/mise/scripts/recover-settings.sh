#!/bin/bash

#MISE description="~/.claude/settings.json が上書きされていたら、変更をリポジトリに安全に反映し symlink を復元する"
#MISE depends=["check_env"]
#MISE shell="bash -c"
#MISE quiet=true

set -eu

if [ "${MISE_CONFIG_ROOT:-}" = "" ]; then
  MISE_CONFIG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

# ---------------------------------------------------------------------------
# プロファイル解決
# ---------------------------------------------------------------------------
local_toml="${MISE_CONFIG_ROOT}/mise.local.toml"

if $IS_WSL; then
  auto_detect_profile="${WSL_CLAUDE_PROFILE:-}"
  if [ -z "${auto_detect_profile}" ]; then
    auto_detect_profile=$(grep '^WSL_CLAUDE_PROFILE' "${local_toml}" | cut -d'"' -f2)
  fi
else
  auto_detect_profile="${DEFAULT_CLAUDE_PROFILE:-}"
  if [ -z "${auto_detect_profile}" ]; then
    auto_detect_profile=$(grep '^DEFAULT_CLAUDE_PROFILE' "${local_toml}" | cut -d'"' -f2)
  fi
fi

option_profile=""
while [ $# -gt 0 ]; do
  case "$1" in
  --prof)
    option_profile="$2"
    shift 2
    ;;
  *)
    shift
    ;;
  esac
done

PROFILE=$([ -n "$option_profile" ] && echo "$option_profile" || echo "$auto_detect_profile")

if [ -z "$PROFILE" ]; then
  printf "🚨 プロファイルが指定されていません。\n" >&2
  exit 1
fi

PROFILE_PATH="${MISE_CONFIG_ROOT}/${PROFILES_DIR:-profiles}/$PROFILE"
TARGET="${HOME}/.claude/settings.json"
REPO_SETTINGS="${PROFILE_PATH}/settings.json"
REPO_LOCAL="${PROFILE_PATH}/settings.local.json"

# ---------------------------------------------------------------------------
# symlink チェック
# ---------------------------------------------------------------------------
if [ -L "$TARGET" ]; then
  printf "✅ %s は symlink です。同期不要。\n" "$TARGET"
  exit 0
fi

if [ ! -f "$TARGET" ]; then
  printf "⚠️  %s が存在しません。mise run link で作成してください。\n" "$TARGET" >&2
  exit 1
fi

printf "🔍 %s が実ファイルに置き換わっています。同期を開始します。\n\n" "$TARGET"

# ---------------------------------------------------------------------------
# マシン固有キーの定義
# settings.local.json に分離すべきトップレベルキー
# ---------------------------------------------------------------------------
LOCAL_KEYS='["awsAuthRefresh", "otelHeadersHelper"]'

# env 内でマシン固有のキー（ローカルパスや認証情報を含むもの）
LOCAL_ENV_KEYS='["CREDENTIAL_PROCESS_PATH", "AWS_PROFILE", "AWS_REGION", "SLACK_WEBHOOK_URL", "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_PROTOCOL", "OTEL_LOGS_EXPORTER", "OTEL_METRICS_EXPORTER", "OTEL_RESOURCE_ATTRIBUTES"]'

# hooks はポータブル扱い（Webhook URL は環境変数に分離済み）

# ---------------------------------------------------------------------------
# jq で分離
# ---------------------------------------------------------------------------
OVERWRITTEN=$(cat "$TARGET")

# settings.local.json 用: マシン固有キーを抽出
LOCAL_JSON=$(echo "$OVERWRITTEN" | jq \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson local_env_keys "$LOCAL_ENV_KEYS" \
  '
  # トップレベルのマシン固有キーを抽出
  (to_entries | map(select(.key as $k | $local_keys | index($k))) | from_entries) as $top_local |
  # env 内のマシン固有キーを抽出
  (if has("env") then
    {env: (.env | to_entries | map(select(.key as $k | $local_env_keys | index($k))) | from_entries)}
  else {} end) as $env_local |
  # マージ
  $top_local + $env_local
  ')

# settings.json 用: マシン固有キーを除外したポータブル設定
PORTABLE_JSON=$(echo "$OVERWRITTEN" | jq \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson local_env_keys "$LOCAL_ENV_KEYS" \
  '
  # トップレベルのマシン固有キーを除外
  to_entries | map(select(.key as $k | $local_keys | index($k) | not)) | from_entries |
  # env 内のマシン固有キーを除外
  if has("env") then
    .env |= (to_entries | map(select(.key as $k | $local_env_keys | index($k) | not)) | from_entries)
  else . end
  ')

# ---------------------------------------------------------------------------
# diff 表示
# ---------------------------------------------------------------------------
printf "📋 settings.json (git管理) の変更:\n"
printf "\033[2m────────────────────────────────────────\033[0m\n"
if [ -f "$REPO_SETTINGS" ]; then
  diff_result=$(diff --color=always <(jq --sort-keys . "$REPO_SETTINGS") <(echo "$PORTABLE_JSON" | jq --sort-keys .) || true)
  if [ -z "$diff_result" ]; then
    printf "   (変更なし)\n"
  else
    echo "$diff_result"
  fi
else
  printf "   (新規作成)\n"
  echo "$PORTABLE_JSON" | jq --sort-keys .
fi
printf "\033[2m────────────────────────────────────────\033[0m\n\n"

printf "📋 settings.local.json (gitignore) の変更:\n"
printf "\033[2m────────────────────────────────────────\033[0m\n"
if [ -f "$REPO_LOCAL" ] && [ -s "$REPO_LOCAL" ]; then
  diff_result=$(diff --color=always <(jq --sort-keys . "$REPO_LOCAL") <(echo "$LOCAL_JSON" | jq --sort-keys .) || true)
  if [ -z "$diff_result" ]; then
    printf "   (変更なし)\n"
  else
    echo "$diff_result"
  fi
else
  printf "   (新規作成 or 空ファイルから更新)\n"
  echo "$LOCAL_JSON" | jq --sort-keys .
fi
printf "\033[2m────────────────────────────────────────\033[0m\n\n"

# ---------------------------------------------------------------------------
# ユーザー確認
# ---------------------------------------------------------------------------
if [ -t 0 ]; then
  printf "この内容でリポジトリを更新し、symlink を復元しますか？ [Y/n] "
  read -r answer
  case "$answer" in
  [nN]*)
    printf "中断しました。上書きされたファイルは %s にそのまま残っています。\n" "$TARGET"
    exit 0
    ;;
  esac
else
  printf "⚡ 非対話モード: 自動的に反映します。\n"
fi

# ---------------------------------------------------------------------------
# バックアップ & 書き込み
# ---------------------------------------------------------------------------
backup="${TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$TARGET" "$backup"
printf "💾 バックアップ: %s\n" "$backup"

# ポータブル設定をリポジトリに書き込み
echo "$PORTABLE_JSON" | jq --sort-keys . >"$REPO_SETTINGS"
printf "📝 更新: %s\n" "$REPO_SETTINGS"

# ローカル設定をリポジトリに書き込み
echo "$LOCAL_JSON" | jq --sort-keys . >"$REPO_LOCAL"
printf "📝 更新: %s\n" "$REPO_LOCAL"

# ---------------------------------------------------------------------------
# symlink 復元
# ---------------------------------------------------------------------------
rm "$TARGET"
ln -sfn "$REPO_SETTINGS" "$TARGET"
printf "🔗 symlink 復元: %s -> %s\n" "$TARGET" "$REPO_SETTINGS"

# settings.local.json も symlink 確認・復元
LOCAL_TARGET="${HOME}/.claude/settings.local.json"
if [ ! -L "$LOCAL_TARGET" ]; then
  if [ -f "$LOCAL_TARGET" ]; then
    local_backup="${LOCAL_TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$LOCAL_TARGET" "$local_backup"
    printf "💾 バックアップ: %s\n" "$local_backup"
    rm "$LOCAL_TARGET"
  fi
  ln -sfn "$REPO_LOCAL" "$LOCAL_TARGET"
  printf "🔗 symlink 復元: %s -> %s\n" "$LOCAL_TARGET" "$REPO_LOCAL"
fi

printf "\n✅ 同期完了！\n"
printf "💡 git diff で変更内容を確認し、必要に応じて commit してください。\n"
