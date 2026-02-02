#!/usr/bin/env bash

# OS 判定系ユーティリティ
# ref : https://www.trhrkmk.com/posts/bashrc-os-check/

detect_os() {
  # まずOSTYPEを試す（高速）
  if [[ -n "${OSTYPE}" ]]; then
    case "${OSTYPE}" in
    darwin*) echo "macos" ;;
    linux*) echo "linux" ;;
    cygwin*) echo "cygwin" ;;
    msys*) echo "mingw" ;;
    *) echo "unknown" ;;
    esac
  else
    # フォールバックでuname使用
    case "$(uname -s)" in
    Darwin*) echo "macos" ;;
    Linux*) echo "linux" ;;
    # 以下省略
    esac
  fi
}

is_win() {
  [[ $(detect_os) =~ ^(cygwin|mingw)$ ]]
}

is_mingw() {
  [[ $(detect_os) = "mingw" ]]
}

# Windows の Git Bash でシンボリックリンクを作成できるようにしておく
# ref : https://blog.logicky.com/2017/06/07/windows10-git-bash%E3%81%A7%E3%82%B7%E3%83%B3%E3%83%9C%E3%83%AA%E3%83%83%E3%82%AF%E3%83%AA%E3%83%B3%E3%82%AF%E3%82%92%E3%81%A4%E3%81%8F%E3%82%8C%E3%82%8B%E3%82%88%E3%81%86%E3%81%AB%E3%81%99%E3%82%8B/
# ref : https://qiita.com/ucho/items/c5ea0beb8acf2f1e4772#%E7%92%B0%E5%A2%83%E5%A4%89%E6%95%B0msys%E3%81%ABwinsymlinksnativestrict%E3%82%92%E8%A8%AD%E5%AE%9A%E3%81%99%E3%82%8B
if is_win; then
  export MSYS=winsymlinks:nativestrict
fi

#########################
# WSL 判定系ユーティリティ #
#########################

is_wsl() {
  [[ -n "$WSL_DISTRO_NAME" ]] ||
    ([[ $(detect_os) = "linux" ]] && grep -qEi "(Microsoft|WSL)" /proc/version 2>/dev/null)
}

detect_wsl() {
  local wsl_version=""

  # WSL環境変数をチェック（最も確実で高速）
  if [[ -n "$WSL_DISTRO_NAME" ]]; then
    if [[ -n "$WSL_INTEROP" ]]; then
      wsl_version="wsl2"
    else
      wsl_version="wsl1"
    fi
  # フォールバック検出
  elif [[ -f /proc/version ]] && grep -qi "microsoft\|wsl" /proc/version 2>/dev/null; then
    if grep -qi "wsl2" /proc/version 2>/dev/null; then
      wsl_version="wsl2"
    elif [[ -d /run/WSL ]]; then
      wsl_version="wsl2"
    else
      wsl_version="wsl1"
    fi
  fi
  echo "$wsl_version"
}

# WSL情報の取得
get_wsl_info() {
  if is_wsl; then
    echo "Distro: ${WSL_DISTRO_NAME:-unknown}"
    echo "Version: $(detect_wsl)"
  else
    echo "Not running in WSL"
    return 1
  fi
}
