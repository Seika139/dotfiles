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
    debug | info | notice | warn | error)
        local label=$1
        shift
        ;;
    *)
        error "Argument Error: unknown LOGLEVEL $1"
        error "Usage: log LOGLEVEL message"
        return 1
        ;;
    esac
    echo "$(now) [${label:u}]: $*"
}

success() {
    echo_green "$(log info "$@")"
}

debug() {
    if [[ ${ENABLE_DEBUG} = 1 ]]; then
        echo_white "$(log debug "$@")"
    fi
}

info() {
    echo_white "$(log info "$@")"
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

    echo "Added to PATH: $dir"
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
