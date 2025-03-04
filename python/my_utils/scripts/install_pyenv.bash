#!/bin/bash

set -euo pipefail

# 定数と関数を定義する
BASHRC="$HOME/.bashrc"
PYENV_ROOT="$HOME/.pyenv"

log_info() {
    echo -e "\033[00;33m[INFO]\033[0m $*"
}

log_error() {
    echo -e "\033[00;31m[ERROR]\033[0m $*" >&2
}

log_success() {
    echo -e "\033[00;32m[SUCCESS]\033[0m $*"
}

# .bashrcの更新処理を行う関数
update_bashrc() {
    local temp_file
    temp_file=$(mktemp)

    # 既存の設定があるか確認
    if grep -q "PYENV_ROOT" "$BASHRC"; then
        log_info "pyenv configuration already exists in .bashrc"
        return 0
    fi

    # 既存ファイルの内容を保持しつつ、空行が2行以上続かないようにする
    awk 'NR==1{print} NR>1{if(NF>0){print $0} else {if(!prev_empty){print $0}} prev_empty=(NF==0)}' "$BASHRC" >"$temp_file"

    # 1行空行を入れてから設定を追加するが、ファイルが空の場合は空行を入れない
    if [ -s "$temp_file" ]; then
        echo "" >>"$temp_file"
        cat <<'EOF' >>"$temp_file"
#!/bin/bash

EOF
    fi
    cat <<'EOF' >>"$temp_file"

# pyenv settings
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF

    # 元のファイルを置き換え
    mv "$temp_file" "$BASHRC"
}

main() {
    # pyenv がすでにインストールされているかを確認する
    if [ -d "$PYENV_ROOT" ]; then
        log_error "pyenv is already installed at $PYENV_ROOT"
        exit 1
    fi

    # pyenv をインストールする
    log_info "Installing pyenv..."
    if ! git clone https://github.com/pyenv/pyenv.git "$PYENV_ROOT" 2>/dev/null; then
        log_error "Failed to clone pyenv repository. Please check:"
        log_error "1. Git is installed and accessible"
        log_error "2. You have internet connection"
        log_error "3. GitHub is accessible from your network"
        exit 1
    fi

    # 環境変数を設定する
    log_info "Configuring environment variables..."

    # .bashrcのバックアップを作成
    if [ -f "$BASHRC" ]; then
        if ! cp "$BASHRC" "${BASHRC}.backup.$(date +%Y%m%d_%H%M%S)"; then
            log_error "Failed to create backup of .bashrc"
            exit 1
        fi
        log_info "Created backup of .bashrc"
        update_bashrc
    else
        # .bashrcが存在しない場合は新規作成
        cat <<'EOF' >"$BASHRC"
#!/bin/bash

# pyenv settings
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
    fi

    # インストール完了
    log_success "Installation completed successfully!"
    log_info "Note: To build Python versions, you may need to install additional packages:"
    log_info "    sudo dnf install gcc make zlib-devel bzip2-devel readline-devel sqlite-devel openssl-devel tk-devel libffi-devel xz-devel"
    log_info "Please run the following command to activate pyenv:"
    echo "    source $BASHRC"
    log_info "Or start a new shell session."
}

main
