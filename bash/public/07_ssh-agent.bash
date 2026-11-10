#!/usr/bin/env bash

# シェルの起動時にssh-agentを追加するが、複数プロセスが立ち上がらないようにする。
# ref : http://kurokawh.blogspot.com/2012/07/linuxcygwin-ssh-agent.html
# ref : https://himadatanode.hatenablog.com/entry/20160823/p14

# Windows (Git Bash) で 1Password が導入済みなら、1Password の SSH エージェントを標準にする
# 1Password のエージェントは名前付きパイプ上にあり、Windows 標準の OpenSSH だけが接続できる
# Git 同梱の ssh / ssh-add / ssh-agent は使わないため、冒頭の判定より前に処理する
case "$(uname -s)" in
MINGW* | MSYS*)
  _op_ssh_dir="/c/Windows/System32/OpenSSH"
  _op_found=
  if [ -f "${_op_ssh_dir}/ssh.exe" ] && [ -f "${_op_ssh_dir}/ssh-add.exe" ]; then
    for _op_base in "${PROGRAMFILES}" "${PROGRAMW6432}" "${LOCALAPPDATA}"; do
      [ -n "${_op_base}" ] || continue
      if [ -d "$(cygpath -u "${_op_base}")/1Password" ]; then
        _op_found=1
        break
      fi
    done
  fi

  if [ -n "${_op_found}" ]; then
    # MSYS のソケット (Git 同梱 ssh-agent のもの) は Windows 標準の ssh-add を壊すので外す
    # VS Code などが転送したそれ以外のソケットは残す
    case "${SSH_AUTH_SOCK}" in
    /tmp/ssh-* | "${HOME}"/.ssh/agent/*)
      unset SSH_AUTH_SOCK SSH_AGENT_PID
      ;;
    esac

    # core.sshCommand (~/.gitconfig.local) より GIT_SSH_COMMAND が優先される
    export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-C:/Windows/System32/OpenSSH/ssh.exe -o IdentitiesOnly=no}"

    # 子プロセスの bash スクリプトに影響しないよう、関数ではなく対話シェルの alias にする
    case $- in
    *i*)
      for _op_cmd in ssh ssh-add scp sftp ssh-keygen; do
        # shellcheck disable=SC2139
        alias "${_op_cmd}=C:/Windows/System32/OpenSSH/${_op_cmd}.exe"
      done
      ;;
    esac

    unset _op_ssh_dir _op_found _op_base _op_cmd
    return 0
  fi
  unset _op_ssh_dir _op_found _op_base
  ;;
esac

# 既に有効なSSHエージェントがある場合は何もしない（例: VS Code の転送）
if [ -S "${SSH_AUTH_SOCK}" ] && ssh-add -l >/dev/null 2>&1; then
  return 0
fi

# ssh-agent のプロセスを確認する
# ps -ef | grep ssh-agent

SSH_ENV="${HOME}/.ssh/environment"
SSH_AGENT=/usr/bin/ssh-agent
SSH_AGENT_ARGS="-s"
PF_FILE="${HOME}/.ssh/pass_phrase.txt"

start_agent() {
  echo_yellow '新しい SSH Agent をインストールします'
  if ! ${SSH_AGENT} ${SSH_AGENT_ARGS} | sed 's/^echo/#echo/' >"${SSH_ENV}"; then
    echo "Error: Failed to start ssh-agent"
    return 1
  fi
  chmod 600 "${SSH_ENV}"
  # shellcheck source=/dev/null
  . "${SSH_ENV}" >/dev/null

  if [ -f "${PF_FILE}" ]; then
    # パスフレーズのファイルがあるならクリップボードに登録する
    if detect_os | command grep -q "macos"; then
      pbcopy <"${PF_FILE}" # macOSの場合はpbcopyを使用
    else
      clip <"${PF_FILE}" # 他のOSの場合はclipを使用
    fi
  fi

  if ! ssh-add; then
    echo "Error: Failed to add SSH key"
    return 1
  fi
}

# mac では ssh-agent が自動的に立ち上がるので ssh-agent の面倒は見ない
if detect_os | command grep -q "macos"; then
  # 1Password SSH Agent を利用している場合にそのソケットを指定する
  #
  # ※ Mac では ~/.ssh/config の IdentityAgent 設定が ssh コマンドを実行した瞬間にしか効かないため
  #   Dev Container 内で git コマンドを実行した際に 1Password のエージェントに接続できない問題が生じた
  #   そこで VS Code がエージェント転送を行うには、VS Code 自体が起動する時にこのパスを知っている必要がある
  #   そこで SSH_AUTH_SOCK を環境変数として設定することで、Dev Container 内の git コマンドが
  #   1Password のエージェントに接続できるようにした
  sock_path="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
  if [ -S "${sock_path}" ]; then
    export SSH_AUTH_SOCK="${sock_path}"
  fi
elif [ -f "${SSH_ENV}" ]; then
  # Source SSH settings, if applicable
  # shellcheck source=/dev/null
  . "${SSH_ENV}" >/dev/null

  # SSH_AGENT_PID がない場合は start_agentを実行する
  # || の前が true だと後ろは実行されないことを利用している
  # ref : http://okazu.air-nifty.com/blog/2010/04/bash-f628.html

  if [ -z "${SSH_AGENT_PID}" ] || ! ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1; then
    echo -n 'SSH_AGENT_PID が未設定のため、'
    start_agent
  fi

  # SSH_AUTH_SOCKが存在しない場合、新しいエージェントを開始
  if [ ! -S "${SSH_AUTH_SOCK}" ]; then
    echo -n 'SSH_AUTH_SOCK が未設定のため、'
    start_agent
  fi

  # ssh-add -l で登録されている鍵がなければ登録する
  if ! ssh-add -l >/dev/null 2>&1; then
    echo "ssh-add -l で登録されている鍵がなければ登録する"
    if [ -f "${PF_FILE}" ]; then
      cat "${PF_FILE}"
    fi
    ssh-add
  fi
else
  start_agent
fi
