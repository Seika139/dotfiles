#!/bin/bash

# このスクリプトは Git の user.name と user.email の設定を確認し、
# 未設定の場合はリポジトリローカル（このプロジェクトのみ）に設定します。
# devcontainer 環境では再構築時にグローバル設定が失われるため、
# このプロジェクト固有の設定のみを行います。
#
# 環境変数 GIT_USER_NAME と GIT_USER_EMAIL が設定されている場合は、
# それらを自動的に使用します（非対話モード）。

# ==================== ユーティリティ関数 ====================

# 色付きの出力用関数
print_color() {
  local color=$1
  local text=$2

  case $color in
  "red") echo -e "\e[31m$text\e[0m" ;;
  "green") echo -e "\e[32m$text\e[0m" ;;
  "yellow") echo -e "\e[33m$text\e[0m" ;;
  "blue") echo -e "\e[34m$text\e[0m" ;;
  "cyan") echo -e "\e[36m$text\e[0m" ;;
  *) echo "$text" ;;
  esac
}

# ==================== Git 設定処理の共通関数 ====================

# 設定状況を表示する関数
show_config_summary() {
  local local_name=$1
  local local_email=$2
  local local_signingkey=$3
  local global_name=$4
  local global_email=$5
  local global_signingkey=$6

  echo "----------------------------------------"
  print_color "blue" "現在の Git 設定状況:"
  echo ""
  echo "● ローカル設定（このリポジトリ）:"
  echo "  ユーザー名: ${local_name:-'(未設定)'}"
  echo "  メールアドレス: ${local_email:-'(未設定)'}"
  echo "  署名キー: ${local_signingkey:-'(未設定)'}"
  echo ""

  # グローバル設定が存在する場合は表示
  if [ -n "$global_name" ] || [ -n "$global_email" ] || [ -n "$global_signingkey" ]; then
    echo "● グローバル設定:"
    echo "  ユーザー名: ${global_name:-'(未設定)'}"
    echo "  メールアドレス: ${global_email:-'(未設定)'}"
    echo "  署名キー: ${global_signingkey:-'(未設定)'}"
    echo ""
  fi

  # 環境変数が設定されている場合は表示
  if [ -n "${GIT_USER_NAME:-}" ] || [ -n "${GIT_USER_EMAIL:-}" ] || [ -n "${GIT_USER_SIGNINGKEY:-}" ]; then
    echo "● 環境変数:"
    echo "  GIT_USER_NAME: ${GIT_USER_NAME:-'(未設定)'}"
    echo "  GIT_USER_EMAIL: ${GIT_USER_EMAIL:-'(未設定)'}"
    echo "  GIT_USER_SIGNINGKEY: ${GIT_USER_SIGNINGKEY:-'(未設定)'}"
    echo ""
  fi

  echo "----------------------------------------"

  # 設定完了・未完了の判定とメッセージ
  if [ -n "$local_name" ] && [ -n "$local_email" ]; then
    print_color "green" "✅ このリポジトリの Git 設定が完了しました。"
  else
    print_color "yellow" "⚠️  このリポジトリの Git 設定が不完全です。"
    print_color "yellow" "    コミットする前に以下のコマンドで設定してください:"
    [ -z "$local_name" ] && echo "    git config user.name \"Your Name\""
    [ -z "$local_email" ] && echo "    git config user.email \"your.email@example.com\""
  fi
}

