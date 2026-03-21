#!/usr/bin/env bash

# プロンプトの色や表示内容の設定
# .active-profile の値に応じて配色テーマを切り替える

# Windows の GitBash だと __git_ps1 のせいでプロンプトの表示が遅いので軽くする
function light__git_ps1() {
  local branch_name
  branch_name="$(git symbolic-ref --short HEAD 2>/dev/null)"
  if [ -z "$branch_name" ]; then
    # ブランチ名がなければ Git リポジトリ配下ではないと見なし、何も出力せず中断する
    exit 0
  fi
  echo "[$branch_name]" # 省略版と一目で分かるようにブラケットを使用
}

function _bdot_build_ps1() {
  # .active-profile からプロファイル名を読み取る
  local profile_file="${DOTPATH:-$HOME/dotfiles}/.active-profile"
  local profile="default"
  if [[ -f "$profile_file" ]]; then
    local _val
    _val=$(<"$profile_file")
    _val="${_val#"${_val%%[![:space:]]*}"}"
    _val="${_val%"${_val##*[![:space:]]}"}"
    [[ -n "$_val" ]] && profile="$_val"
  fi
  local c_user c_time c_dir c_git

  case "$profile" in
  cg-m2-mac) # グリーン基調
    c_user='\[\e[40;92m\]'
    c_time='\[\e[95m\]'
    c_dir='\[\e[93m\]'
    c_git='\[\e[1;32m\]'
    ;;
  h1-m1-mac) # ブルー/シアン基調
    c_user='\[\e[40;96m\]'
    c_time='\[\e[94m\]'
    c_dir='\[\e[97m\]'
    c_git='\[\e[1;36m\]'
    ;;
  wsl-ubuntu) # オレンジ基調
    c_user='\[\e[40;33m\]'
    c_time='\[\e[38;5;214m\]'
    c_dir='\[\e[38;5;228m\]'
    c_git='\[\e[1;33m\]'
    ;;
  win-15034) # マゼンタ基調
    c_user='\[\e[40;35m\]'
    c_time='\[\e[38;5;213m\]'
    c_dir='\[\e[38;5;225m\]'
    c_git='\[\e[1;35m\]'
    ;;
  *) # default グリーン基調
    c_user='\[\e[40;92m\]'
    c_time='\[\e[95m\]'
    c_dir='\[\e[93m\]'
    c_git='\[\e[1;32m\]'
    ;;
  esac

  local user_part="${c_user}\u@\h"
  local time_part="${c_time}\t"
  local dir_part="${c_dir}\w\[\e[49m\]"
  local git_part=""
  local last_part='\[\e[0m\]\n\$ '

  # shellcheck disable=SC2016
  if is_mingw; then
    git_part="${c_git}"'`light__git_ps1`'
  elif executable __git_ps1; then
    git_part="${c_git}"'`__git_ps1 "(%s)"`'
  fi

  export PS1="${user_part} ${time_part} ${dir_part} ${git_part} ${last_part}"
}

# PROMPT_COMMAND に登録（既存値があれば末尾に追加）
if [[ -z "${PROMPT_COMMAND}" ]]; then
  PROMPT_COMMAND="_bdot_build_ps1"
else
  PROMPT_COMMAND="${PROMPT_COMMAND};_bdot_build_ps1"
fi
