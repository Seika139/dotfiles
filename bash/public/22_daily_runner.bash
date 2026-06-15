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

_bdotdir_daily_proc_start_time() {
  local pid="$1"
  local stat rest
  [[ -r "/proc/${pid}/stat" ]] || return 1

  stat="$(<"/proc/${pid}/stat")"
  rest="${stat#*) }"
  # shellcheck disable=SC2086
  set -- $rest
  [[ -n "${20:-}" ]] || return 1
  printf '%s' "${20}"
}

_bdotdir_daily_boot_id() {
  [[ -r /proc/sys/kernel/random/boot_id ]] || return 1
  cat /proc/sys/kernel/random/boot_id
}

_bdotdir_daily_process_tree_contains_profile_script() {
  local pid="$1"
  local cmdline fd_target child_pid
  local -a children=()

  [[ -d "/proc/${pid}" ]] || return 1

  if [[ -r "/proc/${pid}/cmdline" ]]; then
    cmdline="$(tr '\0' ' ' <"/proc/${pid}/cmdline")"
    if [[ "$cmdline" == *"${BDOTDIR_DAILY_ROOT}/profile/"* ]]; then
      return 0
    fi
  fi

  if [[ -e "/proc/${pid}/fd/255" ]]; then
    fd_target="$(readlink "/proc/${pid}/fd/255" 2>/dev/null || true)"
    if [[ "$fd_target" == "${BDOTDIR_DAILY_ROOT}/profile/"* ]]; then
      return 0
    fi
  fi

  if [[ -r "/proc/${pid}/task/${pid}/children" ]]; then
    read -r -a children <"/proc/${pid}/task/${pid}/children"
    for child_pid in "${children[@]}"; do
      if _bdotdir_daily_process_tree_contains_profile_script "$child_pid"; then
        return 0
      fi
    done
  fi

  return 1
}

_bdotdir_daily_read_runner_lock() {
  local lock_file="$1"
  local first_line key value

  BDOTDIR_DAILY_LOCK_PID=""
  BDOTDIR_DAILY_LOCK_START_TIME=""
  BDOTDIR_DAILY_LOCK_BOOT_ID=""
  BDOTDIR_DAILY_LOCK_CREATED_AT=""
  BDOTDIR_DAILY_LOCK_LEGACY=0

  [[ -f "$lock_file" ]] || return 1
  IFS= read -r first_line <"$lock_file" || [[ -n "$first_line" ]] || return 1

  if [[ "$first_line" =~ ^[0-9]+$ ]]; then
    BDOTDIR_DAILY_LOCK_PID="$first_line"
    BDOTDIR_DAILY_LOCK_LEGACY=1
    return 0
  fi

  while IFS='=' read -r key value; do
    case "$key" in
    pid) BDOTDIR_DAILY_LOCK_PID="$value" ;;
    start_time) BDOTDIR_DAILY_LOCK_START_TIME="$value" ;;
    boot_id) BDOTDIR_DAILY_LOCK_BOOT_ID="$value" ;;
    created_at) BDOTDIR_DAILY_LOCK_CREATED_AT="$value" ;;
    esac
  done <"$lock_file"

  [[ "$BDOTDIR_DAILY_LOCK_PID" =~ ^[0-9]+$ ]]
}

_bdotdir_daily_runner_lock_is_active() {
  local lock_file="$1"
  local pid current_start_time current_boot_id now lock_age

  _bdotdir_daily_read_runner_lock "$lock_file" || return 1
  pid="$BDOTDIR_DAILY_LOCK_PID"

  kill -0 "$pid" 2>/dev/null || return 1

  if [[ "$BDOTDIR_DAILY_LOCK_LEGACY" == "1" ]]; then
    if [[ -d /proc ]]; then
      _bdotdir_daily_process_tree_contains_profile_script "$pid"
      return $?
    fi
    return 0
  fi

  if [[ -n "$BDOTDIR_DAILY_LOCK_BOOT_ID" ]]; then
    current_boot_id="$(_bdotdir_daily_boot_id 2>/dev/null)" || return 1
    [[ "$current_boot_id" == "$BDOTDIR_DAILY_LOCK_BOOT_ID" ]] || return 1
  fi

  if [[ -n "$BDOTDIR_DAILY_LOCK_START_TIME" ]]; then
    current_start_time="$(_bdotdir_daily_proc_start_time "$pid" 2>/dev/null)" || return 1
    [[ "$current_start_time" == "$BDOTDIR_DAILY_LOCK_START_TIME" ]] || return 1
  fi

  if [[ -d /proc ]]; then
    if _bdotdir_daily_process_tree_contains_profile_script "$pid"; then
      return 0
    fi

    if [[ "$BDOTDIR_DAILY_LOCK_CREATED_AT" =~ ^[0-9]+$ ]]; then
      now="$(date +%s)"
      lock_age=$((now - BDOTDIR_DAILY_LOCK_CREATED_AT))
      ((lock_age < 5)) && return 0
    fi

    return 1
  fi

  return 0
}

