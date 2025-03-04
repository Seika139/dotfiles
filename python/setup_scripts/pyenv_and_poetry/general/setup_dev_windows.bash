#!/bin/bash

# エラーが発生したら即座に終了する
set -e

# ログ関数を定義する
log_info() {
    echo -e "\033[00;33m[INFO]\033[0m $*"
}

log_error() {
    echo -e "\033[00;31m[ERROR]\033[0m $*" >&2
}

log_success() {
    echo -e "\033[00;32m[SUCCESS]\033[0m $*"
}

# スクリプトに渡された引数を確認する
if [ -z "$1" ]; then
    log_error "Usage: $0 <directory>"
    exit 1
fi

TARGET_DIR="$1"

# 絶対パスに変換する
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

if [ ! -d "$TARGET_DIR" ]; then
    log_error "Directory not found: $TARGET_DIR"
    exit 1
fi

cd "$TARGET_DIR"

log_info "Creating development environment in $TARGET_DIR..."

# 必要なファイルが揃っているか確認する
REQUIRED_FILES=(".python-version" "pyproject.toml")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Required file '$file' not found in $TARGET_DIR"
        exit 1
    fi
done

# .python-version ファイルからバージョンを読み取る
FULL_VERSION=$(cat .python-version)
# メジャーとマイナーバージョンのみ抽出（例: 3.9.7 → 3.9）
PYTHON_VERSION=$(echo "$FULL_VERSION" | cut -d. -f1,2)
log_info "Required Python version: $FULL_VERSION (using $PYTHON_VERSION)"

# Python が指定バージョンでインストールされているか確認する
if ! command -v py "-$PYTHON_VERSION" --version &>/dev/null; then
    log_info "Python $PYTHON_VERSION is not installed. Installing..."
    # インストーラをダウンロードする
    curl -O "https://www.python.org/ftp/python/${PYTHON_VERSION}.0/python-${PYTHON_VERSION}.0-amd64.exe"
    # サイレントインストール
    "./python-${PYTHON_VERSION}.0-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1
    # インストーラを削除する
    rm "python-${PYTHON_VERSION}.0-amd64.exe"
    log_success "Python $PYTHON_VERSION installed successfully"
fi

# Poetry がインストールされているか確認する
if ! command -v poetry &>/dev/null; then
    log_info "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    log_success "Poetry installed successfully"
fi

# Python のパスを取得し、Windows から WSL 形式に変換する
log_info "Getting Python path..."
PYTHON_PATH=$(py "-$PYTHON_VERSION" -c "import sys; print(sys.executable)" | sed -E 's/^(\w+)+/\L\1/g' | sed -e 's/\\/\//g' | sed -e 's/://g' | sed -e '/^\//!s/^/\//g')

if [ -n "$PYTHON_PATH" ]; then
    log_info "Using Python path: $PYTHON_PATH"
    # Poetry の仮想環境を設定する
    log_info "Configuring Poetry virtual environment..."
    poetry env use "$PYTHON_PATH"
else
    log_error "Failed to get Python path"
    exit 1
fi

# 全ての依存関係をインストール（開発用依存関係を含む）
log_info "Installing all dependencies including development packages..."
poetry install

# Git hooks の設定
log_info "Setting up Git hooks..."
mkdir -p .git/hooks

# pre-commit hook の設定（存在しない場合のみ）
if [ ! -f ".git/hooks/pre-commit" ]; then
    # pre-commit.template はこのスクリプトと同じディレクトリにある前提
    cp "$(dirname "$0")/pre-commit.template" .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    log_success "Git hooks configured successfully"
fi

log_success "Development environment setup completed in $TARGET_DIR!"
