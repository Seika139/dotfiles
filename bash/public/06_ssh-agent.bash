#!/usr/bin/env bash

# シェルの起動時にssh-agentを追加するが、複数プロセスが立ち上がらないようにする。
# ref : http://kurokawh.blogspot.com/2012/07/linuxcygwin-ssh-agent.html
# ref : https://himadatanode.hatenablog.com/entry/20160823/p14

# ssh-agent のプロセスを確認する
# ps -ef | grep ssh-agent

SSH_ENV="${HOME}/.ssh/environment"
SSHAGENT=/usr/bin/ssh-agent
SSHAGENTARGS="-s"

function start_agent {
    echo_yellow '新しい SSH Agent をインストールします'
    ${SSHAGENT} | sed 's/^echo/#echo/' >"${SSH_ENV}"
    chmod 600 "${SSH_ENV}"
    . "${SSH_ENV}" >/dev/null
    ssh-add # 秘密鍵のパスフレーズを入力させる
}

# mac では ssh-agent が自動的に立ち上がるので ssh-agent の面倒は見ない
if is_osx; then
    :
elif [ -f "${SSH_ENV}" ]; then
    # Source SSH settings, if applicable
    . "${SSH_ENV}" >/dev/null

    # SSH_AGENT_PID がない場合は start_agentを実行する
    # || の前が true だと後ろは実行されないことを利用している
    # ref : http://okazu.air-nifty.com/blog/2010/04/bash-f628.html

    if [ -z "${SSH_AGENT_PID}" ] || ! ps -p ${SSH_AGENT_PID} >/dev/null 2>&1; then
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
        ssh-add
    fi
else
    start_agent
fi
