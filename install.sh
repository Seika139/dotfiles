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
    ".bash_profile"
    ".gitconfig"
    ".gitignore_global"
    ".gitmessage"
)

echo -e "\033[00;33m以下のファイルのシンボリックリンクを作成します。\033[0m"
echo -e "\033[00;33m${files_to_link[@]}\033[0m"
echo -e "\033[00;33m古いものは消えてしまうので注意してください\033[0m"
echo ""

for file in ${files_to_link[@]}; do # [@] で全ての要素にアクセス
    ln -siv "${ROOT}/${file}" "${HOME}"
    # ln コマンドのオプション
    # -s : シンボリックリンク(無いとハードリンクになる)
    # -i : 別名となるパス名が存在する時は確認する
    # -f : 別名となるパス名が存在する時も強制実行する
    # -v : 詳細を表示
done

unset files_to_link file

#-------------------------------------
# 2. .gituser
#-------------------------------------

# 無い場合は作成する
file="${ROOT}/.gituser"
if [ ! -e $file ]; then
    echo ".gituser を作成してください"
    read -p "git name = " name
    read -p "git email = " email
    cat <<GITUSER >$file
[user]
	name = ${name}
	email = ${email}

GITUSER
    unset name email
fi

# シンボリックリンクを貼る
ln -siv "${file}" "${HOME}"
unset file

#-------------------------------------
# 3. finish install
#-------------------------------------

# シンボリックリンクを貼り終わったのでシェルを読み込む

source "${HOME}/.bash_profile"

#-------------------------------------
# 11. homwbrew
#-------------------------------------

if is_osx && ! executable brew; then
    # home brew をインストールする
    info "homebrew をインストールします"
    notice "以下の /bin/bash から始まるインストールのコマンドは古い可能性があるので注意してください"
    url="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
    if [[ $(curl ${url} -o /dev/null -w '%{http_code}\n' -s) = "200" ]]; then
        /bin/bash -c "$(curl -fsSL ${url})" # 書き換える必要性が起こりうるコマンド
    else
        warn "次のURLが存在しませんでした。${url}"
        warn "https://brew.sh/index_ja を見て最新のコマンドに書き換えてください"
    fi
fi

if executable brew; then
    yellow "brew upgrade を行いますか？時間がかかる場合があります [y/N]: "
    read ANS

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
