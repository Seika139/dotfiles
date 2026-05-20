#!/usr/bin/env bash

# gitignore.io のコマンド
gi() {
  local queries
  queries="$(echo "$*" | tr ' ' ',')"
  curl -sL "https://www.toptal.com/developers/gitignore/api/$queries"
  echo
}

# gだけでもgitコマンドの補完が効くようにする
alias g="git"
if declare -F __git_wrap__git_main >/dev/null 2>&1; then
  complete -o bashdefault -o default -o nospace -F __git_wrap__git_main g
fi

# git branch
alias gb='git branch'
# リモートも表示する
alias gba='git branch -a'
# git status --short --branch の略。省略表記しつつブランチ名も確認できる
alias gs='git status -sb'
# git add
alias ga='git add'
# git commit
alias gc='git commit'
# git worktree
alias gw='git worktree'
# git worktree list
alias gwl='git worktree list'
# git pull
alias gpl='git pull'
# git tag list でバージョンタグを降順で表示
alias gtl="git tag | sort -rV"

PRETTY_FORMAT="%C(Yellow)%h %C(#519acf)%cd %C(#e0a77e)%cn %C(Reset)%s %C(#72e359)%d"
GL_DATE_FORMAT="%Y/%m/%d %H:%M:%S"

# git log … 飾り付けて表示
gl() {
  local command
  command=("git" "log" "--date=format-local:${GL_DATE_FORMAT}" "--pretty=format:${PRETTY_FORMAT}" "$@")
  echo_yellow "${command[*]}"
  "${command[@]}"
}

# git log … グラフ表示
glr() {
  local command
  command=("git" "log" "--date=format-local:${GL_DATE_FORMAT}" "--pretty=format:${PRETTY_FORMAT}" "--graph" "$@")
  echo_yellow "${command[*]}"
  "${command[@]}"
}

# git log … 修正ライン数が分かる
gll() {
  local command
  command=("git" "log" "--date=format-local:${GL_DATE_FORMAT}" "--pretty=format:${PRETTY_FORMAT}" "--numstat" "$@")
  echo_yellow "${command[*]}"
  "${command[@]}"
}

# git の不要なブランチを削除する
grm() {
  default_branch=$(git rev-parse --abbrev-ref origin/HEAD | sed 's/origin\///') || return 1
  echo_yellow "git checkout ${default_branch}" &&
    git checkout "${default_branch}" &&
    echo_yellow "git pull" &&
    git pull &&
    echo_yellow "git remote prune origin" &&
    git remote prune origin &&
    echo_yellow "git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -d" &&
    git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -d
}

alias gd='git diff --src-prefix="BEFORE/" --dst-prefix=" AFTER/"'

alias gr='git remote'
alias grp='git remote prune origin'
alias grpo='git remote prune origin'

alias gsl='git stash list --date=iso-local'

# 今いる git リポジトリのルートディレクトリへのパスを取得する
alias grd='git rev-parse --show-superproject-working-tree --show-toplevel | head -1'

# 新しく作ったブランチをプッシュするのがめんどい時のコマンド
gpsu() {
  branch_name=$(git symbolic-ref --short HEAD)
  echo_yellow "Executing alias : git push --set-upstream origin ${branch_name}"
  git push --set-upstream origin "$branch_name"
  unset branch_name
}

