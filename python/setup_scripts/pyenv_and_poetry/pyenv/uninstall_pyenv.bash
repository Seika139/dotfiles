#!/bin/bash

set -euo pipefail

# 定数と関数を定義する
BASHRC="$HOME/.bashrc"
PYENV_ROOT="$HOME/.pyenv"

log_info() {
  echo -e "\033[00;33m[INFO]\033[0m $*"
}

log_error() {
  echo -e "\033[00;31m[ERROR]\033[0m $*" >&2
}

log_success() {
  echo -e "\033[00;32m[SUCCESS]\033[0m $*"
}

# 本当にアンインストールしていいか確認する関数
confirm_uninstallation() {
  log_info "This will remove pyenv and its configurations from your system."
  read -rp "Do you want to uninstall pyenv? [y/N] " response
  if [[ ! $response =~ ^[Yy]$ ]]; then
    log_info "Uninstallation cancelled."
    exit 0
  fi
}

# .bashrcから設定を削除する関数
remove_bashrc_config() {
  local temp_file
  temp_file=$(mktemp)
  local in_pyenv_section=0

  # 行ごとに処理して、pyenv設定部分のみを除外
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "# pyenv settings" ]]; then
      in_pyenv_section=1
      continue
    fi

    if [[ $in_pyenv_section -eq 1 ]]; then
      # shellcheck disable=SC2016
      if [[ "$line" == 'eval "$(pyenv init -)"' ]]; then
        in_pyenv_section=0
        continue
      fi
      continue
    fi

    echo "$line" >>"$temp_file"
  done <"$BASHRC"

  # 末尾の連続する空行を1つにまとめる
  awk '
    NF {
        if (buf) {
            print buf
            buf = ""
        }
        print
        empty = 0
    }
    !NF {
        if (!empty) buf = $0
        empty = 1
    }
    END {
        if (!empty && buf) print buf
    }
    ' "$temp_file" >"${temp_file}.clean"

  # 元のファイルを置き換え
  mv "${temp_file}.clean" "$BASHRC"
  rm -f "$temp_file"
}

# 削除対象の設定を表示する関数
show_config_to_remove() {
  log_info "The following configuration will be removed:"
  echo "----------------------------------------"
  # shellcheck disable=SC2016
  sed -n '/# pyenv settings/,/eval "$(pyenv init -)"/p' "$BASHRC"
  echo "----------------------------------------"
  read -rp "Continue with removal? [y/N] " response
  if [[ ! $response =~ ^[Yy]$ ]]; then
    log_info "Uninstallation cancelled."
    exit 0
  fi
}

# メイン処理
main() {
  # pyenv がインストールされているか確認
  if [ ! -d "$PYENV_ROOT" ]; then
    log_error "pyenv is not installed at $PYENV_ROOT"
    exit 1
  fi

  # 設定の確認と削除の承認を一度に行う
  if [ -f "$BASHRC" ]; then
    show_config_to_remove # この関数内で確認を行うため、confirm_uninstallationは不要
  else
    confirm_uninstallation # .bashrcが存在しない場合のみこちらを使用
  fi

  # .bashrcのバックアップを作成する
  if [ -f "$BASHRC" ]; then
    if ! cp "$BASHRC" "${BASHRC}.backup.$(date +%Y%m%d_%H%M%S)"; then
      log_error "Failed to create backup of .bashrc"
      exit 1
    fi
    log_info "Created backup of .bashrc"
  fi

  # pyenvディレクトリを削除する
  log_info "Removing pyenv directory..."
  if ! rm -rf "$PYENV_ROOT"; then
    log_error "Failed to remove pyenv directory"
    exit 1
  fi

  # .bashrcから設定を削除する
  log_info "Removing pyenv configuration from .bashrc..."
  if [ -f "$BASHRC" ]; then
    remove_bashrc_config

    # .bashrc が空になった場合、またはシェバン行しか残っていない場合はリセットする
    if [[ $(grep -cv -E '^(#!/.*|\s*)$' "$BASHRC") -eq 0 ]]; then
      log_info "Removing empty .bashrc..."
      rm "$BASHRC"
    fi
  fi

  # アンインストール完了
  log_success "Uninstallation completed successfully!"

  if [ -f "$BASHRC" ]; then
    log_info "Please run the following command to apply changes:"
    echo "    source $BASHRC"
  else
    log_info "Please start a new shell session to apply changes."
  fi
}

main
