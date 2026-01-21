#!/usr/bin/env bash

# shellcheck disable=SC2034

# git のコマンドの補完ツール(mac用)
# ref : https://qiita.com/NorsteinBekkler/items/a0622ee6a39d08d61b72
# ref : https://smootech.hatenablog.com/entry/2017/02/23/102531

prompt_files=(
  '/opt/homebrew/etc/bash_completion.d/git-prompt.sh'    # Homebrew on M1 Mac
  '/usr/lib/git-core/git-sh-prompt'                      # Linux
  '/c/Program Files/Git/etc/profile.d/git-prompt.sh'     # Git for Windows
  '/usr/share/git/completion/git-prompt.sh'              # その他のLinux系
  '/etc/bash_completion.d/git-prompt.sh'                 # その他のLinux系
  '/usr/local/etc/bash_completion.d/git-prompt.sh'       # その他のLinux系
  '/usr/share/git-core/contrib/completion/git-prompt.sh' # その他のLinux系
)
found=false

for file in "${prompt_files[@]}"; do
  if [ -f "${file}" ]; then
    # shellcheck disable=SC1090
    source "${file}"
    found=true
    break
  fi
done

if [ "${found}" = false ]; then
  warn "git-prompt に必要なファイルが見つかりません(違う場所にある可能性もあります)"
fi

# Gitブランチの状況を*+%で表示
GIT_PS1_SHOWDIRTYSTATE=true
GIT_PS1_SHOWUNTRACKEDFILES=true
GIT_PS1_SHOWSTASHSTATE=true
GIT_PS1_SHOWUPSTREAM=auto
