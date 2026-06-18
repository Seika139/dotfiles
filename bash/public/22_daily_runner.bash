#!/usr/bin/env bash

# 対話的シェルのみ日次処理を有効化
if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE}" != "1" ]]; then
  return
fi

# キャッシュディレクトリ初期化
BDOTDIR_DAILY_ROOT="${BDOTDIR}/daily"
BDOTDIR_DAILY_CACHE_DIR="${BDOTDIR_DAILY_ROOT}/.cache"

if [[ ! -d "${BDOTDIR_DAILY_CACHE_DIR}" ]]; then
  if ! mkdir -p "${BDOTDIR_DAILY_CACHE_DIR}"; then
    printf '%s\n' "日次キャッシュディレクトリの作成に失敗しました: ${BDOTDIR_DAILY_CACHE_DIR}" >&2
    return
  fi
fi

# プロファイル設定の読み込み
if [[ -f "${BDOTDIR_DAILY_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  source "${BDOTDIR_DAILY_ROOT}/.env"
fi
: "${DAILY_PROFILE:=default}"

_bdotdir_daily_log_verbose() {
  if declare -F verbose >/dev/null 2>&1; then
    verbose "$@"
  else
    printf '%s\n' "$*"
  fi
}

_bdotdir_daily_log_warn() {
  if declare -F warn >/dev/null 2>&1; then
    warn "$@"
  else
    printf '%s\n' "$*" >&2
  fi
}

_bdotdir_normalize_cache_key() {
  local key="$1"
  key="${key//[^A-Za-z0-9_.-]/_}"
  printf '%s' "$key"
}

_bdotdir_daily_stamp_is_today() {
  local stamp_file="$1"
  local today="$2"
  local last_run

  [[ -f "$stamp_file" ]] || return 1
  last_run="$(<"$stamp_file")"
  [[ "$last_run" == "$today" ]]
}

_bdotdir_daily_write_stamp() {
  local stamp_file="$1"
  local today="$2"

  printf '%s\n' "$today" >"$stamp_file"
}

_bdotdir_daily_command_stamp_file() {
  local key="$1"
  local profile_key normalized_key

  profile_key="$(_bdotdir_normalize_cache_key "$DAILY_PROFILE")"
  normalized_key="${profile_key}__$(_bdotdir_normalize_cache_key "$key")"
  printf '%s/%s.stamp' "$BDOTDIR_DAILY_CACHE_DIR" "$normalized_key"
}

_bdotdir_daily_try_create_attempt() {
  local attempt_file="$1"
  local today="$2"

  (
    set -o noclobber
    {
      printf 'date=%s\n' "$today"
      printf 'profile=%s\n' "$DAILY_PROFILE"
      printf 'pid=%s\n' "${BASHPID:-$$}"
      printf 'created_at=%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
    } >"$attempt_file"
  ) 2>/dev/null
}

_bdotdir_daily_log_script_skip_status() {
  local script_path="$1"
  local today="$2"
  local cache_file

  cache_file="$(_bdotdir_daily_command_stamp_file "$script_path")"
  if _bdotdir_daily_stamp_is_today "$cache_file" "$today"; then
    _bdotdir_daily_log_verbose "日次コマンド(${script_path})は既に実行済みです"
  else
    _bdotdir_daily_log_verbose "日次コマンド(${script_path})は本日すでに起動済みです（正常完了は未確認）"
  fi
}

bdotdir_run_once_per_day() {
  if [[ $# -lt 2 ]]; then
    _bdotdir_daily_log_warn "bdotdir_run_once_per_day: cache key とコマンドを指定してください"
    return 1
  fi

  local key="$1"
  shift
  local -a command=("$@")

  local cache_file
  cache_file="$(_bdotdir_daily_command_stamp_file "$key")"
  local today
  today="$(date +%Y-%m-%d)"

  if _bdotdir_daily_stamp_is_today "$cache_file" "$today"; then
    _bdotdir_daily_log_verbose "日次コマンド(${key})は既に実行済みです"
    return 0
  fi

  _bdotdir_daily_log_verbose "日次コマンド(${key})を実行します..."
  # 起動元シェルの stdin を継承すると、VS Code/WSL の pipe を読んで残ることがある。
  local exit_code
  if "${command[@]}" </dev/null; then
    _bdotdir_daily_write_stamp "$cache_file" "$today"
    _bdotdir_daily_log_verbose "日次コマンド(${key})の実行が完了しました"
    return 0
  else
    exit_code=$?
  fi

  _bdotdir_daily_log_warn "日次コマンド(${key})の実行に失敗しました (exit ${exit_code})"
  return $exit_code
}

bdotdir_run_daily_script() {
  if [[ $# -lt 1 ]]; then
    _bdotdir_daily_log_warn "bdotdir_run_daily_script: スクリプトパスを指定してください"
    return 1
  fi

  local script_path="$1"
  shift
  local -a script_args=("$@")

  if [[ ! -f "$script_path" ]]; then
    _bdotdir_daily_log_warn "日次スクリプトが見つかりません: ${script_path}"
    return 1
  fi

  local absolute_path="$script_path"
  if [[ ! "$script_path" = /* ]]; then
    # 絶対パスでない場合は BDOTDIR からの相対パスとして解決を試みる
    if [[ -f "${BDOTDIR}/${script_path}" ]]; then
      absolute_path="${BDOTDIR}/${script_path}"
    fi
  fi

  local -a runner
  if [[ -x "$absolute_path" ]]; then
    runner=("$absolute_path")
  else
    runner=("/usr/bin/env" "bash" "$absolute_path")
  fi

  if [[ ${#script_args[@]} -gt 0 ]]; then
    runner+=("${script_args[@]}")
  fi

  local script_timeout="${BDOTDIR_DAILY_SCRIPT_TIMEOUT:-1800}"
  if [[ "$script_timeout" =~ ^[1-9][0-9]*$ ]] && command -v timeout >/dev/null 2>&1; then
    runner=("timeout" "$script_timeout" "${runner[@]}")
  fi

  bdotdir_run_once_per_day "$absolute_path" "${runner[@]}"
}

_bdotdir_run_profile_daily_scripts() {
  local profile_dir="${BDOTDIR_DAILY_ROOT}/profile/${DAILY_PROFILE}"
  local profile_key today attempt_file legacy_runner_stamp

  profile_key="$(_bdotdir_normalize_cache_key "$DAILY_PROFILE")"
  today="$(date +%Y-%m-%d)"
  attempt_file="${BDOTDIR_DAILY_CACHE_DIR}/runner-${profile_key}-${today}.attempt"
  legacy_runner_stamp="${BDOTDIR_DAILY_CACHE_DIR}/runner-${profile_key}.stamp"

  if [[ ! -d "$profile_dir" ]]; then
    _bdotdir_daily_log_warn "プロファイルディレクトリが見つかりません: ${profile_dir}"
    return 1
  fi

  local -a scripts=()
  while IFS= read -r script; do
    [[ -n "$script" ]] && scripts+=("$script")
  done < <(LC_ALL=C find "${profile_dir}" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.bash' \) -print | LC_ALL=C sort)

  if [[ ${#scripts[@]} -eq 0 ]]; then
    return 0
  fi

  if [[ -e "$attempt_file" ]] || _bdotdir_daily_stamp_is_today "$legacy_runner_stamp" "$today"; then
    for script in "${scripts[@]}"; do
      _bdotdir_daily_log_script_skip_status "$script" "$today"
    done
    return 0
  fi

  if ! _bdotdir_daily_try_create_attempt "$attempt_file" "$today"; then
    for script in "${scripts[@]}"; do
      _bdotdir_daily_log_script_skip_status "$script" "$today"
    done
    return 0
  fi

  for script in "${scripts[@]}"; do
    bdotdir_run_daily_script "$script"
  done
}

(
  _bdotdir_run_profile_daily_scripts
)

unset -f _bdotdir_daily_log_verbose _bdotdir_daily_log_warn _bdotdir_normalize_cache_key \
  _bdotdir_daily_stamp_is_today _bdotdir_daily_write_stamp _bdotdir_daily_command_stamp_file \
  _bdotdir_daily_try_create_attempt _bdotdir_daily_log_script_skip_status \
  bdotdir_run_once_per_day bdotdir_run_daily_script _bdotdir_run_profile_daily_scripts
