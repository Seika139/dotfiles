#!/usr/bin/env bash

# `bash/envs` ディレクトリから環境プロファイルを読み込む仕組み。
# 01_select_env.bash で読み込み対象のファイル名を配列 `BDOT_ENV_PROFILE_FILES`
# として指定し、ここで実際に source する。

ENV_DIR="${BDOTDIR:-$HOME/dotfiles/bash}/envs"
SELECT_FILE="${ENV_DIR}/01_select_env.bash"
SELECT_SAMPLE_FILE="${ENV_DIR}/01_select_env.sample.bash"
USED_SELECT_FILE="$SELECT_FILE"

load_file() {
  local file_path="$1"
  [[ -f "$file_path" ]] || return 1
  # shellcheck disable=SC1090
  source "$file_path"
  return 0
}

if ! load_file "$SELECT_FILE" && [[ -f "$SELECT_SAMPLE_FILE" ]]; then
  load_file "$SELECT_SAMPLE_FILE"
  USED_SELECT_FILE="$SELECT_SAMPLE_FILE"
  if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE:-0}" == "1" ]]; then
    printf '🚨 \033[31m[Env Warning] \033[36m%s\033[31m が見つからないため sample を読み込みました。\033[0m\n' "$SELECT_FILE"
  fi
fi

if [[ ${#BDOT_ENV_PROFILE_FILES[@]} -eq 0 ]]; then
  if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE:-0}" == "1" ]]; then
    printf '🚨 \033[31m[Env Warning] BDOT_ENV_PROFILE_FILES が設定されていません。\033[36m %s\033[31m を編集してください。\033[0m\n' "$SELECT_FILE"
  fi
else
  for profile_file in "${BDOT_ENV_PROFILE_FILES[@]}"; do
    profile_path="${ENV_DIR}/${profile_file}"
    if ! load_file "$profile_path"; then
      if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE:-0}" == "1" ]]; then
        printf '🚨 \033[31m[Env Warning] \033[36m%s\033[31m を読み込めませんでした。\033[0m\n' "$profile_path"
      fi
    fi
  done
fi

# 必要な環境変数が設定されているか確認する関数
check_required_env_vars() {
  local missing_vars=()
  for var in "$@"; do
    if [[ -z "${!var}" ]]; then
      missing_vars+=("$var")
    fi
  done

  if ((${#missing_vars[@]} > 0)); then
    printf '🚨 \033[31m[Env Error] 以下の環境変数が設定されていません。\033[36m%s\033[31m を確認してください。\033[33m\n %s\033[0m\n' "$USED_SELECT_FILE" "${missing_vars[*]}" >&2
    return 1
  fi
  return 0
}

# 読み込み後に必須とする環境変数を配列 BDOT_ENV_REQUIRED_VARS に列挙できるようにする
if [[ -z "${BDOT_ENV_REQUIRED_VARS+x}" ]]; then
  BDOT_ENV_REQUIRED_VARS=(
    "BDOTDIR"
    "BDOT_ACTIVE_PROFILE"
  )
fi

if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE:-0}" == "1" ]] && ((${#BDOT_ENV_REQUIRED_VARS[@]} > 0)); then
  check_required_env_vars "${BDOT_ENV_REQUIRED_VARS[@]}"
fi

unset -f load_file
unset -f check_required_env_vars
unset ENV_DIR SELECT_FILE SELECT_SAMPLE_FILE USED_SELECT_FILE profile_file profile_path
