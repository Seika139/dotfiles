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

  mise_config_root="${MISE_CONFIG_DIR:-${XDG_CONFIG_HOME:-${HOME}/.config}/mise}"
  mise_profile_link="${mise_config_root}/conf.d/dotfiles-profile.toml"
  mise_profile_target=""
  if [[ -L "${mise_profile_link}" ]]; then
    mise_profile_target="$(readlink "${mise_profile_link}")"
    case "${mise_profile_target}" in
    "${DOTFILES_ROOT}"/mise/profiles/*.toml)
      mise_profile_target_name="${mise_profile_target#"${DOTFILES_ROOT}/mise/profiles/"}"
      if [[ "${mise_profile_target_name}" != */* && "${mise_profile_target_name}" =~ ^[A-Za-z0-9_-]+\.toml$ ]]; then
        echo_yellow "Removing mise profile symlink: ${mise_profile_link}"
        rm "${mise_profile_link}"
      fi
      ;;
    esac
  fi
  mise_legacy_link="${mise_config_root}/conf.d/dotfiles-managed.toml"
  mise_legacy_source="${DOTFILES_ROOT}/mise/global.toml"
  if [[ -L "${mise_legacy_link}" && "$(readlink "${mise_legacy_link}")" == "${mise_legacy_source}" ]]; then
    echo_yellow "Removing legacy mise symlink: ${mise_legacy_link}"
    rm "${mise_legacy_link}"
  fi
  unset mise_config_root mise_profile_link mise_profile_target mise_profile_target_name mise_legacy_link mise_legacy_source

  # $HOME/.ssh のシンボリックリンクを削除する
  if ! command grep -qEi "(Microsoft|WSL)" /proc/version &>/dev/null; then
    ssh_linked_files=(
      ".ssh/config"
      ".ssh/config.secret"
    )
    for file in "${ssh_linked_files[@]}"; do
      abs_path=$(abs_path "${HOME}/${file}")
      if [[ -L "${abs_path}" && $(readlink "${abs_path}") = *dotfiles* ]]; then
        echo_yellow "Removing symlink: ${abs_path}"
        rm "${abs_path}"
      fi
    done
    unset ssh_linked_files file abs_path
  fi

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

  # rumdl 設定のシンボリックリンクを削除する
  rumdl_config_path="${HOME}/.config/rumdl/rumdl.toml"
  rumdl_config_source="${DOTFILES_ROOT}/vscode-settings/extension-config/.rumdl.toml"
  if [[ -L "${rumdl_config_path}" && $(readlink "${rumdl_config_path}") = "${rumdl_config_source}" ]]; then
    echo "Removing rumdl symlink: ${rumdl_config_path}"
    rm "${rumdl_config_path}"
  fi
  unset rumdl_config_path rumdl_config_source
}

main "$@"
