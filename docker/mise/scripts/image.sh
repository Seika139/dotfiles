#!/usr/bin/env bash

selected_option="$1"

if [ -z "${selected_option}" ]; then
  selected_option=$(
    printf "show-all\nshow-deletable\nprune\nprune-all\n" | fzf --height 8 --border --prompt "選択: " \
      --preview '
        case {} in
          show-all) printf "全イメージを表示します\n" ;;
          show-deletable) printf "削除可能なイメージを表示します\n" ;;
          prune) printf "タグづけされてないイメージ(dangling image)を削除します\n" ;;
          prune-all) printf "停止中のコンテナを含む全てのコンテナから参照されていないイメージを削除します\n" ;;
        esac
      ' --preview-window=right,50%
  )
fi

case $selected_option in
show-all)
  printf "show-all: 全イメージを表示します\n"
  printf "\033[36m$ docker image ls\033[0m\n"
  docker image ls
  ;;
show-deletable)
  printf "show-deletable: タグづけされてないイメージ(dangling image)を表示します\n\n"
  printf "\033[36m$ docker images -f dangling=true\033[0m\n"
  docker images -f dangling=true
  printf "\n"
  USED_IDS_FILE="$(mktemp)"
  docker ps -aq | xargs -r docker inspect -f '{{.Image}}' | sort -u >"$USED_IDS_FILE"
  printf "\033[36m未使用（docker image prune -a の削除対象）イメージ一覧\033[0m\n"

  docker images --no-trunc \
    --format '{{.ID}}\\t{{.Repository}}:{{.Tag}}\\t{{.CreatedSince}}\\t{{.Size}}' |
    awk -F '\\t' -v f="$USED_IDS_FILE" '
      BEGIN {
        while ((getline line < f) > 0) used[line]=1; close(f);
        print "IMAGE ID\tREPOSITORY:TAG\tCREATED\tSIZE"
        print "--------\t--------------\t-------\t----"
      }
      {
        id=$1;
        if (!(id in used)) printf "%s\\t%s\\t%s\\t%s\\n", $1,$2,$3,$4;
      }
    ' | column -t -s $'\t'
  rm -f "$USED_IDS_FILE"
  ;;
prune)
  printf "prune: タグづけされてないイメージ(dangling image)を削除します\n"
  printf "\033[36m$ docker image prune --force\033[0m\n"
  docker image prune --force
  ;;
prune-all)
  printf "prune-all: 停止中のコンテナを含む全てのコンテナから参照されていないイメージを削除します\n"
  printf "\033[36m$ docker image prune --all --force\033[0m\n"
  docker image prune --all --force
  ;;
*)
  printf "%s\n" "無効なオプションです: $selected_option"
  exit 1
  ;;
esac
