#!/usr/bin/env bash

# 対話的シェルのみ日次処理を有効化
if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE}" != "1" ]]; then
  return
fi

# キャッシュディレクトリ初期化
: "${BDOTDIR_DAILY_ROOT:=${BDOTDIR}/daily}"
: "${BDOTDIR_DAILY_CACHE_DIR:=${BDOTDIR_DAILY_ROOT}/.cache}"

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

_bdotdir_daily_log_info() {
  if declare -F info >/dev/null 2>&1; then
    info "$@"
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

bdotdir_run_once_per_day() {
  if [[ $# -lt 2 ]]; then
    _bdotdir_daily_log_warn "bdotdir_run_once_per_day: cache key とコマンドを指定してください"
    return 1
  fi

  local key="$1"
  shift
  local -a command=("$@")

  local normalized_key
  normalized_key="$(_bdotdir_normalize_cache_key "$key")"
  local cache_file="${BDOTDIR_DAILY_CACHE_DIR}/${normalized_key}.stamp"
  local today
  today="$(date +%Y-%m-%d)"

  if [[ -f "$cache_file" ]]; then
    local last_run
    last_run="$(<"$cache_file")"
    if [[ "$last_run" == "$today" ]]; then
      return 0
    fi
  fi

  if "${command[@]}"; then
    printf '%s\n' "$today" >"$cache_file"
    _bdotdir_daily_log_info "日次コマンド(${key})を実行しました"
    return 0
  fi

  local exit_code=$?
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
    absolute_path="$(pwd)/$script_path"
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

  bdotdir_run_once_per_day "$absolute_path" "${runner[@]}"
}

_bdotdir_run_profile_daily_scripts() {
  local profile_dir="${BDOTDIR_DAILY_ROOT}/profile/${DAILY_PROFILE}"

  if [[ ! -d "$profile_dir" ]]; then
    _bdotdir_daily_log_warn "プロファイルディレクトリが見つかりません: ${profile_dir}"
    return 1
  fi

  while IFS= read -r script; do
    bdotdir_run_daily_script "$script"
  done < <(LC_ALL=C find "${profile_dir}" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.bash' \) -print | LC_ALL=C sort)
}

_bdotdir_run_profile_daily_scripts

unset -f _bdotdir_daily_log_info _bdotdir_daily_log_warn _bdotdir_normalize_cache_key \
  _bdotdir_run_profile_daily_scripts
