#!/usr/bin/env bash

# とりあえずのインストーラ

#-------------------------------------
# 1. link files
#-------------------------------------

# NOTE: 必ずホームディレクトリにクローンするものとする
ROOT="${HOME}/dotfiles"
if [ ! -e $ROOT ]; then
    echo "No such directory ${ROOT}"
    exit 1
fi

# シンボリックリンクを貼る
files_to_link=(
    ".bash_logout"
    ".bash_profile"
    ".gitconfig"
    ".gitignore_global"
    ".gitmessage"
)

echo -e "\033[01;37m以下のファイルのシンボリックリンクを作成します。"
echo -e "${files_to_link[@]}\033[0m"
echo ""

# Windows の Git Bash でシンボリックリンクを作成するには一手間かかる
# ref : https://onl.la/wFBsfCN
# ref : https://qiita.com/ucho/items/c5ea0beb8acf2f1e4772
if [[ "${OSTYPE}" == msys* ]]; then
    export MSYS=winsymlinks:nativestrict

    # .bash_profile のシンボリックリンクも貼り直す必要がある
    CURRENT_DIR=$(pwd)
    cd "${ROOT}"
    ln -sf "bash/.bashenv" ".bash_profile"
    cd "${CURRENT_DIR}"
    unset CURRENT_DIR
fi

for file in ${files_to_link[@]}; do # [@] で全ての要素にアクセス
    ln -sfv "${ROOT}/${file}" "${HOME}"
    # ln コマンドのオプション
    # -s : シンボリックリンク(無いとハードリンクになる)
    # -i : 別名となるパス名が存在する時は確認する
    # -f : 別名となるパス名が存在する時も強制実行する
    # -v : 詳細を表示
done

unset files_to_link file

#-------------------------------------
# 2. .gitconfig.local
#-------------------------------------

# 無い場合は作成する
file="${ROOT}/.gitconfig.local"
if [ ! -e $file ]; then
    echo ".gitconfig.local を作成します"
    read -p "git config user.name = " NAME
    read -p "git config user.email = " EMAIL
    DEFAULT_CORE_EXCLUDES_FILE="~/.gitignore_global"
    read -p "git config core.excludesfile = [${DEFAULT_CORE_EXCLUDES_FILE}]" CORE_EXCLUDES_FILE
    DEFAULT_SOURCETREE_CMD='~/Applications/Sourcetree.app/Contents/Resources/opendiff-w.sh \"$LOCAL\" \"$REMOTE\" -ancestor \"$BASE\" -merge \"$MERGED\"'
    read -p "git config mergetool.sourcetree.cmd = [${DEFAULT_SOURCETREE_CMD}]" SOURCETREE_CMD

    # gitコマンドで確認・追加するときは次のようにやる
    #
    # git congfig [key] : 確認 / --list で一覧表示
    #
    # git congfig [key] [設定内容] : 新たにその値に設定する
    #   --global で HOME ディレクトリ下の .gitconfig に書き込む
    #   --file [PATH] で PATH の示すファイルに設定に書き込む

    cat <<EOF >${file}
[user]
	name = ${NAME}
	email = ${EMAIL}

[core]
	excludesfile = ${CORE_EXCLUDES_FILE:-${DEFAULT_CORE_EXCLUDES_FILE}}

[mergetool "sourcetree"]
	cmd = ${SOURCETREE_CMD:-${DEFAULT_SOURCETREE_CMD}}
EOF
    unset NAME EMAIL DEFAULT_CORE_EXCLUDES_FILE CORE_EXCLUDES_FILE DEFAULT_SOURCETREE_CMD SOURCETREE_CMD
fi

# シンボリックリンクを貼る
ln -sfv "${file}" "${HOME}"
unset file

#-------------------------------------
# 3. load bash_profile
#-------------------------------------

# シンボリックリンクを貼り終わったのでシェルを読み込む

source "${HOME}/.bash_profile" >/dev/null

#-------------------------------------
# 11. homwbrew
#-------------------------------------

if is_osx && ! executable brew; then
    # home brew をインストールする
    echo_yellow "homebrew をインストールします"
    echo_yellow "以下の /bin/bash から始まるインストールのコマンドは古い可能性があるので注意してください"
    url="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    if [[ $(curl ${url} -o /dev/null -w '%{http_code}\n' -s) = "200" ]]; then
        /bin/bash -c "$(curl -fsSL ${url})" # 書き換える必要性が起こりうるコマンド
    else
        warn "次のURLが存在しませんでした。${url}"
        warn "https://brew.sh/index_ja を見て最新のコマンドに書き換えてください"
    fi
fi

if executable brew; then
    read -p "$(echo_yellow 'brew upgrade を行いますか？時間がかかる場合があります [y/N]: ')" ANS
    case $ANS in
    [Yy]*)
        brew upgrade # homwbrew および homoebrewで管理しているパッケージをアップデートする

        # TODO : brewfile をもとに brew install したい
        # ref : https://tech.gootablog.com/article/homebrew-brewfile/

        # とりあえず必要なやつだけインストールする
        brew install "bash-completion" && brew upgrade "bash-completion"
        brew install "git" && brew upgrade "git"
        ;;
    esac
    unset ANS
fi
