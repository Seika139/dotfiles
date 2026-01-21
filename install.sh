#!/usr/bin/env bash

# shellcheck disable=SC2016,SC2162

# dotfiles を clone したらまず実行するインストーラ

# dotfiles のルートディレクトリを動的に取得
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/" && pwd)"
if [ ! -e "${ROOT}" ]; then
  echo "No such directory ${ROOT}"
  exit 1
fi

# 非対話モードの判定
# REMOTE_CONTAINERS, CI, NONINTERACTIVE のいずれかが設定されている場合は非対話モード
if [[ -n "${REMOTE_CONTAINERS}" ]] || [[ -n "${CI}" ]] || [[ -n "${NONINTERACTIVE}" ]]; then
  NONINTERACTIVE=true
  echo -e "\033[33m⚠️  非対話モードで実行します（環境変数: REMOTE_CONTAINERS=${REMOTE_CONTAINERS}, CI=${CI}, NONINTERACTIVE=${NONINTERACTIVE}）\033[0m"
else
  NONINTERACTIVE=false
fi

# カラー出力ヘルパがまだ読み込まれていない環境でも利用できるようにする
if ! declare -F echo_yellow >/dev/null 2>&1; then
  echo_yellow() {
    if [[ $1 == "-n" ]]; then
      shift
      printf '\033[00;33m%s\033[0m' "$*"
    else
      printf '\033[00;33m%s\033[0m\n' "$*"
    fi
  }
fi

# Ensure this script is sourced; otherwise abort to avoid return errors later.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "このスクリプトは source $ROOT/install.sh として実行してください。"
  exit 1
fi

#-------------------------------------
# 0. install homebrew (if OSX)
#-------------------------------------

# homebrew インストール後にパスを追加する可能性があるため
# homebrew が入っていない OSX の場合は先にインストールさせて再実行させる
if [[ $(uname) = "Darwin" ]] && ! type brew >/dev/null 2>&1; then
  echo -e "\033[00;33m💻homebrew をインストールします"
  echo -e "以下の /bin/bash から始まるインストールのコマンドは古い可能性があるので注意してください\033[0m"
  url="https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
  if [[ $(curl ${url} -o /dev/null -w '%{http_code}\n' -s) = "200" ]]; then
    /bin/bash -c "$(curl -fsSL ${url})" # 書き換える必要性が起こりうるコマンド
    echo -e "\033[00;33m💡homebrew のインストールが完了しました。\033[0m"
    echo -n '次のテキストがインストール時に表示され、 ~/.bash_profile への追記を促された場合は、'
    echo '代わりに ~/dotfiles/bash/private/ 内に追記してください。'
    echo -e "\033[01;37m- Run this command in your terminal to add Homebrew to your PATH:"
    echo '    (echo; echo '"'"'eval "$(/opt/homebrew/bin/brew shellenv)"'"'"') >>' "${HOME}/.bash_profile"
    echo -n '    eval "$(/opt/homebrew/bin/brew shellenv)"'
    echo -e "\033[00;33m <- 後で ~/dotfiles/bash/private/ を読み込むことで実行されるので実行不要\033[0m"
    echo ''

    shell_env_file="${ROOT}/bash/private/00_shellenv.bash"
    if [ ! -e "${shell_env_file}" ]; then
      echo "${shell_env_file} が存在しません。"
      if [[ "${NONINTERACTIVE}" == "true" ]]; then
        # 非対話モードの場合は自動的に追加
        echo -e "\033[00;33m非対話モードのため、自動的に shellenv を追加します\033[0m"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >>"${shell_env_file}"
      else
        echo -en '\033[00;33m`eval "$(/opt/homebrew/bin/brew shellenv)"` を'"${shell_env_file} に追加してよろしいですか？"
        read -p "$(echo -e '[Y/n]: \033[0m')" ANS0
        echo ''
        if [[ $ANS0 != [nN] ]]; then
          echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >>"${shell_env_file}"
        else
          echo -e "\033[00;33m brew コマンドが実行できない可能性があるのでご注意ください。"
        fi
        unset ANS0
      fi
    fi
  else
    echo -e "\033[38;2;250;180;100m次のURLが存在しませんでした。${url}"
    echo -e "https://brew.sh/index_ja を見て最新のコマンドに書き換えてください\033[0m"
    return 0
  fi
fi

#-------------------------------------
# 1. link files
#-------------------------------------

