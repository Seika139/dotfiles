#!/usr/bin/env bash
# repo-preset: 選択したコンポーネントを既存 git repo に導入するオーケストレーター
#
# lib.sh (純粋関数) と select.sh (コンポーネント選択) を組み合わせて、
# 「今いる（または --target 指定の）git repo」にコンポーネントを実際に導入する。
# 既存 git repo であることを前提とする（pre-commit/git-secrets が git 必須のため）。
#
# 使い方:
#   bash install.sh [--target <dir>] [--components a,b,c | --all]
#                    [--main-guard] [--dry-run] [--force] [--offline]
#                    [--no-install] [--github-user <name>]
#
#   # target を省略するとカレントディレクトリに導入する
#   bash install.sh --components markdown,shell
#
#   # 対話選択 (TTY + fzf があれば select.sh が fzf を起動する)
#   bash install.sh --target ./my-repo
#
# フラグ:
#   --target <dir>        導入先 (デフォルト: カレントディレクトリ)
#   --components <csv>     select.sh にそのまま渡す (非対話選択)
#   --all                  select.sh にそのまま渡す (全選択可能コンポーネント)
#   --main-guard           pre-commit の guard 版 (main への commit/push 禁止) を採用
#   --dry-run              書き込みを一切行わず、予定を出力する
#   --force                既存ファイルがあっても上書きする (デフォルトは skip)
#   --offline              ネットが必要な処理 (mise install / uv add / pnpm add 等) をスキップ
#   --no-install            ファイル生成のみ行い、mise install / post_scaffold の実行系をスキップ
#   --github-user <name>   プレースホルダ {{github_user}} に使う値
#   -h, --help             このヘルプを表示

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELECT_SH="${SCRIPT_DIR}/select.sh"

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib.sh"

# ---- log helpers ----
c_bold=$'\033[1m'
c_dim=$'\033[2m'
c_green=$'\033[32m'
c_yellow=$'\033[33m'
c_red=$'\033[31m'
c_reset=$'\033[0m'
log() { printf '%s==>%s %s\n' "${c_green}${c_bold}" "${c_reset}" "$*" >&2; }
warn() { printf '%s!! %s%s\n' "${c_yellow}" "$*" "${c_reset}" >&2; }
info() { printf '%s   %s%s\n' "${c_dim}" "$*" "${c_reset}" >&2; }
plan() { printf '%s  would: %s%s\n' "${c_dim}" "$*" "${c_reset}" >&2; }
die() {
  printf '%sERROR:%s %s\n' "${c_red}${c_bold}" "${c_reset}" "$*" >&2
  exit 1
}

usage() {
  sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

# ---- parse args ----
target="."
components_csv=""
use_all=0
main_guard=0
dry_run=0
force=0
offline=0
no_install=0
github_user_opt=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  -h | --help) usage 0 ;;
  --target)
    target="${2:?}"
    shift 2
    ;;
  --target=*)
    target="${1#--target=}"
    shift
    ;;
  --components)
    components_csv="${2:?}"
    shift 2
    ;;
  --components=*)
    components_csv="${1#--components=}"
    shift
    ;;
  --all)
    use_all=1
    shift
    ;;
  --main-guard)
    main_guard=1
    shift
    ;;
  --dry-run)
    dry_run=1
    shift
    ;;
  --force)
    force=1
    shift
    ;;
  --offline)
    offline=1
    shift
    ;;
  --no-install)
    no_install=1
    shift
    ;;
  --github-user)
    github_user_opt="${2:?}"
    shift 2
    ;;
  --github-user=*)
    github_user_opt="${1#--github-user=}"
    shift
    ;;
  *)
    die "unknown option: $1"
    ;;
  esac
done

# ---- resolve target (absolute path) ----
if [[ -d "$target" ]]; then
  target="$(cd "$target" && pwd)"
else
  # dry-run でも「対象確認」のため存在チェックはエラーにする
  die "target が存在しません: ${target}"
fi

# ---- git repo チェック (非 git はエラーで停止) ----
if ! git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  die "target は git repo ではありません: ${target} (pre-commit/git-secrets には git repo が必須です)"
fi

# ---- github_user 解決 ----
github_user="$github_user_opt"
if [[ -z "$github_user" ]]; then
  github_user="${GITHUB_USER:-}"
fi
if [[ -z "$github_user" ]]; then
  github_user="$(git -C "$target" config user.name 2>/dev/null || true)"
fi
if [[ -z "$github_user" ]]; then
  github_user="$(git config --global user.name 2>/dev/null || true)"
fi
[[ -n "$github_user" ]] || github_user="your-github-user"

