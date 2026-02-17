#!/usr/bin/env bash

# 補完設定: dockerの補完を設定
alias d='docker'
alias dc='docker compose'
if command -v docker &>/dev/null; then
  # 一時ファイルに補完スクリプトを保存して読み込む
  # NOTE: WSL環境ではDocker Desktop未起動時にdockerスタブが警告をstdoutに出力し
  #       exit code 1 を返すため、終了コードで成否を判定する
  _docker_completion_tmp="/tmp/docker_completion_$$"
  if docker completion bash >"$_docker_completion_tmp" 2>/dev/null; then
    # shellcheck source=/dev/null
    source "$_docker_completion_tmp"
    complete -F __start_docker d dc
  fi
  rm -f "$_docker_completion_tmp"
fi

dps() {
  # docker ps の出力を整形して表示する
  if [[ "$1" = "-t" ]]; then
    (echo "NAME|IMAGE|COMPOSE_FILE|SERVICE" && docker ps --format '{{.Names}}|{{.Image}}|{{.Label "com.docker.compose.project.config_files"}}|{{.Label "com.docker.compose.service"}}') | column -t -s '|'
  else
    docker ps -q | xargs docker inspect | jq -r '.[] | {
      name:         .Name[1:],
      image:        .Config.Image,
      compose_file: (.Config.Labels["com.docker.compose.project.config_files"] // "-"),
      service:      (.Config.Labels["com.docker.compose.service"] // "-")
    }'
  fi
}