# デバイスの種類をチェックする
echo -e 'Check uname: $(uname) is' "\033[01;37m$(uname)\033[0m"
echo -e 'Check OS tpye: $OSTYPE is' "\033[01;37m${OSTYPE}\033[0m"
echo ""

# Windows の Git Bash でシンボリックリンクを作成するには一手間かかる
# ref : https://onl.la/wFBsfCN
# ref : https://qiita.com/ucho/items/c5ea0beb8acf2f1e4772
if [[ "${OSTYPE}" == msys* ]]; then
  echo "Windows では git bash を管理者権限で開いて実行しないとシンボリックリンクの作成に失敗することがあります。"
  if [[ "${NONINTERACTIVE}" == "true" ]]; then
    # 非対話モードの場合は警告を表示して続行
    echo -e "\033[33m⚠️  非対話モードのため、管理者権限の確認をスキップして続行します\033[0m"
    echo -e "\033[33m⚠️  シンボリックリンクの作成に失敗する可能性があります\033[0m"
  else
    read -p "$(echo -e '\033[00;33mこのまま続けてよろしいですか？ [y/N]: \033[0m')" ANS1
    if [[ $ANS1 != [yY] ]]; then
      echo "処理を中断しました。管理者権限で開いた git bash で再実行してください。"
      return 0
    fi
    unset ANS1
  fi

  export MSYS=winsymlinks:nativestrict

  # .bash_profile のシンボリックリンクも貼り直す必要がある
  CURRENT_DIR=$(pwd)
  cd "${ROOT}" && ln -sfv "bash/.bashenv" ".bash_profile"
  cd "${CURRENT_DIR}" && unset CURRENT_DIR
fi

# シンボリックリンクを貼る
files_to_link=(
  ".bash_logout"
  ".bash_profile"
  ".gitconfig"
  ".gitignore_global"
  ".gitmessage"
  ".cursor"
)

echo -e "\033[01;37m以下のファイルのシンボリックリンクを作成します。\033[0m"
echo "${files_to_link[@]}"
echo ""

for file in "${files_to_link[@]}"; do # [@] で全ての要素にアクセス
  ln -sfv "${ROOT}/${file}" "${HOME}"
  # ln コマンドのオプション
  # -s : シンボリックリンク(無いとハードリンクになる)
  # -i : 別名となるパス名が存在する時は確認する
  # -f : 別名となるパス名が存在する時も強制実行する
  # -v : 詳細を表示
done

unset files_to_link file

#-------------------------------------
# 1-1. link files (.ssh/config)
# .ssh/config.secret は .gitignore の対象なので、存在しない場合は作る
# 元々あった .ssh/config が消されないように dotfiles/.ssh 内に保存する
#-------------------------------------
ssh_config_secret="${ROOT}/.ssh/config.secret"

if [ ! -e "${ssh_config_secret}" ]; then
  touch "${ssh_config_secret}"
  if [ -e "${HOME}/.ssh/config" ]; then
    backup_suffix="$(date '+%Y-%m-%d_%H-%M-%S')"
    cp "${HOME}/.ssh/config" "${ROOT}/.ssh/config_save_${backup_suffix}"
  fi
fi
ln -sfv "${ROOT}/.ssh/config" "${HOME}/.ssh"
ln -sfv "${ssh_config_secret}" "${HOME}/.ssh"

#-------------------------------------
# 2. .gitconfig.local
#-------------------------------------

