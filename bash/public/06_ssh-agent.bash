#!/usr/bin/env bash

# OSX では ssh-add のときに
eval "$(ssh-agent)" # ssh-agent を起動
ssh-add             # 秘密会議のパスフレーズを入力させる

# ssh-agent のプロセスを確認する
# ps -ef | grep ssh-agent