# ---- コンポーネント選択 (select.sh をパススルー) ----
select_args=()
((use_all)) && select_args+=(--all)
[[ -n "$components_csv" ]] && select_args+=(--components "$components_csv")

sel=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  sel+=("$line")
done < <(bash "$SELECT_SH" "${select_args[@]}")

[[ ${#sel[@]} -gt 0 ]] || die "コンポーネントが選択されませんでした"

# ---- 推移閉包 ----
comps=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  comps+=("$line")
done < <(rp_resolve_closure "${sel[@]}")

[[ ${#comps[@]} -gt 0 ]] || die "コンポーネントの依存解決に失敗しました"

log "target       : ${target}"
log "components   : ${comps[*]}"

# ---- project_name / slug 導出 ----
project_name="$(basename "$target")"
project_slug="$(printf '%s' "$project_name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '_' | sed 's/_\{2,\}/_/g; s/^_//; s/_$//')"
[[ -n "$project_slug" ]] || project_slug="project"

has_component() {
  local needle="$1" c
  for c in "${comps[@]}"; do
    [[ "$c" == "$needle" ]] && return 0
  done
  return 1
}

# ---- post_scaffold 実行順の決定 ----
# rp_resolve_closure の出力は「_common 先頭 + BFS 発見順」であり、
# markdown/textlint/spell が依存する js (pnpm 基盤) が依存元より後に
# 発見されるケースがある (例: textlint -> [markdown, js] の BFS で
# markdown の post_scaffold より js の方が後に処理されてしまう)。
# js の post_scaffold (pnpm init) は他の pnpm add 系より先に実行する
# 必要があるため先頭に固定する。
# また pre-commit の post_scaffold (git secrets 初期化 / pre-commit
# install) は全ファイルのコピーが終わった後に実行したいため最後に固定する。
post_scaffold_order() {
  local c
  if has_component js; then
    printf '%s\n' "js"
  fi
  for c in "${comps[@]}"; do
    case "$c" in
    js | pre-commit) continue ;;
    esac
    printf '%s\n' "$c"
  done
  if has_component pre-commit; then
    printf '%s\n' "pre-commit"
  fi
}

# ---- dry-run: 予定のみ出力して終了 ----
if ((dry_run)); then
  log "[dry-run] コピー予定"
  for c in "${comps[@]}"; do
    printf '  %s%s:%s\n' "$c_bold" "$c" "$c_reset" >&2
    rp_copy_component "$c" "$target" --dry-run | sed 's/^/  /' >&2
  done

  log "[dry-run] mise.toml マージ予定"
  plan "mise.toml を生成 (tools 統合 + tasks 連結 + 統合 lint/fix)"

  log "[dry-run] .gitignore 合成予定"
  plan ".gitignore を生成 (_common/.gitignore + 各 .gitignore.append)"

  if has_component github; then
    log "[dry-run] dependabot 合成予定"
    plan ".github/dependabot.yml を生成 (github 基底 + 各 dependabot.fragment.yml)"
  fi

  log "[dry-run] pre-commit config 選択予定"
  if ((main_guard)); then
    plan ".pre-commit-config.yaml <- .pre-commit-config.guard.yaml (main guard 版)"
  else
    plan ".pre-commit-config.yaml は通常版を採用 (.pre-commit-config.guard.yaml は削除)"
  fi

  log "[dry-run] post_scaffold 予定"
  while IFS= read -r c; do
    hook="${COMPONENTS_DIR}/${c}/post_scaffold.sh"
    [[ -x "$hook" ]] || continue
    printf '  %s%s:%s\n' "$c_bold" "$c" "$c_reset" >&2
    TARGET_DIR="$target" \
      COMPONENT_DIR="${COMPONENTS_DIR}/${c}" \
      PROJECT_NAME="$project_name" \
      PROJECT_SLUG="$project_slug" \
      GITHUB_USER="$github_user" \
      OFFLINE="$offline" \
      DRY_RUN=1 \
      bash "$hook" 2>&1 | sed 's/^/  /' >&2
  done < <(post_scaffold_order)

  log "[dry-run] 実行予定コマンド"
  if ((no_install)); then
    plan "(--no-install のためファイル生成のみ。実行系はスキップ)"
  else
    if ((offline)); then
      plan "(offline) mise install はスキップ"
    else
      plan "mise -C ${target} install"
    fi
  fi

  log "[dry-run] 完了 (何も書き込んでいません)"
  exit 0
fi

# ---- 実書き込み ----

copy_skip_existing() {
  local c="$1"
  local -a would=()
  while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    would+=("${rel#'  + '}")
  done < <(rp_copy_component "$c" "$target" --dry-run)

  if ((force)); then
    rp_copy_component "$c" "$target"
    return 0
  fi

  # force でない場合、既存ファイルはコピー元から除外してコピーする。
  # rp_copy_component はコンポーネント単位なので、既存ファイルを一時的に
  # 除外した src を作るのではなく、個別コピーで代替する。
  local src="${COMPONENTS_DIR}/${c}"
  local rel dest
  for rel in "${would[@]}"; do
    dest="${target}/${rel}"
    if [[ -e "$dest" ]]; then
      info "skip: ${rel} (既存, ${c})"
      continue
    fi
    mkdir -p "$(dirname "$dest")"
    cp "${src}/${rel}" "$dest"
  done
}

log "コンポーネントをコピー"
for c in "${comps[@]}"; do
  copy_skip_existing "$c"
done

log ".gitignore を合成"
gitignore_out="${target}/.gitignore"
if [[ -e "$gitignore_out" ]] && ! ((force)); then
  warn "skip: .gitignore (既存。手動マージを検討してください)"
else
  rp_merge_gitignore "${COMPONENTS_DIR}/_common/.gitignore" "$gitignore_out" "${comps[@]}"
fi

log "mise.toml を生成"
mise_toml="${target}/mise.toml"
if [[ -e "$mise_toml" ]] && ! ((force)); then
  warn "skip: mise.toml (既存。手動マージを検討してください)"
else
  rp_merge_mise_toml "$mise_toml" "${comps[@]}"
  rp_generate_aggregate_tasks "${comps[@]}" >>"$mise_toml"
  # 生成物末尾の連続空行を除去し、末尾を単一改行に正規化する
  # （taplo fmt --check が末尾空行を差分検出して toml:lint が落ちるのを防ぐ）。
  rp_trim_trailing_blank_lines "$mise_toml"
fi

if has_component github; then
  dependabot_out="${target}/.github/dependabot.yml"
  if [[ -e "$dependabot_out" ]] && ! ((force)); then
    warn "skip: .github/dependabot.yml (既存。手動マージを検討してください)"
  else
    log "dependabot.yml を合成"
    mkdir -p "${target}/.github"
    rp_compose_dependabot "$dependabot_out" \
      "${COMPONENTS_DIR}/github/.github/dependabot.yml" "${comps[@]}"
  fi
fi

log "pre-commit config を選択"
guard_file="${target}/.pre-commit-config.guard.yaml"
normal_file="${target}/.pre-commit-config.yaml"
if [[ -f "$guard_file" ]]; then
  if ((main_guard)); then
    if [[ -e "$normal_file" ]] && ! ((force)); then
      warn "skip: .pre-commit-config.yaml (既存。main-guard 版は採用しませんでした)"
    else
      cp "$guard_file" "$normal_file"
      info "main-guard 版を採用しました"
    fi
  fi
  rm -f "$guard_file"
fi

log "プレースホルダを置換"
rp_substitute_placeholders "$target" "$project_name" "$project_slug" "$github_user"

if ((no_install)); then
  log "--no-install のため mise install / post_scaffold をスキップ"
else
  if ((offline)); then
    info "(offline) mise install をスキップ"
  elif command -v mise >/dev/null 2>&1; then
    log "mise install"
    mise -C "$target" install
  else
    warn "mise が見つかりません。mise install をスキップしました。"
  fi

  log "post_scaffold を実行"
  # mise install で target に入れたツール (pre-commit / git-secrets / uv /
  # pnpm) は親シェルの PATH には無いため、mise がある場合は
  # `mise -C <target> exec --` でラップして post_scaffold に PATH を通す。
  hook_runner=()
  if command -v mise >/dev/null 2>&1; then
    hook_runner=(mise -C "$target" exec -- bash)
  else
    hook_runner=(bash)
  fi
  while IFS= read -r c; do
    hook="${COMPONENTS_DIR}/${c}/post_scaffold.sh"
    [[ -x "$hook" ]] || continue
    log "post_scaffold: ${c}"
    TARGET_DIR="$target" \
      COMPONENT_DIR="${COMPONENTS_DIR}/${c}" \
      PROJECT_NAME="$project_name" \
      PROJECT_SLUG="$project_slug" \
      GITHUB_USER="$github_user" \
      OFFLINE="$offline" \
      DRY_RUN=0 \
      "${hook_runner[@]}" "$hook"
  done < <(post_scaffold_order)

  log "プレースホルダを再置換 (post_scaffold 後)"
  rp_substitute_placeholders "$target" "$project_name" "$project_slug" "$github_user"
fi

log "完了: ${target}"
info "導入したコンポーネント: ${comps[*]}"
printf '%s次のステップ%s\n' "${c_bold}" "${c_reset}" >&2
printf '  cd %s\n' "$target" >&2
((no_install)) && printf '  mise install\n' >&2
printf '  mise run lint\n' >&2
