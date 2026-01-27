#!/usr/bin/env bash

# 01 : colors
# ref: https://qiita.com/ko1nksm/items/095bdb8f0eca6d327233#256%E8%89%B2

# python のリンター black との競合を回避
echo_black() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;30m$*\033[0m"
  else
    echo -e "\033[00;30m$*\033[0m"
  fi
}

echo_red() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;31m$*\033[0m"
  else
    echo -e "\033[00;31m$*\033[0m"
  fi
}

echo_green() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;32m$*\033[0m"
  else
    echo -e "\033[00;32m$*\033[0m"
  fi
}

echo_yellow() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;33m$*\033[0m"
  else
    echo -e "\033[00;33m$*\033[0m"
  fi
}

echo_blue() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;34m$*\033[0m"
  else
    echo -e "\033[00;34m$*\033[0m"
  fi
}

echo_magenta() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;35m$*\033[0m"
  else
    echo -e "\033[00;35m$*\033[0m"
  fi
}

echo_cyan() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[00;36m$*\033[0m"
  else
    echo -e "\033[00;36m$*\033[0m"
  fi
}

echo_white() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[01;37m$*\033[0m"
  else
    echo -e "\033[01;37m$*\033[0m"
  fi
}

echo_orange() {
  if [[ $1 = '-n' ]]; then
    shift
    echo -ne "\033[38;2;250;180;100m$*\033[0m"
  else
    echo -e "\033[38;2;250;180;100m$*\033[0m"
  fi
}

echo_rgb() {
  local no_newline=false # -n オプションをつけるか否か
  if [[ $1 = '-n' ]]; then
    no_newline=true
    shift
  fi

  local red=255
  local green=255
  local blue=255
  local text=""
  for color in red green blue; do
    if is_integer "$1"; then
      eval "${color}=$1"
      shift
    fi
  done
  text="$*"

  if "${no_newline}"; then
    echo -ne "\033[38;2;${red};${green};${blue}m${text}\033[0m"
  else
    echo -e "\033[38;2;${red};${green};${blue}m${text}\033[0m"
  fi
}

is_integer() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

# 02 : logging

now() {
  date +'%Y-%m-%d_%H:%M:%S'
}

log() {
  if [[ $# -lt 1 ]]; then
    error "Argument Error: too few arguments"
    error "Usage: log LOGLEVEL message"
    return 1
  fi
  case $1 in
  verbose | debug | success | info | notice | warn | error)
    local label=$1
    shift
    ;;
  *)
    error "Argument Error: unknown LOGLEVEL $1"
    error "Usage: log LOGLEVEL message"
    return 1
    ;;
  esac
  local filler="*******" # 固定したい文字数分用意

  # ラベルとドットを結合し、先頭から7文字分だけ切り出す
  local final_label="${filler}${label}"
  final_label="${final_label: -7}"

  echo "$(now) [${final_label}]: $*"
}

# RFC 5424 を参考にしてログレベルを定める
# RFC 5424 は 0~ 7 まで
# GCP や Android では別のログレベルが設定されている
#
# 0: Emergency     - OS, カーネルが使用不可(ここでは利用しない)
# 1: Alert         - DBの破損など直ちに対処が必要(ここでは利用しない)
# 2: Critical      - HDDなど損傷など危険な状態(ここでは利用しない)
# 3: Error         - 一般的なエラー
# 4: Warning       - リソース逼迫や設定の不備などの警告（動作はする）
# 5: Notice        - 注意が必要な正常状態（設定変更、重要なサービスの再起動など）
# 6: Informational - ユーザーのログイン、処理完了の記録などの情報
# 7: Debug         - 開発用の詳細なトレースログ
# 8: Verbose       - 最も詳細

verbose() {
  echo_rgb 110 110 110 "$(log verbose "$@")"
}

debug() {
  echo_rgb 160 190 255 "$(log debug "$@")"
}

success() {
  echo_green "$(log success "$@")"
}

info() {
  echo_rgb 160 255 190 "$(log info "$@")"
}

notice() {
  echo_yellow "$(log notice "$@")"
}

warn() {
  echo_orange "$(log warn "$@")"
}

error() {
  echo_red "$(log error "$@")" 1>&2
}

# error 0
# warn 1
# notice 2
# info 3
# success 4
# debug 5
# verbose 6

# 03 : OS distinction
# ref : https://www.trhrkmk.com/posts/bashrc-os-check/

os() {
  case ${OSTYPE} in
  solaris*) echo "SOLARIS" ;;
  darwin*) echo "OSX" ;;
  linux*) echo "LINUX" ;;
  bsd*) echo "BSD" ;;
  cygwin*) echo "CYGWIN" ;; # POSIX compatibility layer and Linux environment emulation for Windows
  msys*) echo "MSYS" ;;     # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
  *) error "unknown" && return 1 ;;
  esac
}

