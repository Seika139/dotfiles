#!/usr/bin/env bash

# dotfiles で作成したシンボリックリンクを解除する

DOTFILES_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/" && pwd)"

util_bash="$DOTFILES_ROOT/bash/public/01_util.bash"
if [ ! -e "${util_bash}" ]; then
  echo "No such file ${util_bash}"
  exit 1
else
  # shellcheck source=/dev/null
  source "${util_bash}"
fi

main() {
  echo_yellow 'ホームディレクトリに作成した dotfiles 関連のシンボリックリンクを削除します。'
  read -r -p "$(echo_yellow '実行してもよろしいですか？ [y/N]: ')" ans1
  if [[ $ans1 != [yY] ]]; then
    info "unlink をスキップしました。"
    return 0
  fi
  unset ans1

  # $HOME のシンボリックリンクを削除する
  linked_files=(
    ".bash_logout"
    ".bash_profile"
    ".cursor"
    ".gitconfig"
    ".gitconfig.local"
    ".gitignore_global"
    ".gitmessage"
    ".tmux.conf"
  )

  for file in "${linked_files[@]}"; do
    abs_path=$(abs_path "${HOME}/${file}")
    if [[ -L "${abs_path}" && $(readlink "${abs_path}") = *dotfiles* ]]; then
      echo_yellow "Removing symlink: ${abs_path}"
      rm "${abs_path}"
    fi
  done
  unset linked_files file abs_path

  # Claude 設定のシンボリックリンクを削除する
  claude_linked_files=(
    ".claude/settings.json"
    ".claude/settings.local.json"
    ".claude/CLAUDE.md"
    ".claude/commands"
  )
  for file in "${claude_linked_files[@]}"; do
    abs_path=$(abs_path "${HOME}/${file}")
    if [[ -L "${abs_path}" && $(readlink "${abs_path}") = *dotfiles* ]]; then
      echo "Removing Claude symlink: ${abs_path}"
      rm "${abs_path}"
    fi
  done
  unset claude_linked_files file abs_path

  # Codex 設定のシンボリックリンクを削除する
  codex_linked_files=(
    ".codex/config.toml"
    ".codex/AGENTS.md"
  )
  for file in "${codex_linked_files[@]}"; do
    abs_path=$(abs_path "${HOME}/${file}")
    if [[ -L "${abs_path}" && $(readlink "${abs_path}") = *dotfiles* ]]; then
      echo "Removing Codex symlink: ${abs_path}"
      rm "${abs_path}"
    fi
  done
  unset codex_linked_files file abs_path
}

main "$@"
