#!/usr/bin/env bash

selected_option="$1"

if [ -z "${selected_option}" ]; then
  selected_option=$(
    printf "show-all\nshow-deletable\nprune\n" |
      fzf --height 7 --border --prompt "選択: " \
        --preview '
        case {} in
          show-all) printf "全コンテナを表示します\n" ;;
          show-deletable) printf "削除可能なコンテナを表示します\n" ;;
          prune) printf "停止中のコンテナを削除します\n" ;;
        esac
      ' --preview-window=right,50%
  )
fi

case $selected_option in
show-all)
  printf "show-all: 全コンテナを表示します\n"
  printf "\\033[36m$ docker ps -a\\033[0m\n"
  docker ps -a
  ;;
show-deletable)
  printf "show-deletable: 削除可能なコンテナを表示します\n\n"
  printf "\\033[36m$ docker ps -a -f status=exited\\033[0m # 停止中のコンテナ\n"
  docker ps -a -f status=exited
  printf "\n\\033[36m$ docker ps -a -f status=dead\\033[0m # 異常終了したコンテナ\n"
  docker ps -a -f status=dead
  ;;
prune)
  printf "prune: 停止中のコンテナを削除します\n"
  printf "\\033[36m$ docker container prune --force\\033[0m\n"
  docker container prune --force
  ;;
*)
  printf "%s\n" "無効なオプションです: $selected_option"
  exit 1
  ;;
esac