# 無い場合は作成する
file="${ROOT}/.gitconfig.local"
if [ ! -e "${file}" ]; then
  echo ".gitconfig.local を作成します"

  if [[ "${NONINTERACTIVE}" == "true" ]]; then
    # 非対話モードの場合は以下の優先順位で値を取得:
    # 1. 既存の git config --global の設定
    # 2. 環境変数 (GIT_USER_NAME, GIT_USER_EMAIL)
    # 3. デフォルト値 (CHANGE-ME, changeme@example.com)

    # 既存の git 設定を確認
    EXISTING_GIT_NAME=$(git config --global user.name 2>/dev/null || echo "")
    EXISTING_GIT_EMAIL=$(git config --global user.email 2>/dev/null || echo "")

    # 優先順位に従って値を決定
    if [[ -n "${EXISTING_GIT_NAME}" ]]; then
      NAME="${EXISTING_GIT_NAME}"
      NAME_SOURCE="git config --global"
    elif [[ -n "${GIT_USER_NAME}" ]]; then
      NAME="${GIT_USER_NAME}"
      NAME_SOURCE="環境変数 GIT_USER_NAME"
    else
      NAME="CHANGE-ME"
      NAME_SOURCE="デフォルト値"
    fi

    if [[ -n "${EXISTING_GIT_EMAIL}" ]]; then
      EMAIL="${EXISTING_GIT_EMAIL}"
      EMAIL_SOURCE="git config --global"
    elif [[ -n "${GIT_USER_EMAIL}" ]]; then
      EMAIL="${GIT_USER_EMAIL}"
      EMAIL_SOURCE="環境変数 GIT_USER_EMAIL"
    else
      EMAIL="changeme@example.com"
      EMAIL_SOURCE="デフォルト値"
    fi

    # shellcheck disable=SC2088
    DEFAULT_CORE_EXCLUDES_FILE="~/.gitignore_global"
    CORE_EXCLUDES_FILE="${DEFAULT_CORE_EXCLUDES_FILE}"
    # shellcheck disable=SC2088
    DEFAULT_SOURCETREE_CMD='~/Applications/Sourcetree.app/Contents/Resources/opendiff-w.sh \"$LOCAL\" \"$REMOTE\" -ancestor \"$BASE\" -merge \"$MERGED\"'
    SOURCETREE_CMD="${DEFAULT_SOURCETREE_CMD}"

    echo -e "\033[33m非対話モードのため、以下の設定で .gitconfig.local を作成します:\033[0m"
    echo -e "  user.name = ${NAME} (from ${NAME_SOURCE})"
    echo -e "  user.email = ${EMAIL} (from ${EMAIL_SOURCE})"
    if [[ "${NAME}" == "CHANGEME" ]] || [[ "${EMAIL}" == "changeme@example.com" ]]; then
      echo -e "\033[33m⚠️  git config や環境変数が設定されていないため、プレースホルダー値を使用しています\033[0m"
      echo -e "\033[33m⚠️  後で .gitconfig.local を編集して正しい値に変更してください\033[0m"
    fi

    unset EXISTING_GIT_NAME EXISTING_GIT_EMAIL NAME_SOURCE EMAIL_SOURCE
  else
    read -p "git config user.name = " NAME
    read -p "git config user.email = " EMAIL
    # shellcheck disable=SC2088
    DEFAULT_CORE_EXCLUDES_FILE="~/.gitignore_global"
    read -p "git config core.excludesfile = [${DEFAULT_CORE_EXCLUDES_FILE}]" CORE_EXCLUDES_FILE
    # shellcheck disable=SC2088
    DEFAULT_SOURCETREE_CMD='~/Applications/Sourcetree.app/Contents/Resources/opendiff-w.sh \"$LOCAL\" \"$REMOTE\" -ancestor \"$BASE\" -merge \"$MERGED\"'
    read -p "git config mergetool.sourcetree.cmd = [${DEFAULT_SOURCETREE_CMD}]" SOURCETREE_CMD
  fi

  # gitコマンドで確認・追加するときは次のようにやる
  #
  # git config [key] : 確認 / --list で一覧表示
  #
  # git config [key] [設定内容] : 新たにその値に設定する
  #   --global で HOME ディレクトリ下の .gitconfig に書き込む
  #   --file [PATH] で PATH の示すファイルに設定に書き込む

  cat <<EOF >"${file}"
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
# 3. pre load bash_profile
#-------------------------------------

# 初回の bash_profile 読み込み前に、必要な処理をする

SSH_DIR="${HOME}/.ssh/"
if [ ! -d "${SSH_DIR}" ]; then
  # ~/.ssh がないと 06_ssh-agent.bash 内で start_agent の実行に失敗するので必ず ~/.ssh があることを保証する
  mkdir -p "${SSH_DIR}"
  chmod 700 "${SSH_DIR}"
fi

#-------------------------------------
# 4. load bash_profile
#-------------------------------------

# シンボリックリンクを貼り終わったのでシェルを読み込む

echo ''
echo 'loading ~/.bash_profile'
source "${HOME}/.bash_profile" >/dev/null
echo 'finish loading'
echo ''

#-------------------------------------
# 5. setup Claude settings (if ~/.claude is empty)
#-------------------------------------

