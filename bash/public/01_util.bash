#!/usr/bin/env bash

# 01 : colors
# ref: https://qiita.com/ko1nksm/items/095bdb8f0eca6d327233#256%E8%89%B2

function black() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;30m$@\033[0m"
    else
        echo -e "\033[00;30m$@\033[0m"
    fi
}

function red() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;31m$@\033[0m"
    else
        echo -e "\033[00;31m$@\033[0m"
    fi
}

function green() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;32m$@\033[0m"
    else
        echo -e "\033[00;32m$@\033[0m"
    fi
}

function yellow() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;33m$@\033[0m"
    else
        echo -e "\033[00;33m$@\033[0m"
    fi
}

function blue() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;34m$@\033[0m"
    else
        echo -e "\033[00;34m$@\033[0m"
    fi
}

function magenta() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;35m$@\033[0m"
    else
        echo -e "\033[00;35m$@\033[0m"
    fi
}

function cyan() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;36m$@\033[0m"
    else
        echo -e "\033[00;36m$@\033[0m"
    fi
}

function white() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[00;37m$@\033[0m"
    else
        echo -e "\033[01;37m$@\033[0m"
    fi
}

function orange() {
    if [[ $1 = '-n' ]]; then
        shift
        echo -ne "\033[38;2;250;180;100m$@\033[0m"
    else
        echo -e "\033[38;2;250;180;100m$@\033[0m"
    fi
}

# 02 : logging

function now() {
    echo $(date +'%Y/%m/%d %H:%M:%S')
}

function log() {
    if [[ $1 = "" ]]; then
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
    echo "$(now) [${label:u}]: $@"
}

function success() {
    green $(log info $@)
}

function debug() {
    if [[ ${ENABLE_DEBUG} = 1 ]]; then
        white $(log debug $@)
    fi
}

function info() {
    white $(log info $@)
}

function notice() {
    yellow $(log notice $@)
}

function warn() {
    orange $(log warn $@)
}

function error() {
    red $(log error $@) 1>&2
}

# 03 : OS distinction
# ref : https://www.trhrkmk.com/posts/bashrc-os-check/

function os() {
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

function is_osx() {
    [[ $(os) = "OSX" ]]
}

function is_msys() {
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

function executable() {
    if [[ $1 = "" ]]; then
        error "too few arguments"
        return 1
    fi
    type $1 >/dev/null 2>&1
}

# 05 : add path
# PATHは先にある方が優先されることに留意する

function add_path() {
    if [[ $1 = "" ]]; then
        error "too few arguments"
        return 1
    fi
    export PATH="$1:${PATH}"
}

# 06 : absolute_path
# 任意のファイルの絶対パスを取得する
# ref : https://maku77.github.io/linux/path/absolute-path-of-file.html

function abs_path() {
    if [[ $1 = "" ]]; then
        error "too few arguments"
        return 1
    elif [[ ! -e $1 ]]; then
        warn "abs_path: $1 : No such file or directory"
    fi
    echo $(
        cd $(dirname $1)
        pwd
    )/$(basename $1)
}
