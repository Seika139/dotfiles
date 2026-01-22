#!/usr/bin/env bash
# Netskope の nscacert.pem の場所を自動検出し、Docker Compose/DevContainer が利用する
# 環境ファイル (docker/.env) に NETSKOPE_PEM_PATH を保存する。
set -Eeuo pipefail

ENV_DIR="docker"
ENV_FILES=(
  "$ENV_DIR/.env" # docker compose が自動で読み込む
)

mkdir -p "$ENV_DIR"

# DevContainer でバインドするディレクトリがない場合に備えて作成しておく
if [ -z "${USERPROFILE:-}" ]; then
  HOME_DIR="$HOME"
  echo "Detected HOME directory: $HOME_DIR (for Linux/macOS)"
else
  HOME_DIR="$USERPROFILE"
  echo "Detected USERPROFILE directory: $HOME_DIR (for Windows)"
fi
mkdir -p "$HOME_DIR/.claude/skills" "$HOME_DIR/.claude/commands"

PATH_CANDIDATES=(
  "${NETSKOPE_PEM_PATH:-}"                                          # 明示指定があれば最優先
  "/Library/Application Support/Netskope/STAgent/data/nscacert.pem" # macOS
  "/c/ProgramData/Netskope/STAgent/data/nscacert.pem"               # Windows (PowerShell パス)
  "/mnt/c/ProgramData/Netskope/STAgent/data/nscacert.pem"           # Windows/WSL
  "$HOME/.netskope/nscacert.pem"                                    # 任意配置
  "/etc/ssl/certs/nscacert.pem"                                     # Linux
)

normalize_path() {
  local raw="$1"
  if [ -z "$raw" ]; then
    return
  fi

  # Windows パスを WSL/Linux 形式へ変換
  if command -v wslpath >/dev/null 2>&1; then
    case "$raw" in
    [A-Za-z]:\\*)
      raw="$(wslpath -u "$raw")"
      ;;
    esac
  fi

  # 絶対パス化（存在しない場合はそのまま返す）
  if [ -e "$raw" ] && command -v realpath >/dev/null 2>&1; then
    realpath "$raw"
  else
    printf "%s\n" "$raw"
  fi
}

resolve_certificate() {
  local path
  for path in "${PATH_CANDIDATES[@]}"; do
    # 空要素はスキップ
    if [ -z "$path" ]; then
      continue
    fi
    path="$(normalize_path "$path")"
    if [ -f "$path" ]; then
      printf "%s\n" "$path"
      return 0
    fi
  done
  return 1
}

if CERT_PATH="$(resolve_certificate)"; then
  echo "✔ Netskope CA を検出: $CERT_PATH"
else
  echo "*** WARN: Netskope CA (nscacert.pem) が見つかりません。" \
    "必要であれば docker/.env 内の NETSKOPE_PEM_PATH を手動で更新してください。" >&2
  CERT_PATH="/dev/null"
fi

update_env_file() {
  local file="$1"
  local tmp
  local escaped
  tmp="$(mktemp)"
  # 既存の定義を除外
  grep -v '^NETSKOPE_PEM_PATH=' "$file" 2>/dev/null >"$tmp" || true
  escaped="${CERT_PATH//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"
  printf 'NETSKOPE_PEM_PATH="%s"\n' "$escaped" >>"$tmp"
  mv "$tmp" "$file"
}

for env_file in "${ENV_FILES[@]}"; do
  update_env_file "$env_file"
  echo "-> NETSKOPE_PEM_PATH を ${env_file} に保存しました"
done
