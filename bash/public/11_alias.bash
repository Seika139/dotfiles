#!/usr/bin/env bash

# lessのオプション設定 SEE : https://qiita.com/delphinus/items/b04752bb5b64e6cc4ea9
export LESS="-g -i -M -R -S -W"

function less_lf() {
  # Linux は改行コードが LF だが windows は改行コードが CR + LFのため
  # windows で less を実行すると ^M がたくさん表示されることがある
  # そのための対応策
  if is_win; then
    # 引数がある場合はファイルとして扱い、ない場合は標準入力を使う
    if [[ -n "$1" ]]; then
      sed s/^M//g "$1" | less "$LESS"
    else
      sed s/^M//g | less "$LESS"
    fi
  else
    if [[ -n "$1" ]]; then
      less "$LESS" "$1"
    else
      less "$LESS"
    fi
  fi
}

# ls にデフォルトで色をつける
# 2025.09.03 追記: brewでインストールしたezaを使用
if command -v eza &>/dev/null; then
  alias ls='eza'
  alias ll='eza -al'
else
  alias ls='ls -GF --color=auto'
  alias ll="ls -al --color=auto"
fi
export LSCOLORS=cxfxgxdxbxegedabagacad
# [Terminal.appでlsのファイル色を変える - by edvakf in hatena](https://edvakf.hatenadiary.org/entry/20080413/1208042916)
# [Terminalで「ls」したら「ls -G」が実行されるようにして、色も設定する。 - taoru's memo](https://taoru.hateblo.jp/entry/20120418/1334713778)

# grepの検索条件に該当する部分にデフォルトで色を付ける。GREP_OPTIONS は非推奨になったのでエイリアスで対応した
# 2025.09.03 追記: brewでインストールしたripgrepを使用
if command -v rg &>/dev/null; then
  # --glob '!.git' を追加して、.gitディレクトリを"絶対に"検索しないようにする
  # -S/--smart-case を追加して、賢い大文字小文字の区別を有効にする
  alias grep='rg --color=auto --glob "!.git" -S'

  # 全てのファイル（隠しファイルや.gitignoreも）を検索するエイリアスを追加
  alias rga='rg -uuu'
else
  alias grep='grep --color=auto'
  alias fgrep='fgrep --color=auto'
  alias egrep='egrep --color=auto'
fi

∫# cat を bat に置き換える
# 2025.09.03 追記: brewでインストールしたbatを使用
if command -v bat &>/dev/null; then
  alias cat='bat --paging=never --style=plain'

  # コマンドの用途を調べるときに `xxx -h | bah` とすると見やすくなる
  alias bah='bat --plain -l=help'
fi

# gnu-sed (gsed) がインストールされている場合は sed を gsed で上書きする
if command -v gsed &>/dev/null; then
  alias sed='gsed'
fi

# 2026.01.24 追記: brew でインストールした zoxide を使用
if command -v zoxide &>/dev/null; then
  eval "$(zoxide init bash)"
fi

# 補完設定: dockerの補完を設定
alias d='docker'
alias dc='docker compose'
if command -v docker &>/dev/null; then
  # 一時ファイルに補完スクリプトを保存して読み込む
  _docker_completion_tmp="/tmp/docker_completion_$$"
  docker completion bash >"$_docker_completion_tmp" 2>/dev/null
  if [ -f "$_docker_completion_tmp" ]; then
    # shellcheck source=/dev/null
    source "$_docker_completion_tmp"
    complete -F __start_docker d dc
    rm -f "$_docker_completion_tmp"
  fi
fi

# 補完設定: miseの補完を設定（シンプルな代替方法）
alias m='mise run'
if command -v mise &>/dev/null; then
  eval "$(mise completion bash)"

  # miseの基本的な補完（タスク名のみ）
  _mise_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local tasks
    tasks=$(mise tasks --no-header 2>/dev/null | awk '{print $1}')
    # shellcheck disable=SC2207
    IFS=$'\n' COMPREPLY=($(compgen -W "$tasks" -- "$cur"))
    unset IFS
  }
  complete -F _mise_complete m
  complete -F _mise_complete mise
fi

# AWS CLI の補完を有効化する
aws_completer_path="$(which aws_completer 2>/dev/null || true)"
if [[ -f "$aws_completer_path" ]]; then
  complete -C "$aws_completer_path" aws
elif command -v aws >/dev/null 2>&1; then
  # aws コマンドが存在する場合でも、aws_completer が見つからないことがある場合は警告を表示
  echo "Warning: aws command found, but aws_completer is missing."
  echo "Please ensure AWS CLI is properly installed."
fi

# GitHub CLI のエイリアス
alias gal='gh auth login'
alias gas='gh auth status'

# GitHub CLI の補完を有効化する
if command -v gh &>/dev/null; then
  eval "$(gh completion -s bash)"
fi

# Claude Code のエイリアス
alias cc='claude --dangerously-skip-permissions'