# 自分がコミットした差分だけを確認したい
gdd() {
  if [[ $1 == '--help' ]]; then
    less <<EOS
usage: gdd author commit1 commit2 [option]

commit1 & commit2 : Commit object. Not only hash but also branch name and tags are supported.
option (optional) : Options for 'git diff' are acceptable, such as --stat, -w

commit1 と commit2 の間で author が作成した差分を一覧表示する
author を - にすると author で絞り込まない

おすすめオプション
--stat           : 変更量をファイル単位で確認
-w --color-words : 改行コードや空白を無視しつつ、単語単位で差分を表示する
EOS
    return 0
  fi

  if [[ $# -lt 3 ]]; then
    echo_yellow 'このエイリアスは最低3つの引数を必要とします'
    echo_yellow "See : gdd --help"
    return 1
  fi

  # 引数が適切なコミットを指していない場合を弾く
  for arg in $2 $3; do
    if [[ $(git show "$arg" | wc -l) -eq 0 ]]; then
      echo
      echo_red -n '不適切なコミット '
      echo_yellow "$arg"
      return 1
    fi
  done

  # $2 と $3 の間のコミットのコミットハッシュを取得
  local -a command1=()
  if [[ "$1" == "-" ]]; then
    # $1 を - にすると author で絞り込まない
    command1=("git" "log" "--pretty=format:%H" "--no-merges" "$2..$3")
  else
    command1=("git" "log" "--pretty=format:%H" "--no-merges" "--author=${1}" "$2..$3")
  fi

  # コミットハッシュごとに変更があったファイルを取得
  command2="xargs -n1 git --no-pager diff --name-only"

  # 取得したファイルから重複を取り除く
  command3="sort -u"

  # 現在の自分のディレクトリにないフォルダについて command5 を実行するとエラーになるので除く
  # (他のブランチの変更を見るときに起こりがちだったので)
  command4="xargs -IXXX sh -c 'if [[ -e \"XXX\" ]]; then echo \"XXX\"; fi'"

  # これまでのコマンドで絞り込んだファイルに対して $2 と $3 の間の git diff を出力する
  local command5
  command5="xargs git diff $2..$3 ${*:4}"

  echo_yellow "${command1[*]} | $command2 | $command3 | $command4 | $command5"

  "${command1[@]}" | $command2 | $command3 |
    xargs -IXXX sh -c 'if [[ -e "XXX" ]]; then echo "XXX"; fi' |
    xargs git diff --src-prefix="BEFORE/" --dst-prefix=" AFTER/" "$2" "$3" "${@:4}"
}

tags_from_commit() {
  # git のコミットに対応するタグ・ブランチを取得する
  local tags
  tags=$(git branch -a --points-at "$1")
  tags="${tags//$'\n'/ }"
  echo "${tags//'*'/}" | sed -e 's/->//' -e 's/ +/ /' -e 's/^ *//' -e 's/  */ /g'
}

commit_with_tags() {
  local tags
  tags="$(tags_from_commit "$1")"
  echo_yellow -n "$1"
  if [[ -n "${tags}" ]]; then
    echo_red -n " (${tags})"
  fi
}

gcl() {
  if [[ $1 == '--help' ]]; then
    less <<EOS
usage: gcl commit1 commit2 [option] [path]

commit1 & commit2 : Commit object. Not only hash but also branch name and tags are supported.
option (optional) : Options for 'git log' are acceptable, such as --stat, --numstat
path   (optional) : Same usage as 'git log -p'
EOS
    return 0
  fi

  # $1 と $2 の共通祖先のコミットである $ancestor を探し
  # $1 と $ancestor、および $2 と $ancestor の差分を表示する
  # $3 以降の引数で検索する差分の範囲を絞り込むことができる

  if [[ $# -lt 2 ]]; then
    echo_yellow 'このエイリアスは最低2つの引数を必要とします'
    echo_yellow "See : gcl --help"
    return 1
  fi

  # 引数が適切なコミットを指していない場合を弾く
  for arg in $1 $2; do
    if [[ $(git show "$arg" | wc -l) -eq 0 ]]; then
      echo
      echo_red -n '不適切なコミット '
      echo_yellow "$arg"
      return 1
    fi
  done

  # 2つのコミットの共通祖先
  local ancestor
  ancestor="$(git merge-base "$1" "$2")"

  # $1 と $2 の コミットハッシュ
  local commit_id_a
  commit_id_a="$(git rev-parse "$1")"
  local commit_id_b
  commit_id_b="$(git rev-parse "$2")"

  local descendant
  if [[ "${ancestor}" == "${commit_id_a}" ]]; then
    descendant=$commit_id_b
  fi
  if [[ "${ancestor}" == "${commit_id_b}" ]]; then
    descendant=$commit_id_a
  fi

  if [[ "${ancestor}" == "${descendant}" ]]; then
    # 2つが同じコミットを指していた場合
    commit_with_tags "$ancestor"
    echo_cyan ' [SAME COMMIT]'
    return 0
  fi

  echo
  if [[ -n ${descendant} ]]; then
    # どちらかがもう一方の祖先だった場合
    commit_with_tags "$ancestor"
    echo_rgb -n 120 120 120 ' ________ '
    commit_with_tags "$descendant"
    echo
    echo
    echo_rgb 180 255 180 "git log ${ancestor}..${descendant} ${*:3}"
    git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"${PRETTY_FORMAT}" "${ancestor}".."${descendant}" "${@:3}"

  else
    # 両者のどちらとも同一でない祖先が存在する場合
    echo_rgb -n 180 180 100 "${ancestor}"
    echo_rgb -n 120 120 120 ' ________ '
    commit_with_tags "$commit_id_a"
    echo
    echo_rgb -n 120 120 120 "                                          \______ "
    commit_with_tags "$commit_id_b"
    echo

    # diff を表示するバージョン
    # echo_rgb 180 255 180 "git diff --histogram -w $1 $ancestor ${@:3}"
    # echo_rgb 180 255 180 "git diff --histogram -w $2 $ancestor ${@:3}"
    # git diff --histogram -w $1 $ancestor ${@:3}
    # git diff --histogram -w $2 $ancestor ${@:3}

    echo
    echo_rgb 180 255 180 "git log ${ancestor}..${commit_id_a} ${*:3}"
    echo_rgb 180 255 180 "git log ${ancestor}..${commit_id_b} ${*:3}"

    git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"${PRETTY_FORMAT}" "${ancestor}..${commit_id_a}" "${@:3}"
    git log --date=format-local:"%Y/%m/%d %H:%M:%S" --pretty=format:"${PRETTY_FORMAT}" "${ancestor}..${commit_id_b}" "${@:3}"

  fi
}

# コミットログから対象ファイルを誰がどれだけ編集したかを集計します
# usage: gln .
# usage: gln --since="2 weeks ago" .
# usage: gln --since="2026/01/10" --until="2026/01/20" .
# usage: gln path/to/file_or_dir
gln() {
  echo_yellow 'コミットログをもとに指定したファイル・ディレクトリを誰がどれだけ編集したかを集計します'

  # --pretty="AUTH:%an" で著者名行にプレフィックスを付け、統計行（数字開始）と確実に区別します
  git log --numstat --pretty="AUTH:%an" "$@" | awk '
    /^AUTH:/ {
      # 著者名をセット
      a = substr($0, 6)
      next
    }
    /^[0-9]/ {
      # 統計行（数字 削除数 パス）を処理
      if (a != "") {
        ins[a] += $1
        del[a] += $2
      }
      next
    }
    # 空行やバイナリファイル (- -) はスキップ
    END {
      for (i in ins) {
        printf "%d\t%d\t%d\t%s\n", ins[i], del[i], ins[i] + del[i], i
      }
    }
  ' | sort -rn -k3 | awk -F'\t' '
    BEGIN {
      printf "%8s  %8s  %8s  %-20s\n", "Added", "Removed", "Total", "Author"
    }
    {
      if ($3 > 0) {
        printf "%8d  %8d  %8d  %-20s\n", $1, $2, $3, $4
      }
    }'
}

glh() {
  echo_yellow '最初のコミットが古い順に作業者を表示します'
  local files=("$@")
  if [[ ${#files[@]} -eq 0 ]] && fzf_available; then
    # 引数なしなら fzf でパス選択。キャンセルされたらリポジトリ全体で集計する
    _gf_pick_paths files || files=()
  fi
  git log --pretty=format:"%ad %an" --date=short --reverse -- "${files[@]}" |
    awk '{if (!seen[$2]++) {print $0}}'
}

# fd + fzf でパス（ファイル/ディレクトリ）を複数選択するヘルパー
# 第1引数: 結果を格納する配列名（nameref）
# 戻り値: 0=選択あり, 1=キャンセル/fzf不可
_gf_pick_paths() {
  if ! fzf_available; then
    return 1
  fi
  local -n _out_arr="$1"
  _out_arr=()

  # NUL 区切りで安全に受け渡し、先頭に "." を加えて pwd を選択肢に含める。
  # コマンド置換 $() は NUL を保持できないので、プロセス置換で直接配列へ読む。
  local item
  while IFS= read -r -d '' item; do
    [[ -n "$item" ]] && _out_arr+=("$item")
  done < <(
    {
      printf '.\0'
      # .gitignore を正しく設定していれば自動的に除外されるが、念のため fd の --exclude オプションで除外するパターンを指定しておく
      # --hidden は隠しファイルを検索対象にするオプション
      fd --hidden --print0 \
        --exclude .git \
        --exclude node_modules \
        --exclude vendor \
        --exclude __pycache__ \
        --exclude .venv \
        --exclude .mypy_cache \
        --exclude .pytest_cache \
        --exclude .ruff_cache \
        --exclude htmlcov \
        --exclude .cache \
        --exclude .DS_Store \
        .
    } | fzf --read0 --print0 --multi \
      --prompt='パス選択 ❯ ' \
      --pointer='▶' \
      --marker='✓' \
      --header="$(
        echo_blue -n 'Tab  '
        echo -n '選択切替 / '
        echo_blue -n 'Shift+Tab '
        echo -n '選択切替（逆へ移動）/ '
        echo_blue -n 'ESC '
        echo 'フラグなしで続行'

        echo_blue -n 'Ctrl+A '
        echo -n '全選択 / '
        echo_blue -n 'Ctrl+D '
        echo -n '全解除 / '
        echo_blue -n 'Ctrl+/ '
        echo -n 'preview 切替'
      )" \
      --color='prompt:75,pointer:211,marker:84,header:italic:245,hl:84,hl+:84:reverse' \
      --bind='tab:toggle+down,shift-tab:toggle+up,ctrl-a:toggle-all,ctrl-d:deselect-all,ctrl-/:toggle-preview' \
      --preview-window='right,60%,wrap' \
      --preview 'printf "\033[1;33m── 選択対象a ──\033[0m\n"
        printf "  %s\n" {+}
        printf "\n\033[1;36m── ファイル/ディレクトリ ──\033[0m\n"
        if [[ -f {} ]]; then
          bat --color=always --style=full --line-range :120 {}
        else
          eza --tree --color=always {}
        fi'
  )

  ((${#_out_arr[@]} > 0))
}

# git log のフラグを fzf で複数選択するヘルパー
# 第1引数: 結果を格納する配列名（nameref）
# 戻り値: 0=fzf 起動成功（選択ゼロでも 0）, 1=fzf 不可
_gf_pick_flags() {
  if ! fzf_available; then
    return 1
  fi
  local -n _flags_out="$1"
  _flags_out=()

  # フラグ\t説明 の形式。--with-nth=1 で list 表示は左列のみ、preview に説明を表示
  local FLAG_CHOICES=(
    $'--stat\tファイルごとの追加/削除行数（視覚的な棒グラフ）'
    $'-p\tunified diff を含めて表示'
    $'--graph\tコミットグラフを線で表示'
    $'--numstat\tファイルごとの追加/削除行数（タブ区切り、機械処理向き）'
    $'--shortstat\tファイル数と合計追加/削除行数のみ'
    $'--name-status\t変更ファイル名 + 種別 (A=追加, M=変更, D=削除, R=リネーム)'
    $'--reverse\t古い順に表示'
    $'--first-parent\tマージコミットでメインライン側のみを辿る'
    $'--no-merges\tマージコミットを除外'
  )

  local picked
  picked=$(
    printf '%s\n' "${FLAG_CHOICES[@]}" |
      fzf --multi \
        --delimiter=$'\t' \
        --with-nth=1 \
        --prompt='フラグ選択 ❯ ' \
        --pointer='▶' \
        --marker='✓' \
        --header="$(
          echo_blue -n 'Tab '
          echo -n '選択切替 / '
          echo_blue -n 'Shift+Tab '
          echo -n '選択切替（逆へ移動）/ '
          echo_blue -n 'ESC '
          echo -n 'フラグなしで続行 / '
          echo_blue -n 'Ctrl+A '
          echo -n '全選択 / '
          echo_blue -n 'Ctrl+D '
          echo -n '全解除'
        )" \
        --color='prompt:75,pointer:211,marker:84,header:italic:245,hl:84,hl+:84:reverse' \
        --bind='tab:toggle+down,shift-tab:toggle+up,ctrl-a:toggle-all,ctrl-d:deselect-all' \
        --preview-window='down,3,wrap' \
        --preview 'printf "\033[38;5;214m%s\033[0m\n" {2..}'
  )

  # picked が空でも成功扱い（ユーザー意図 = フラグなしで続行）
  if [[ -z "$picked" ]]; then
    return 0
  fi

  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] && _flags_out+=("${line%%$'\t'*}")
  done <<<"$picked"

  return 0
}

# gf [<git log フラグ>...] [-- <path>...]
# - 引数なし: fzf でフラグ選択 → fzf でパス選択 → git log 実行
# - フラグだけ指定: パスは fzf で選択
# - -- <path> 指定: フラグだけ fzf で選択（フラグも省略可）
# - フラグも -- も両方指定: fzf を一切起動せず即実行
# どの fzf もキャンセル可。フラグキャンセル = フラグなし、パスキャンセル = パスなし。
gf() {
  # 引数を -- で前後に分割
  local flags=()
  local files=()
  local seen_sep=0
  local arg
  for arg in "$@"; do
    if ((seen_sep == 0)) && [[ "$arg" == "--" ]]; then
      seen_sep=1
      continue
    fi
    if ((seen_sep == 0)); then
      flags+=("$arg")
    else
      files+=("$arg")
    fi
  done

  # フラグが空なら fzf で選択（キャンセル可: 空のまま続行）
  if [[ ${#flags[@]} -eq 0 ]] && fzf_available; then
    _gf_pick_flags flags || flags=()
  fi

  # パスが空なら fzf で選択（キャンセル可: 空のまま = リポジトリ全体）
  if [[ ${#files[@]} -eq 0 ]] && fzf_available; then
    _gf_pick_paths files || files=()
  fi

  local command=("git" "log" "--date=format-local:${GL_DATE_FORMAT}" "--pretty=format:${PRETTY_FORMAT}")
  if [[ ${#flags[@]} -gt 0 ]]; then
    command+=("${flags[@]}")
  fi
  if [[ ${#files[@]} -gt 0 ]]; then
    command+=("--" "${files[@]}")
  fi

  local cmd_str
  printf -v cmd_str '%q ' "${command[@]}"
  echo_yellow "${cmd_str% }"
  "${command[@]}"
}
