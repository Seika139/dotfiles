#!/usr/bin/env bash

# --with-apt オプションで apt update/upgrade も実行する
WITH_APT=false
for arg in "$@"; do
  case "$arg" in
  --with-apt) WITH_APT=true ;;
  esac
done

if "$WITH_APT"; then
  printf "%b%s%b\n" "\\033[38;5;214m" "=== apt update && upgrade (mise 本体含む) ===" "\\033[0m"
  sudo apt update && sudo apt upgrade -y
fi

# mise 管理のツール
printf "%b%s%b\n" "\\033[38;5;214m" "=== mise ===" "\\033[0m"
MISE_UPGRADE_TIMEOUT="${MISE_UPGRADE_TIMEOUT:-300}"
timeout "$MISE_UPGRADE_TIMEOUT" mise upgrade || {
  rc=$?
  if [ "$rc" -eq 124 ]; then
    printf "%s\n" "mise upgrade: ${MISE_UPGRADE_TIMEOUT}秒でタイムアウトしました。"
  else
    printf "%s\n" "mise upgrade: 失敗しました (exit ${rc})。"
  fi
}

# Volta 管理のツール（volta list から動的に取得）
printf "%b%s%b\n" "\\033[38;5;214m" "=== volta ===" "\\033[0m"

# volta install 1 件あたりの最大待ち時間（秒）。
# codex は native バイナリ 233MB のダウンロードがあるため、遅い回線でも完了できる程度に余裕を持たせる。
VOLTA_INSTALL_TIMEOUT="${VOLTA_INSTALL_TIMEOUT:-180}"

# stale な volta.lock を掃除する。
# volta install がハングしたまま死ぬとロックが残り、以降の全 install が
# "Waiting for file lock on Volta directory" で無限待機に陥るため、
# ロックを掴む生きたプロセスが無い場合に限りロックファイルを除去する。
cleanup_stale_volta_lock() {
  local lock="${VOLTA_HOME:-$HOME/.volta}/volta.lock"
  [ -e "$lock" ] || return 0

  # fuser でロックを開いているプロセスがあれば stale ではない。触らない。
  if fuser "$lock" >/dev/null 2>&1; then
    printf "%s\n" "volta.lock は使用中のため触れません（実行中の volta があります）。"
    return 1
  fi

  printf "%s\n" "stale な volta.lock を検出。除去します: $lock"
  rm -f "$lock"
}

if ! command -v volta >/dev/null 2>&1; then
  printf "%s\n" "Volta が見つかりません。インストールしてください: https://volta.sh/"
  exit 1
else
  cleanup_stale_volta_lock

  # while read がサブシェルにならないよう、対象パッケージを配列に集めてから回す。
  # （パイプ内の while だと install の失敗・スキップ状況を呼び出し側で集計できない）
  mapfile -t volta_packages < <(volta list all --format plain | awk '
    /^runtime .* \(default\)/ { name=$2; sub(/@[^@]*$/, "", name); print name }
    /^package-manager /        { name=$2; sub(/@[^@]*$/, "", name); print name }
    /^package .* \(default\)/  { name=$2; sub(/@[^@]*$/, "", name); print name }
  ' | sort -u)

  volta_failed=()
  for pkg in "${volta_packages[@]}"; do
    printf "%s\n" "volta install ${pkg}@latest"
    # 各 install を timeout で囲み、ハングしても次へ進む。
    # timeout は 124（タイムアウト）/その他（install 失敗）を区別できる。
    # 注: `if ! cmd; then rc=$?` だと $? が `!` 反転後の値になりタイムアウトを
    # 取り違えるため、コマンドを実行してから直後に exit code を捕捉する。
    rc=0
    timeout "$VOLTA_INSTALL_TIMEOUT" volta install "${pkg}@latest" || rc=$?
    if [ "$rc" -ne 0 ]; then
      if [ "$rc" -eq 124 ]; then
        printf "%s\n" "  -> ${pkg}: ${VOLTA_INSTALL_TIMEOUT}秒でタイムアウト。中断して次へ進みます。"
        # ハングした install がロックを掴んだまま死んだ場合に備えて掃除する。
        cleanup_stale_volta_lock
      else
        printf "%s\n" "  -> ${pkg}: install に失敗しました (exit ${rc})。"
      fi
      volta_failed+=("$pkg")
    fi
  done

  if [ "${#volta_failed[@]}" -gt 0 ]; then
    printf "%s\n" "volta: 次のパッケージで問題が発生しました: ${volta_failed[*]}"
    printf "%s\n" "  手動で再実行してください: volta install <pkg>@latest"
  fi
fi

# uv 本体（pipx 経由でインストール）
printf "%b%s%b\n" "\\033[38;5;214m" "=== uv ===" "\\033[0m"
PIPX_UPGRADE_TIMEOUT="${PIPX_UPGRADE_TIMEOUT:-180}"
timeout "$PIPX_UPGRADE_TIMEOUT" pipx upgrade uv || {
  rc=$?
  if [ "$rc" -eq 124 ]; then
    printf "%s\n" "pipx upgrade uv: ${PIPX_UPGRADE_TIMEOUT}秒でタイムアウトしました。"
  else
    printf "%s\n" "pipx upgrade uv: 失敗しました (exit ${rc})。"
  fi
}

if ! "$WITH_APT"; then
  printf "\n%b%s%b\n" "\\033[38;5;214m" "=== apt ===" "\\033[0m"
  printf "%b%s%b%s\n" "\\033[33m" "⚠  apt のアップデートはスキップしました（mise 本体含む）。" "\\033[0m" "実行する場合:"
  printf "%b%s%b\n" "\\033[36m" "  sudo apt update && sudo apt upgrade -y" "\\033[0m"
fi