# Git 設定を対話的に設定する共通関数
# 引数:
#   $1: config_key (例: "user.name")
#   $2: display_name (例: "ユーザー名")
#   $3: env_var_name (例: "GIT_USER_NAME")
#   $4: local_value (ローカル設定の現在値)
#   $5: global_value (グローバル設定の現在値)
#   $6: is_optional (オプション項目かどうか: "true" or "false")
configure_git_setting() {
  local config_key=$1
  local display_name=$2
  local env_var_name=$3
  local local_value=$4
  local global_value=$5
  local is_optional=${6:-false}

  # 既に設定されている場合はスキップ
  if [ -n "$local_value" ]; then
    print_color "green" "✅ Git ${display_name}: $local_value"
    return 0
  fi

  print_color "yellow" "Git ${display_name}が設定されていません。"

  # 環境変数から自動設定を試みる
  local env_value="${!env_var_name}"
  if [ -n "$env_value" ]; then
    git config "$config_key" "$env_value"
    print_color "green" "✅ Git ${display_name}を環境変数から自動設定しました: $env_value"
    return 0
  fi

  # グローバル設定がある場合はそれを提案
  if [ -n "$global_value" ]; then
    print_color "cyan" "グローバル設定に「$global_value」が見つかりました。"
    echo -n "この${display_name}を使用しますか？ [Y/n]: "
    read -r use_global

    if [ -z "$use_global" ] || [ "$use_global" = "Y" ] || [ "$use_global" = "y" ]; then
      git config "$config_key" "$global_value"
      print_color "green" "✅ このリポジトリの Git ${display_name}を「$global_value」に設定しました。"
      return 0
    fi
  fi

  # オプション項目の場合はスキップを許可
  if [ "$is_optional" = "true" ]; then
    echo "Git の${display_name}の設定をスキップしました。"
    return 0
  fi

  # 手動入力を促す
  echo -n "Git ${display_name}を入力してください: "
  read -r input_value

  if [ -n "$input_value" ]; then
    git config "$config_key" "$input_value"
    print_color "green" "✅ このリポジトリの Git ${display_name}を「$input_value」に設定しました。"
  else
    print_color "red" "Git ${display_name}の設定をスキップしました。"
  fi
}

# ==================== メイン処理 ====================

echo "Gitの設定を確認しています..."

# 現在の設定を取得（ローカル → グローバルの順で確認）
LOCAL_USER_NAME=$(git config --get user.name)
LOCAL_USER_EMAIL=$(git config --get user.email)
LOCAL_USER_SIGNINGKEY=$(git config --get user.signingkey)

# グローバル設定も確認（デフォルト値として使用）
GLOBAL_USER_NAME=$(git config --global --get user.name 2>/dev/null || true)
GLOBAL_USER_EMAIL=$(git config --global --get user.email 2>/dev/null || true)
GLOBAL_USER_SIGNINGKEY=$(git config --global --get user.signingkey 2>/dev/null || true)

# 早期リターン: 既に全て設定されている場合
if [ -n "$LOCAL_USER_NAME" ] && [ -n "$LOCAL_USER_EMAIL" ]; then
  print_color "green" "Git ユーザー名とメールアドレスは既に設定されています。"
  echo "----------------------------------------"
  echo "ユーザー名: $LOCAL_USER_NAME"
  echo "メールアドレス: $LOCAL_USER_EMAIL"
  echo "署名キー: ${LOCAL_USER_SIGNINGKEY:-'(未設定)'}"
  echo "----------------------------------------"
  exit 0
fi

# 各設定項目を処理（共通関数を使用）
configure_git_setting "user.name" "ユーザー名" "GIT_USER_NAME" "$LOCAL_USER_NAME" "$GLOBAL_USER_NAME" "false"
configure_git_setting "user.email" "メールアドレス" "GIT_USER_EMAIL" "$LOCAL_USER_EMAIL" "$GLOBAL_USER_EMAIL" "false"
configure_git_setting "user.signingkey" "署名キー" "GIT_USER_SIGNINGKEY" "$LOCAL_USER_SIGNINGKEY" "$GLOBAL_USER_SIGNINGKEY" "true"

# ==================== 設定状況の表示 ====================

# 設定後の状態を再取得
LOCAL_NAME=$(git config --get user.name)
LOCAL_EMAIL=$(git config --get user.email)
LOCAL_SIGNINGKEY=$(git config --get user.signingkey)

# 設定サマリーを表示
show_config_summary "$LOCAL_NAME" "$LOCAL_EMAIL" "$LOCAL_SIGNINGKEY" \
  "$GLOBAL_USER_NAME" "$GLOBAL_USER_EMAIL" "$GLOBAL_USER_SIGNINGKEY"
