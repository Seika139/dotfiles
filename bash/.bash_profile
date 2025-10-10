#!/usr/bin/env bash

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

# シェルの種類とホームディレクトリ情報をログ出力
printf "%s\n" "✨ Starting bash initialization..."
printf "Shell: \033[36m%s\033[0m, OSTYPE: \033[36m%s\033[0m, HOME: \033[36m%s\033[0m, BDOTDIR: \033[36m%s\033[0m\n" "$SHELL" "$OSTYPE" "$HOME" "$BDOTDIR"

# .bashrcを読み込む
if [ -f "${BDOTDIR}/.bashrc" ]; then
    # shellcheck disable=SC1091
    source "${BDOTDIR}/.bashrc"
else
    echo "Warning: ${BDOTDIR}/.bashrc not found!"
    # フォールバック: 標準の.bashrcを読み込む
    if [ -f "$HOME/.bashrc" ]; then
        # shellcheck disable=SC1091
        source "$HOME/.bashrc"
    fi
fi
