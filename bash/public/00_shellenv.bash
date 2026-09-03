#!/usr/bin/env bash

# Homebrew にパスを通す (Mac の場合)
# これをしないと brew install したコマンドの設定ができない
# 例えばこんなことをしたくても zoxide コマンドが認識されない
#
# if command -v zoxide &>/dev/null; then
#   eval "$(zoxide init bash)"
# fi
#
# なので先ず Homebrew へのパスを通すことが大事

if [ -f /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

#------------------------------------------------------------------------------------------------
# mise が存在する場合に bash 用の設定を有効化する
#
# mise use -g <package> を実行すると package は グローバル設定に追加される
# シェル起動時にグローバル設定を自動的に PATH に追加するために以下の処理で対応している
#------------------------------------------------------------------------------------------------
if command -v mise &>/dev/null; then
  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows の git-bash では mise.exe が Windows 形式の PATH (C:\...;C:\...) を出力する。
    # これを eval すると Unix 形式の PATH が破壊され、sed/date/grep など coreutils が
    # command not found になる。そのため activate は使わず、shims ディレクトリを Unix 形式パスに
    # 変換して PATH の先頭へ追加し、mise 管理ツールを git-bash から呼べるようにする。
    mise_shims="$(cygpath -u "${LOCALAPPDATA:-$HOME/AppData/Local}/mise/shims" 2>/dev/null)"
    if [ -n "$mise_shims" ] && [ -d "$mise_shims" ]; then
      case ":$PATH:" in
      *":$mise_shims:"*) ;;
      *) export PATH="$mise_shims:$PATH" ;;
      esac
    fi
    unset mise_shims
  else
    eval "$(mise activate bash)"
  fi
fi
