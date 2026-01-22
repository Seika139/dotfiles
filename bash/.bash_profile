#!/usr/bin/env bash

# shellcheck disable=SC1091

# BDOTDIRが設定されていない場合は、デフォルト値を設定
if [ -z "${BDOTDIR}" ]; then
  # dotfilesディレクトリの推定（ユーザーのホームディレクトリ下のdotfiles/bashを想定）
  export BDOTDIR="${HOME}/dotfiles/bash"
  # Windowsパスの場合は変換を試みる
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windowsパスをmsys/cygwinパスに変換
    if [[ "$HOME" =~ ^[A-Za-z]:\\ ]]; then
      # ドライブレターを取得してパス変換
      drive_letter="${HOME%%:*}"
      export BDOTDIR="/${drive_letter,,}/Users/${USER}/dotfiles/bash"
    fi
  fi
fi

# 対話的かどうかを毎回判定（install.sh などの非対話実行で 0 が残り続けるのを防ぐ）
if [[ $- == *i* ]] && [[ -t 1 ]]; then
  BDOTDIR_SHELL_IS_INTERACTIVE=1
else
  BDOTDIR_SHELL_IS_INTERACTIVE=0
fi
export BDOTDIR_SHELL_IS_INTERACTIVE

if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE}" == "1" ]]; then
  # シェルの種類とホームディレクトリ情報をログ出力
  printf "%s\n" "✨ Starting bash initialization..."
  printf "Shell: \033[36m%s\033[0m, OSTYPE: \033[36m%s\033[0m, HOME: \033[36m%s\033[0m, BDOTDIR: \033[36m%s\033[0m\n" "$SHELL" "$OSTYPE" "$HOME" "$BDOTDIR"
fi

# まずシステム/コンテナの.bashrcを読み込む（存在する場合）
# Devcontainer で dotfiles を使う場合を想定
if [ -f "$HOME/.bashrc" ] && [ "$HOME/.bashrc" != "${BDOTDIR}/.bashrc" ]; then
  source "$HOME/.bashrc"
fi

# 自前の .bashrcを読み込む
if [ -f "${BDOTDIR}/.bashrc" ]; then
  source "${BDOTDIR}/.bashrc"
else
  [[ "${BDOTDIR_SHELL_IS_INTERACTIVE}" == "1" ]] && echo "Warning: ${BDOTDIR}/.bashrc not found!"
fi
