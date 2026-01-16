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

log_info "Starting production environment setup..."

# .python-version ファイルから Python バージョンを読み取る
if [ -f ".python-version" ]; then
  PYTHON_VERSION=$(cat .python-version)
  # .python-version が CRLF で保存されている場合に失敗するので末尾の改行文字を削除する
  PYTHON_VERSION=${PYTHON_VERSION%$'\r'}
  log_info "Required Python version: $PYTHON_VERSION"
else
  log_error ".python-version file not found"
  exit 1
fi

# pyenv で Python バージョンが利用可能か確認する
if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
  log_info "Installing Python $PYTHON_VERSION..."
  pyenv install "$PYTHON_VERSION"
  log_success "Python $PYTHON_VERSION installed successfully"
fi

# Python バージョンを設定する
log_info "Setting local Python version..."
pyenv local "$PYTHON_VERSION"
log_success "Python version set to $PYTHON_VERSION"

# Poetry がインストールされているか確認する
if ! command -v poetry &>/dev/null; then
  log_info "Poetry not found. Installing Poetry..."
  curl -sSL https://install.python-poetry.org | python3 -
  log_success "Poetry installed successfully"
fi

# Poetry の設定確認
if [ ! -f "pyproject.toml" ]; then
  log_error "pyproject.toml not found. Please ensure the project is properly initialized."
  exit 1
fi

# Poetry の仮想環境を設定する
log_info "Configuring Poetry virtual environment..."
PYTHON_PATH=$(pyenv prefix "$PYTHON_VERSION")/bin/python
poetry env use "$PYTHON_PATH"

# 設定の確認
log_info "Verifying Python version..."
POETRY_PYTHON_VERSION=$(poetry run python --version)
log_success "Poetry is using: $POETRY_PYTHON_VERSION"

# 本番環境用の依存関係をインストール（開発用依存関係を除外）
log_info "Installing production dependencies..."
poetry install --only main
log_success "Production dependencies installed successfully"
