#!/usr/bin/env bash

# 01 : colors
# ref: https://qiita.com/ko1nksm/items/095bdb8f0eca6d327233#256%E8%89%B2

function black() {
    echo -e "\033[00;30m$@\033[0m"
}

function red() {
    echo -e "\033[00;31m$@\033[0m"
}

function green() {
    echo -e "\033[00;32m$@\033[0m"
}

function yellow() {
    echo -e "\033[00;33m$@\033[0m"
}

function blue() {
    echo -e "\033[00;34m$@\033[0m"
}

function magenta() {
    echo -e "\033[00;35m$@\033[0m"
}

function cyan() {
    echo -e "\033[00;36m$@\033[0m"
}

function white() {
    echo -e "\033[01;37m$@\033[0m"
}

function orange() {
    echo -e "\033[38;2;250;180;100m$@\033[0m"
}


# 02 : logging

function now() {
    echo $(date +'%Y/%m/%d %H:%M:%S')
}

function log() {
    if [[ $1 = "" ]]; then
        error "Argument Error: too few argument"
        error "Usage: log LOGLEVEL message"
        return 1
    fi
    case $1 in
        debug|info|notice|warn|error)
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
        msys*) echo "MSYS" ;; # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
        *) error "unknown" && return 1 ;;
    esac
}

function is_osx() {
    [[ $(os) = "OSX" ]]
}

function is_msys() {
    [[ $(os) = "MSYS" ]]
}


# 04 : executable
# コマンドが実行可能なら 0 を、そうでなければ 1 を返す

# >/dev/null 2>&1 → 標準エラー出力を標準出力にマージして /dev/null に捨てる
# https://qiita.com/ritukiii/items/b3d91e97b71ecd41d4ea

function executable() {
    if [[ $1 = "" ]]; then
        error "too few argument"
        return 1
    fi
    type $1>/dev/null 2>&1
}

# 05 : add path
# PATHは先にある方が優先されることに留意する

function add_path() {
    if [[ $1 = "" ]]; then
        error "too few argument"
        return 1
    fi
    export PATH="$1:${PATH}"
}
