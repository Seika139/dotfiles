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
#   - 既存 settings.local.json に既に存在するキー (= provenance。下記参照)
# それ以外は PORTABLE (settings.json、git 管理)
#
#   local    = LOCAL_KEYS ∪ LOCAL_ENV_KEYS ∪ 非 portable な marketplace ∪ provenance
#   portable = SOURCE (~/.claude/settings.json) から local を引いたもの
#
# provenance (由来ベースの分類):
#   キー名ホワイトリストだけでは、マージ済みの ~/.claude/settings.json (SOURCE) から
#   どちらのファイル由来かを判別できないキー (例: hooks) を分類できない。
#   そこで「既存 settings.local.json に既にあるキーは local に留める」を 4 番目の
#   判定ソースとして使う。トップレベルキー K について:
#     - existing_local[K] と SOURCE[K] が両方オブジェクトなら
#       -> SOURCE[K] にも存在するサブキーだけを local に振り分ける
#        (hooks のイベント名単位、env の変数名単位の分類になる)
#     - それ以外 (配列・スカラー・型が食い違う)
#       -> K を丸ごと local に振り分ける
#   provenance は「行き先」を決めるだけで「存在」を作らない: SOURCE に無いキーは
#   existing_local にあっても復活させない (~/.claude/ から削除された hook 等)。
#   LOCAL_KEYS / marketplace 系のキーは専用ロジックが既にあるため provenance の対象外。
LOCAL_KEYS='["awsAuthRefresh", "otelHeadersHelper"]'
LOCAL_ENV_KEYS='["AWS_PROFILE", "AWS_REGION", "CREDENTIAL_PROCESS_PATH", "OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_RESOURCE_ATTRIBUTES", "SLACK_WEBHOOK_URL"]'

# extraKnownMarketplaces / enabledPlugins は marketplace 単位のホワイトリストで分類:
#   - PORTABLE_MARKETPLACES に含まれる marketplace (= 公開 OK) -> settings.json
#   - それ以外 (= 社内 marketplace 等)                          -> settings.local.json
# enabledPlugins のキー "<plugin>@<marketplace>" は @ の右側で判定する。
PORTABLE_MARKETPLACES='["claude-plugins-official", "openai-codex"]'

# provenance の入力: 既存 settings.local.json (無い/空なら {} として扱う)
if [ -f "$REPO_LOCAL" ] && [ -s "$REPO_LOCAL" ]; then
  EXISTING_LOCAL_JSON=$(cat "$REPO_LOCAL")
else
  EXISTING_LOCAL_JSON='{}'
fi

# ---------------------------------------------------------------------------
# jq で分離
# ---------------------------------------------------------------------------
SOURCE=$(cat "$TARGET")

# 両フィルタで共通の provenance 判定ロジック (existing_local の各キーを SOURCE と比較)。
# 出力: [{key, mode: "whole"}] または [{key, mode: "partial", subkeys: [...]}] の配列。
# exclude_keys (LOCAL_KEYS / marketplace 系) は専用ロジックがあるため対象外にする。
# SOURCE に存在しないキーは対象外 (= provenance で存在を復活させない)。
# shellcheck disable=SC2016 # jq の $var 記法であり shell 展開ではない
JQ_PROVENANCE_DEF='
def provenance_decisions($source; $existing_local; $exclude_keys):
  [ $existing_local | keys[] as $k |
    select($exclude_keys | index($k) | not) |
    select($source | has($k)) |
    ($existing_local[$k]) as $el |
    ($source[$k]) as $sv |
    if ($el | type) == "object" and ($sv | type) == "object" then
      ($el | keys) as $elkeys |
      ($sv | keys) as $svkeys |
      ($elkeys | map(select(. as $ek | $svkeys | index($ek)))) as $shared |
      if ($shared | length) > 0 then {key: $k, mode: "partial", subkeys: $shared} else empty end
    else
      {key: $k, mode: "whole"}
    end
  ];
'

