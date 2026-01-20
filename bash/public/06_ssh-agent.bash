#!/usr/bin/env bash

# シェルの起動時にssh-agentを追加するが、複数プロセスが立ち上がらないようにする。
# ref : http://kurokawh.blogspot.com/2012/07/linuxcygwin-ssh-agent.html
# ref : https://himadatanode.hatenablog.com/entry/20160823/p14

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
    if is_osx; then
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
if is_osx; then
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
