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

# Source SSH settings, if applicable

if [ -f "${SSH_ENV}" ]; then
    . "${SSH_ENV}" >/dev/null

    # SSH_AGENT_PID がない場合は start_agentを実行する
    # || の前が true だと後ろは実行されないことを利用している
    # ref : http://okazu.air-nifty.com/blog/2010/04/bash-f628.html

    #ps ${SSH_AGENT_PID} doesn’t work under cywgin
    ps -ef | grep ${SSH_AGENT_PID} | grep ssh-agent$ >/dev/null || {
        start_agent
    }

    # 登録されている鍵を表示
    echo_yellow "ssh-add -l"
    ssh-add -l

    # ssh-add -l で登録されている鍵がなければ登録する
    # mac の場合は問答無用でスルー
    if ! is_osx && [[ -z $(ssh-add -l) ]]; then
        ssh-add
    fi
else
    start_agent
fi
