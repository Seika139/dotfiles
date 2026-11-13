#!/usr/bin/env bash
# mise タスクの共通関数。各タスクで ROOT_DIR を定義してから source する。
# shellcheck disable=SC2034

SETTINGS_PY="${ROOT_DIR}/mise/scripts/settings.py"
EDITORS=(vscode cursor agy)

# Python の実行コマンドを PY に入れる
resolve_python() {
  PY="$(command -v python3 || command -v python || true)"
  if [ -z "$PY" ]; then
    echo "❌ python3 / python が見つかりません" >&2
    return 1
  fi
}

# プロファイル名 (--prof か DEFAULT_PROFILE) と、そのディレクトリを PROFILE / PROFILE_DIR に入れる
resolve_profile() {
  PROFILE="${usage_prof:-${DEFAULT_PROFILE:-}}"
  PROFILE_DIR="${PROFILE_ROOT:-}/${PROFILE}"
}

require_profile_dir() {
  if [ ! -d "$PROFILE_DIR" ]; then
    echo "❌ プロファイルディレクトリが見つかりません: $PROFILE_DIR"
    return 1
  fi
}

# CONFIG_FILES (空白区切り) を配列 CONFIG_FILE_LIST にする
load_config_files() {
  read -r -a CONFIG_FILE_LIST <<<"${CONFIG_FILES:-}"
}

# mise.toml の [env] にある "$HOME/..." や "$(...)" を展開する (env_shell_expand = false のため自前で展開)
expand_path() {
  # shellcheck disable=SC2294
  eval "printf '%s' \"$1\""
}

# エディタ名 (vscode / cursor / agy / antigravity) から展開済みのパスを出力する
editor_path_for() {
  local raw
  case "$1" in
  vscode) raw="${VSCODE_PATH:-}" ;;
  cursor) raw="${CURSOR_PATH:-}" ;;
  agy | antigravity) raw="${AGY_PATH:-}" ;;
  *) return 1 ;;
  esac
  expand_path "$raw"
}

# エディタのパスを検査する。0: 問題なし、1: 空または相対パス、2: // を含む
check_editor_path() {
  case "$1" in
  *//*) return 2 ;;
  /* | [A-Za-z]:*) return 0 ;;
  *) return 1 ;;
  esac
}
