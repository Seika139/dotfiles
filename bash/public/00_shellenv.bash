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
