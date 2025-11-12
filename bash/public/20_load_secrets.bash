#!/usr/bin/env bash

# 機密情報は git 管理下に置かないファイルから読み込む。
# 既定のパスは bash/envs/00_secrets.bash (SECRETS_FILE で上書き可)。

SECRETS_FILE="${SECRETS_FILE:-${BDOTDIR:-$HOME/dotfiles/bash}/envs/00_secrets.bash}"
if [[ -f "$SECRETS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$SECRETS_FILE"
elif [[ "${BDOTDIR_SHELL_IS_INTERACTIVE:-0}" == "1" ]]; then
    printf '🚨 \033[31m[Secrets Warning] \033[36m %s \033[31mが見つかりません。必要な機密情報を記載してください。\033[0m\n' "$SECRETS_FILE"
fi

# 必要な環境変数が設定されているか確認する関数
check_required_env_vars() {
    local missing_vars=()
    for var in "$@"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if (( ${#missing_vars[@]} > 0 )); then
        printf "🚨 \033[31m[Secrets Error] 以下の環境変数が設定されていません。\033[36m $SECRETS_FILE \033[31mを確認してください\033[0m\n %s\n" "${missing_vars[*]}" >&2
        return 1
    fi
    return 0
}

# 機密情報を含む環境変数の名前だけをここに列挙し、読み込まれたことを確認する
REQUIRED_SECRETS_VARS=(
    "OPENAI_API_KEY"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
)

if [[ "${BDOTDIR_SHELL_IS_INTERACTIVE:-0}" == "1" ]] && (( ${#REQUIRED_SECRETS_VARS[@]} > 0 )); then
    check_required_env_vars "${REQUIRED_SECRETS_VARS[@]}"
fi

unset REQUIRED_SECRETS_VARS
unset SECRETS_FILE
