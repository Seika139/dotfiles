#!/bin/bash

#MISE description="~/.claude/settings.json (実ファイル) を split して dotfiles に取り込み、~/.claude/settings.json を再生成する"
#MISE depends=["check_env"]
#MISE shell="bash -c"
#MISE quiet=true

# ---------------------------------------------------------------------------
# CCWB (Claude Code with Bedrock 認証ヘルパー) が ~/.claude/settings.json を
# 物理書き換えするため、dotfiles との同期は双方向同期モデルで行う。
# 詳細は claude/docs/settings-sync.md を参照。
#
#   recover (このスクリプト): ~/.claude/settings.json -> dotfiles の 2 ファイルに split
#   link (link.sh):           dotfiles の 2 ファイル  -> ~/.claude/settings.json に merge
# ---------------------------------------------------------------------------

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
# 前提チェック
# ---------------------------------------------------------------------------
if [ ! -e "$TARGET" ]; then
  printf "⚠️  %s が存在しません。先に CCWB の初期化または mise run link を実行してください。\n" "$TARGET" >&2
  exit 1
fi

if [ -L "$TARGET" ]; then
  printf "⚠️  %s が symlink です。新方針では実ファイル運用が前提です。\n" "$TARGET" >&2
  printf "    旧 symlink を削除して mise run link を実行してください。\n" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 分類ルール (claude/docs/settings-sync.md を参照)
# ---------------------------------------------------------------------------
# LOCAL = 公開リポジトリにコミットしたくない値:
#   - 非公開情報 / Webhook シークレット
#   - マシン固有の絶対パス
# それ以外は PORTABLE (settings.json、git 管理)
LOCAL_KEYS='["awsAuthRefresh", "otelHeadersHelper"]'
LOCAL_ENV_KEYS='["AWS_PROFILE", "AWS_REGION", "CREDENTIAL_PROCESS_PATH", "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_RESOURCE_ATTRIBUTES", "SLACK_WEBHOOK_URL"]'

# extraKnownMarketplaces / enabledPlugins は marketplace 単位のホワイトリストで分類:
#   - PORTABLE_MARKETPLACES に含まれる marketplace (= 公開 OK) -> settings.json
#   - それ以外 (= 社内 marketplace 等)                          -> settings.local.json
# enabledPlugins のキー "<plugin>@<marketplace>" は @ の右側で判定する。
PORTABLE_MARKETPLACES='["claude-plugins-official", "openai-codex"]'

# ---------------------------------------------------------------------------
# jq で分離
# ---------------------------------------------------------------------------
SOURCE=$(cat "$TARGET")

LOCAL_JSON=$(echo "$SOURCE" | jq \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson local_env_keys "$LOCAL_ENV_KEYS" \
  --argjson portable_marketplaces "$PORTABLE_MARKETPLACES" \
  '
  # トップレベルで丸ごと LOCAL 行きのキー (extraKnownMarketplaces / enabledPlugins は除外して別処理)
  (to_entries | map(select(
    (.key as $k | $local_keys | index($k))
    and (.key | IN("extraKnownMarketplaces", "enabledPlugins") | not)
  )) | from_entries) as $top_local |
  # env 内のローカルキー
  (if has("env") then
    {env: (.env | to_entries | map(select(.key as $k | $local_env_keys | index($k))) | from_entries)}
  else {} end) as $env_local |
  # extraKnownMarketplaces のうち PORTABLE_MARKETPLACES に含まれない marketplace
  (if has("extraKnownMarketplaces") then
    (.extraKnownMarketplaces | to_entries
      | map(select(.key as $m | $portable_marketplaces | index($m) | not))
      | from_entries) as $local_mks |
    if ($local_mks | length) > 0 then {extraKnownMarketplaces: $local_mks} else {} end
  else {} end) as $mks_local |
  # enabledPlugins のうち @<marketplace> が PORTABLE_MARKETPLACES に含まれないキー
  (if has("enabledPlugins") then
    (.enabledPlugins | to_entries
      | map(select(.key | split("@") | last as $m | $portable_marketplaces | index($m) | not))
      | from_entries) as $local_plugins |
    if ($local_plugins | length) > 0 then {enabledPlugins: $local_plugins} else {} end
  else {} end) as $plugins_local |
  $top_local + $env_local + $mks_local + $plugins_local
  ')

PORTABLE_JSON=$(echo "$SOURCE" | jq \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson local_env_keys "$LOCAL_ENV_KEYS" \
  --argjson portable_marketplaces "$PORTABLE_MARKETPLACES" \
  '
  # トップレベルで丸ごと LOCAL 行きのキーを除外 (extraKnownMarketplaces / enabledPlugins は別処理で残す)
  to_entries | map(select(
    (.key as $k | $local_keys | index($k) | not)
    or (.key | IN("extraKnownMarketplaces", "enabledPlugins"))
  )) | from_entries |
  # env 内のローカルキーを除外
  (if has("env") then
    .env |= (to_entries | map(select(.key as $k | $local_env_keys | index($k) | not)) | from_entries)
  else . end) |
  # extraKnownMarketplaces はホワイトリストにあるものだけ残す。残りなしなら削除
  (if has("extraKnownMarketplaces") then
    (.extraKnownMarketplaces | to_entries
      | map(select(.key as $m | $portable_marketplaces | index($m)))
      | from_entries) as $portable_mks |
    if ($portable_mks | length) > 0 then .extraKnownMarketplaces = $portable_mks
    else del(.extraKnownMarketplaces) end
  else . end) |
  # enabledPlugins も同様
  (if has("enabledPlugins") then
    (.enabledPlugins | to_entries
      | map(select(.key | split("@") | last as $m | $portable_marketplaces | index($m)))
      | from_entries) as $portable_plugins |
    if ($portable_plugins | length) > 0 then .enabledPlugins = $portable_plugins
    else del(.enabledPlugins) end
  else . end)
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
  printf "この内容で dotfiles を更新し、~/.claude/settings.json を再生成しますか？ [Y/n] "
  read -r answer
  case "$answer" in
  [nN]*)
    printf "中断しました。~/.claude/settings.json は変更していません。\n"
    exit 0
    ;;
  esac
else
  printf "⚡ 非対話モード: 自動的に反映します。\n"
fi

# ---------------------------------------------------------------------------
# バックアップ & dotfiles に書き込み
# ---------------------------------------------------------------------------
backup="${TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$TARGET" "$backup"
printf "💾 バックアップ: %s\n" "$backup"

echo "$PORTABLE_JSON" | jq --sort-keys . >"$REPO_SETTINGS"
printf "📝 更新: %s\n" "$REPO_SETTINGS"

echo "$LOCAL_JSON" | jq --sort-keys . >"$REPO_LOCAL"
printf "📝 更新: %s\n" "$REPO_LOCAL"

# ---------------------------------------------------------------------------
# ~/.claude/settings.json を再生成 (link を呼ぶ)
# ---------------------------------------------------------------------------
LINK_SCRIPT="${MISE_CONFIG_ROOT}/mise/scripts/link.sh"
if [ -x "$LINK_SCRIPT" ] || [ -f "$LINK_SCRIPT" ]; then
  printf "\n🔄 link を呼んで ~/.claude/settings.json を再生成します。\n"
  bash "$LINK_SCRIPT" --prof "$PROFILE"
else
  printf "⚠️  link.sh が見つかりません: %s\n" "$LINK_SCRIPT" >&2
  exit 1
fi

printf "\n✅ recover 完了！\n"
printf "💡 git diff で変更内容を確認し、必要に応じて commit してください。\n"
