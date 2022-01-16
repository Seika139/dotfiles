#!/usr/bin/env bash

# bash のコマンドの補完ツール(mac用)
# 参考 : https://qiita.com/NorsteinBekkler/items/a0622ee6a39d08d61b72

if executable brew; then
    if [ -f $(brew --prefix)/etc/bash_completion ]; then
        source $(brew --prefix)/etc/bash_completion
    fi
fi