is_osx() {
  [[ $(os) = "OSX" ]]
}

is_win() {
  [[ $(os) =~ ^(MSYS|CYGWIN|winnt)$ ]]
}

is_wsl() {
  if is_linux; then
    if grep -qEi "(Microsoft|WSL)" /proc/version &>/dev/null; then
      return 0
    else
      return 1
    fi
  else
    return 1
  fi
}

is_msys() {
  [[ $(os) = "MSYS" ]]
}

# Windows の Git Bash でシンボリックリンクを作成できるようにしておく
# ref : https://blog.logicky.com/2017/06/07/windows10-git-bash%E3%81%A7%E3%82%B7%E3%83%B3%E3%83%9C%E3%83%AA%E3%83%83%E3%82%AF%E3%83%AA%E3%83%B3%E3%82%AF%E3%82%92%E3%81%A4%E3%81%8F%E3%82%8C%E3%82%8B%E3%82%88%E3%81%86%E3%81%AB%E3%81%99%E3%82%8B/
# ref : https://qiita.com/ucho/items/c5ea0beb8acf2f1e4772#%E7%92%B0%E5%A2%83%E5%A4%89%E6%95%B0msys%E3%81%ABwinsymlinksnativestrict%E3%82%92%E8%A8%AD%E5%AE%9A%E3%81%99%E3%82%8B
if is_msys; then
  export MSYS=winsymlinks:nativestrict
fi

# 04 : executable
# コマンドが実行可能なら 0 を、そうでなければ 1 を返す

# >/dev/null 2>&1 → 標準エラー出力を標準出力にマージして /dev/null に捨てる
# https://qiita.com/ritukiii/items/b3d91e97b71ecd41d4ea

executable() {
  if [[ $# -ne 1 ]]; then
    error "executable : requires only 1 argument"
    return 1
  fi
  type "$1" >/dev/null 2>&1
}

# 05 : add path
# PATHは先にある方が優先されることに留意する

add_path() {
  if [[ $# -ne 1 ]]; then
    error "add_path : requires only 1 argument" >&2
    return 1
  fi

  # 引数をエスケープ解除
  local dir
  dir=$(echo -e "$1" | sed 's/\\//g')

  if [[ ! -d "$dir" ]]; then
    error "add_path : $dir is not a valid directory" >&2
    return 1
  fi

  case ":$PATH:" in
  *":$1:"*) ;;
  *) export PATH="$1:${PATH}" ;;
  esac

  [[ "${BDOTDIR_SHELL_IS_INTERACTIVE}" == "1" ]] && echo "Added to PATH: $dir"
}

# 06 : absolute_path
# 任意のファイルの絶対パスを取得する
# ref : https://maku77.github.io/linux/path/absolute-path-of-file.html

abs_path() {
  if [[ $# -ne 1 ]]; then
    error "abs_path : requires only 1 argument"
    return 1
  fi
  echo "$(
    cd "$(dirname "$1")" || exit 1
    pwd
  )"/"$(basename "$1")"
}