# ~/.claude が空または存在しない場合のみシンボリックリンクを作成
if [ ! -d "${HOME}/.claude" ] || [ -z "$(ls -A "${HOME}/.claude" 2>/dev/null)" ]; then
  echo -e "\\033[01;37m~/.claude が空です。Claude設定のシンボリックリンクを作成します。\\033[0m"

  # ~/.claude ディレクトリを作成（存在しない場合）
  mkdir -p "${HOME}/.claude"

  # mise.local.tomlから DEFAULT_CLAUDE_PROFILE を読み取り
  CLAUDE_MISE_LOCAL="${ROOT}/claude/mise.local.toml"
  if [ -f "${CLAUDE_MISE_LOCAL}" ]; then
    DEFAULT_CLAUDE_PROFILE=$(grep '^DEFAULT_CLAUDE_PROFILE=' "${CLAUDE_MISE_LOCAL}" | cut -d'"' -f2)

    if [ -n "${DEFAULT_CLAUDE_PROFILE}" ]; then
      CLAUDE_PROFILE_DIR="${ROOT}/claude/profiles/${DEFAULT_CLAUDE_PROFILE}"

      if [ -d "${CLAUDE_PROFILE_DIR}" ]; then
        echo "Claude profile '${DEFAULT_CLAUDE_PROFILE}' からシンボリックリンクを作成します"

        # Claude設定ファイルのシンボリックリンクを作成
        claude_files=("settings.json" "settings.local.json" "CLAUDE.md")
        for file in "${claude_files[@]}"; do
          source_file="${CLAUDE_PROFILE_DIR}/${file}"
          target_file="${HOME}/.claude/${file}"

          if [ -f "${source_file}" ]; then
            ln -sfv "${source_file}" "${target_file}"
          fi
        done

        # commands ディレクトリのシンボリックリンクを作成
        commands_source="${CLAUDE_PROFILE_DIR}/commands"
        commands_target="${HOME}/.claude/commands"
        if [ -d "${commands_source}" ]; then
          ln -sfv "${commands_source}" "${commands_target}"
        fi

        echo -e "\\033[32m✅ Claude設定を '${DEFAULT_CLAUDE_PROFILE}' プロファイルからリンクしました\\033[0m"
      else
        echo -e "\\033[33m⚠️ Claude profile directory '${CLAUDE_PROFILE_DIR}' が見つかりません\\033[0m"
      fi
    else
      echo -e "\\033[33m⚠️ DEFAULT_CLAUDE_PROFILE が設定されていません\\033[0m"
    fi
  else
    echo -e "\\033[33m⚠️ ${CLAUDE_MISE_LOCAL} が見つかりません\\033[0m"
  fi
else
  echo -e "\\033[33m~/.claude に既存のファイルがあります。Claude設定のセットアップをスキップします。\\033[0m"
fi

#-------------------------------------
# 6. upgrade homebrew (if OSX)
#-------------------------------------

# フォーミュラがインストール済みの場合はアップデートを行い、未インストールの場合はインストールを行う
function brew_upstall {
  for FORMULA in "$@"; do
    if brew ls --versions "$FORMULA" >/dev/null; then
      echo_yellow "$FORMULA はインストール済みです。アップグレードを実施します..."
      brew upgrade "$FORMULA"
    else
      echo_yellow "$FORMULA は未インストールです。インストールを実施します..."
      brew install "$FORMULA"
    fi
  done
}

if command -v brew >/dev/null 2>&1; then
  if [[ "${NONINTERACTIVE}" == "true" ]]; then
    # 非対話モードの場合は brew upgrade をスキップ
    echo -e "\033[33m非対話モードのため、brew upgrade をスキップします\033[0m"
    echo -e "  必要に応じて手動で 'brew upgrade' を実行してください"
  else
    read -p "$(echo_yellow 'brew upgrade を行いますか？時間がかかる場合があります [y/N]: ')" ANS
    case $ANS in
    [Yy]*)
      # macOS の場合は homebrew のアップグレードを行う
      printf "  🗒️  brew でインストールするパッケージの管理は %s で行います\n" "$HOME/dotfiles/brew/mise.toml"
      brew upgrade
      formulae=(
        "bash-completion"
        "git"
        "mise"
      )
      for FORMULA in "${formulae[@]}"; do
        brew_upstall "${FORMULA}"
      done
      ;;
    esac
    unset ANS FORMULA formulae
  fi
fi