LOCAL_JSON=$(echo "$SOURCE" | jq \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson local_env_keys "$LOCAL_ENV_KEYS" \
  --argjson portable_marketplaces "$PORTABLE_MARKETPLACES" \
  --argjson existing_local "$EXISTING_LOCAL_JSON" \
  "
  ${JQ_PROVENANCE_DEF}
  . as \$source |
  # トップレベルで丸ごと LOCAL 行きのキー (extraKnownMarketplaces / enabledPlugins は除外して別処理)
  (to_entries | map(select(
    (.key as \$k | \$local_keys | index(\$k))
    and (.key | IN(\"extraKnownMarketplaces\", \"enabledPlugins\") | not)
  )) | from_entries) as \$top_local |
  # extraKnownMarketplaces のうち PORTABLE_MARKETPLACES に含まれない marketplace
  (if has(\"extraKnownMarketplaces\") then
    (.extraKnownMarketplaces | to_entries
      | map(select(.key as \$m | \$portable_marketplaces | index(\$m) | not))
      | from_entries) as \$local_mks |
    if (\$local_mks | length) > 0 then {extraKnownMarketplaces: \$local_mks} else {} end
  else {} end) as \$mks_local |
  # enabledPlugins のうち @<marketplace> が PORTABLE_MARKETPLACES に含まれないキー
  (if has(\"enabledPlugins\") then
    (.enabledPlugins | to_entries
      | map(select(.key | split(\"@\") | last as \$m | \$portable_marketplaces | index(\$m) | not))
      | from_entries) as \$local_plugins |
    if (\$local_plugins | length) > 0 then {enabledPlugins: \$local_plugins} else {} end
  else {} end) as \$plugins_local |
  # provenance: 既存 settings.local.json に既にあるキーは local に留める
  (provenance_decisions(\$source; \$existing_local; (\$local_keys + [\"extraKnownMarketplaces\", \"enabledPlugins\"]))) as \$decisions |
  # env は LOCAL_ENV_KEYS ホワイトリストと provenance の union で判定
  ((\$decisions | map(select(.key == \"env\")))[0].subkeys // []) as \$env_provenance_keys |
  (if has(\"env\") then
    (\$local_env_keys + \$env_provenance_keys | unique) as \$env_local_keys_all |
    {env: (.env | to_entries | map(select(.key as \$k | \$env_local_keys_all | index(\$k))) | from_entries)}
  else {} end) as \$env_local |
  # env 以外の provenance キー (hooks のイベント名単位分類等)
  (reduce (\$decisions[] | select(.key != \"env\")) as \$d ({};
    if \$d.mode == \"whole\" then
      . + {(\$d.key): \$source[\$d.key]}
    else
      . + {(\$d.key): (\$source[\$d.key] | to_entries | map(select(.key as \$sk | \$d.subkeys | index(\$sk))) | from_entries)}
    end
  )) as \$provenance_local |
  \$top_local + \$env_local + \$mks_local + \$plugins_local + \$provenance_local
  ")

PORTABLE_JSON=$(echo "$SOURCE" | jq \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson local_env_keys "$LOCAL_ENV_KEYS" \
  --argjson portable_marketplaces "$PORTABLE_MARKETPLACES" \
  --argjson existing_local "$EXISTING_LOCAL_JSON" \
  "
  ${JQ_PROVENANCE_DEF}
  . as \$source |
  # トップレベルで丸ごと LOCAL 行きのキーを除外 (extraKnownMarketplaces / enabledPlugins は別処理で残す)
  (to_entries | map(select(
    (.key as \$k | \$local_keys | index(\$k) | not)
    or (.key | IN(\"extraKnownMarketplaces\", \"enabledPlugins\"))
  )) | from_entries) as \$without_top_local |
  (\$without_top_local
    | (if has(\"extraKnownMarketplaces\") then
        (.extraKnownMarketplaces | to_entries
          | map(select(.key as \$m | \$portable_marketplaces | index(\$m)))
          | from_entries) as \$portable_mks |
        if (\$portable_mks | length) > 0 then .extraKnownMarketplaces = \$portable_mks
        else del(.extraKnownMarketplaces) end
      else . end)
    | (if has(\"enabledPlugins\") then
        (.enabledPlugins | to_entries
          | map(select(.key | split(\"@\") | last as \$m | \$portable_marketplaces | index(\$m)))
          | from_entries) as \$portable_plugins |
        if (\$portable_plugins | length) > 0 then .enabledPlugins = \$portable_plugins
        else del(.enabledPlugins) end
      else . end)
  ) as \$after_marketplace |
  # provenance: 既存 settings.local.json に既にあるキー (のサブキー) を除外
  (provenance_decisions(\$source; \$existing_local; (\$local_keys + [\"extraKnownMarketplaces\", \"enabledPlugins\"]))) as \$decisions |
  ((\$decisions | map(select(.key == \"env\")))[0].subkeys // []) as \$env_provenance_keys |
  (\$after_marketplace
    | (if has(\"env\") then
        (\$local_env_keys + \$env_provenance_keys | unique) as \$env_local_keys_all |
        .env |= (to_entries | map(select(.key as \$k | \$env_local_keys_all | index(\$k) | not)) | from_entries)
      else . end)
  ) as \$after_env |
  reduce (\$decisions[] | select(.key != \"env\")) as \$d (\$after_env;
    if \$d.mode == \"whole\" then
      del(.[\$d.key])
    else
      (.[\$d.key] | to_entries | map(select(.key as \$sk | \$d.subkeys | index(\$sk) | not)) | from_entries) as \$remaining |
      if (\$remaining | length) > 0 then .[\$d.key] = \$remaining else del(.[\$d.key]) end
    end
  )
  ")

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
# 書き込み前の安全ガード (diff 表示の直後、確認プロンプトより前に置く)
# ---------------------------------------------------------------------------
# provenance は既存 settings.local.json を参照する自己参照的な仕組みのため、
# 参照先が無い/不足している状態 (git clone 直後は settings.local.json が
# gitignore されており必ず不在) では保護が消え、hooks 全体が portable 判定に
# 戻ってマシン固有の絶対パスが公開リポジトリにコミットされ得る。
# ここでは分類ルールを変えず、書き込み直前の最後の防波堤として 2 つのガードを置く。
# 確認プロンプトは非対話では無条件に適用されるため、TTY 判定より前で検証する。

# ガード A (abort): settings.json (公開予定) にこのマシンの実際のホームディレクトリ
# が含まれていたら中断する。パスの「形」(/Users/ や /home/ 等の汎用パターン) では
# 判定しない。移植可能な絶対パス (/usr/bin/... 等) を誤検知するため。
# JSON 文字列中のバックスラッシュは \\ にエスケープされているので、jq で文字列
# スカラーを unescape してから照合する。
GUARD_HOME_POSIX="$HOME"
if command -v cygpath &>/dev/null; then
  GUARD_HOME_WINDOWS="$(cygpath -w "$HOME" 2>/dev/null || true)"
else
  GUARD_HOME_WINDOWS=""
fi

PORTABLE_STRINGS=$(echo "$PORTABLE_JSON" | jq -r '[.. | strings] | .[]')

GUARD_A_HIT=""
if [ -n "$GUARD_HOME_POSIX" ] && printf '%s\n' "$PORTABLE_STRINGS" | grep -qF "$GUARD_HOME_POSIX"; then
  GUARD_A_HIT="$GUARD_HOME_POSIX"
elif [ -n "$GUARD_HOME_WINDOWS" ] && printf '%s\n' "$PORTABLE_STRINGS" | grep -qF "$GUARD_HOME_WINDOWS"; then
  GUARD_A_HIT="$GUARD_HOME_WINDOWS"
fi

if [ -n "$GUARD_A_HIT" ]; then
  printf "🚨 ガード A: settings.json (公開予定) にこのマシンのホームディレクトリ (%s) が含まれています。\n" "$GUARD_A_HIT" >&2
  printf "    settings.local.json が無い/不足している可能性があります (git clone 直後など)。\n" >&2
  printf "    settings.local.json を復元するか手動で分類してから再実行してください。書き込み・link は実行せず中断します。\n" >&2
  exit 1
fi

# ガード B (warn): provenance が local に振り分けたサブキーが、コミット済み
# settings.json の同名キーと衝突していないかを警告する (中断はしない)。
# link.sh の `jq -s '.[0] * .[1]'` は配列を右辺 (local) で丸ごと置換するため、
# 同じ hooks イベント名が settings.json と settings.local.json の両方にあると、
# link 時に git 管理側の内容が届かず、次の recover で警告もエラーもなく
# settings.json から消える (データロス)。
if [ -f "$REPO_SETTINGS" ]; then
  REPO_SETTINGS_JSON=$(cat "$REPO_SETTINGS")
else
  REPO_SETTINGS_JSON='{}'
fi

GUARD_B_WARNINGS=$(jq -rn \
  --argjson source "$SOURCE" \
  --argjson existing_local "$EXISTING_LOCAL_JSON" \
  --argjson local_keys "$LOCAL_KEYS" \
  --argjson repo_settings "$REPO_SETTINGS_JSON" \
  "
  ${JQ_PROVENANCE_DEF}
  (provenance_decisions(\$source; \$existing_local; (\$local_keys + [\"extraKnownMarketplaces\", \"enabledPlugins\"]))
    | map(select(.mode == \"partial\"))) as \$partials |
  [ \$partials[] |
    .key as \$k |
    (\$repo_settings[\$k] // {} | if type == \"object\" then keys else [] end) as \$repo_subkeys |
    (.subkeys | map(select(. as \$sk | \$repo_subkeys | index(\$sk)))) as \$collide |
    select((\$collide | length) > 0) |
    \"⚠️  ガード B: \" + \$k + \" の \" + (\$collide | join(\", \")) + \" が settings.json (git管理) と settings.local.json の両方に存在します。link 実行時に settings.json 側のコミット済み内容が失われます。\"
  ] | .[]
  ")

if [ -n "$GUARD_B_WARNINGS" ]; then
  printf '%s\n' "$GUARD_B_WARNINGS" >&2
fi

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