_bdotdir_daily_write_runner_lock() {
  local lock_file="$1"
  local pid start_time boot_id created_at

  pid="${BASHPID:-$$}"
  start_time="$(_bdotdir_daily_proc_start_time "$pid" 2>/dev/null || true)"
  boot_id="$(_bdotdir_daily_boot_id 2>/dev/null || true)"
  created_at="$(date +%s)"

  {
    printf 'pid=%s\n' "$pid"
    [[ -n "$start_time" ]] && printf 'start_time=%s\n' "$start_time"
    [[ -n "$boot_id" ]] && printf 'boot_id=%s\n' "$boot_id"
    printf 'created_at=%s\n' "$created_at"
    printf 'profile=%s\n' "$DAILY_PROFILE"
  } >"$lock_file"
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
      _bdotdir_daily_log_verbose "日次コマンド(${key})は既に実行済みです"
      return 0
    fi
  fi

  _bdotdir_daily_log_verbose "日次コマンド(${key})を実行します..."
  # 起動元シェルの stdin を継承すると、VS Code/WSL の pipe を読んで残ることがある。
  local exit_code
  if "${command[@]}" </dev/null; then
    printf '%s\n' "$today" >"$cache_file"
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
  local lock_file="${BDOTDIR_DAILY_CACHE_DIR}/runner.lock"

  if [[ ! -d "$profile_dir" ]]; then
    _bdotdir_daily_log_warn "プロファイルディレクトリが見つかりません: ${profile_dir}"
    return 1
  fi

  # 排他制御: ロックファイルのチェック
  if [[ -f "$lock_file" ]]; then
    if _bdotdir_daily_runner_lock_is_active "$lock_file"; then
      local pid="$BDOTDIR_DAILY_LOCK_PID"
      _bdotdir_daily_log_verbose "デイリー処理が既に他のシェル(PID: ${pid})で実行中のため、スキップします"
      return 0
    fi

    local pid="${BDOTDIR_DAILY_LOCK_PID:-unknown}"
    _bdotdir_daily_log_verbose "古いロックファイル(PID: ${pid})を検出しました。実行中のデイリー処理ではないため削除して続行します"
    rm -f "$lock_file"
  fi

  # ロックの取得
  _bdotdir_daily_write_runner_lock "$lock_file"
  # 終了時にロックファイルを確実に削除するためのトラップ
  trap 'rm -f "$lock_file"' EXIT INT TERM

  # 実行対象スクリプトを収集
  local -a scripts=()
  while IFS= read -r script; do
    [[ -n "$script" ]] && scripts+=("$script")
  done < <(LC_ALL=C find "${profile_dir}" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.bash' \) -print | LC_ALL=C sort)

  if [[ ${#scripts[@]} -eq 0 ]]; then
    # スクリプトがない場合は何もしない
    rm -f "$lock_file"
    trap - EXIT INT TERM
    return 0
  fi

  for script in "${scripts[@]}"; do
    bdotdir_run_daily_script "$script"
  done

  # 正常終了時のクリーンアップ
  rm -f "$lock_file"
  trap - EXIT INT TERM
}

(
  _bdotdir_run_profile_daily_scripts
)

unset -f _bdotdir_daily_log_verbose _bdotdir_daily_log_warn _bdotdir_normalize_cache_key \
  _bdotdir_daily_proc_start_time _bdotdir_daily_boot_id \
  _bdotdir_daily_process_tree_contains_profile_script _bdotdir_daily_read_runner_lock \
  _bdotdir_daily_runner_lock_is_active _bdotdir_daily_write_runner_lock \
  bdotdir_run_once_per_day bdotdir_run_daily_script _bdotdir_run_profile_daily_scripts
unset BDOTDIR_DAILY_LOCK_PID BDOTDIR_DAILY_LOCK_START_TIME BDOTDIR_DAILY_LOCK_BOOT_ID BDOTDIR_DAILY_LOCK_CREATED_AT BDOTDIR_DAILY_LOCK_LEGACY
