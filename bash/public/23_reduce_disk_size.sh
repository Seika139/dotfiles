#!/usr/bin/env bash

prune_mise() {
  local before after
  local root

  root=$(mise where 2>/dev/null | head -1)

  # macOS / Windows Git Bash 共通
  if [[ -z "$root" ]]; then
    root="$HOME"
  fi

  before=$(df -Pk "$root" | awk 'NR==2 {print $4}')
  mise prune --yes --tools || return 1
  after=$(df -Pk "$root" | awk 'NR==2 {print $4}')

  awk -v before="$before" -v after="$after" '
    BEGIN {
      printf "mise prune によるディスク空き容量の増加: %+.2f MiB\n",
        (after - before) / 1024
    }'
}

# fzf で選んだ git worktree と対応するブランチを削除する (メインの worktree は対象外)
# 使い方: gwr [-f|--force]
#   既定: y/N で確認し、worktree は変更があれば拒否、ブランチは `branch -d` (未マージなら拒否)
#   -f  : 確認を省略し、`worktree remove --force` と `branch -D` で削除する
gwr() {
  local force=0 main_worktree selected path branch answer status=0

  case "${1:-}" in
  -f | --force) force=1 ;;
  "") ;;
  *)
    echo "Usage: gwr [-f|--force]" >&2
    return 2
    ;;
  esac

  fzf_available || return 1
  main_worktree=$(git rev-parse --path-format=absolute --git-common-dir | sed 's|/\.git$||') || return 1

  # 出力: "<path>\t<branch or (detached)>"。先頭 (メイン) の worktree は除外する
  selected=$(
    git worktree list --porcelain |
      awk -v main="${main_worktree}" '
        function flush() { if (path != "" && path != main) printf "%s\t%s\n", path, (branch == "" ? "(detached)" : branch) }
        /^worktree / { flush(); path = substr($0, 10); branch = "" }
        /^branch refs\/heads\// { branch = substr($0, 19) }
        END { flush() }
      ' |
      fzf --multi --delimiter=$'\t' --header='削除する worktree を選択 (Tab で複数選択)'
  ) || return 0
  [[ -n "${selected}" ]] || return 0

  # 通常は -d / 無オプション、-f のときは最初から -D / --force
  local branch_opt=-d wt_opt=
  [[ "${force}" -eq 1 ]] && branch_opt=-D wt_opt=--force

  # ループの stdin を here-string に取られると確認の read が選択結果を読んでしまうため fd 3 で回す
  while IFS=$'\t' read -r -u 3 path branch; do
    if [[ "${force}" -eq 0 ]]; then
      read -r -p "worktree '${path}' とブランチ '${branch}' を削除しますか? [y/N] " answer
      [[ "${answer}" =~ ^[yY]$ ]] || {
        echo "Skipped: ${path}"
        continue
      }
    fi

    # 通常削除に失敗したら、確認のうえ強制削除で 1 回だけやり直す
    echo_yellow "git -C ${main_worktree} worktree remove ${wt_opt:+${wt_opt} }${path}"
    if ! git -C "${main_worktree}" worktree remove ${wt_opt} "${path}"; then
      [[ "${force}" -eq 0 ]] && read -r -p "強制削除しますか? [y/N] " answer
      if [[ "${force}" -eq 1 || ! "${answer}" =~ ^[yY]$ ]]; then
        status=1
        continue
      fi
      echo_yellow "git -C ${main_worktree} worktree remove --force ${path}"
      git -C "${main_worktree}" worktree remove --force "${path}" || {
        status=1
        continue
      }
    fi

    [[ "${branch}" == "(detached)" ]] && continue
    echo_yellow "git -C ${main_worktree} branch ${branch_opt} ${branch}"
    if ! git -C "${main_worktree}" branch "${branch_opt}" "${branch}"; then
      [[ "${force}" -eq 0 ]] && read -r -p "ブランチを強制削除 (-D) しますか? [y/N] " answer
      if [[ "${force}" -eq 1 || ! "${answer}" =~ ^[yY]$ ]]; then
        status=1
        continue
      fi
      echo_yellow "git -C ${main_worktree} branch -D ${branch}"
      git -C "${main_worktree}" branch -D "${branch}" || status=1
    fi
  done 3<<<"${selected}"

  return "${status}"
}
