#!/usr/bin/env bash

# ────────────────────────────────────────────
# fzf でインタラクティブな選択を行うための関数群
# 他のソースコードにコピペできるように、他のファイルに依存するコードは書かない
# ────────────────────────────────────────────

# stdin が端末に接続されているかを判定する。
# fzf のようなインタラクティブ UI を起動してよいかの判定に使う。
# fzf は /dev/tty を直接開いて描画するため、stdout がパイプ（コマンド置換）でも動作する。
# よって stdin だけ確認すれば十分。
require_stdin_tty() {
  if [ ! -t 0 ]; then
    echo "Error: This function requires a TTY." >&2
    return 1
  fi
}

# fzf が利用可能かを確認する。なければ案内を stderr に出して非ゼロで終了する。
require_fzf() {
  if ! command -v fzf >/dev/null 2>&1; then
    echo "fzf が見つかりません。サブコマンドを引数で指定してください。" >&2
    return 1
  fi
}

# Yes/No を fzf で選ばせる。選択されなければ非ゼロで終了（キャンセル扱い）。
# 使い方: if binary_choice "本当に実行しますか？"; then ...
binary_choice() {
  local res
  res=$(printf "Yes\nNo\n" | fzf --height 6 --border --prompt "${1:-選択}: ")
  if [ -z "$res" ]; then
    return 1
  fi
  echo "$res" | grep -iq "^yes$"
}

# ────────────────────────────────────────────
# 選択肢から1つを選択させる関数
# ecs で選択肢から選ばなかった場合は、空文字を返す
# 引数: 選択肢の配列（タブ区切りにすると、選択肢と説明を分けられる）
#      --prompt | -p: プロンプトを指定（デフォルト: "選択肢から1つを選択 > "）
#      --preview | -v: プレビューに表示するコマンド（デフォルト: 'printf "\033[38;5;214m%s\033[0m\n" {2..}'）
#      --preview-window | -w: fzf の --preview-window オプションの値（デフォルト: 'down,3,wrap'）
#      --: 選択肢の配列の開始を示す。これ以降の引数はすべて選択肢として扱われる。
# 戻り値: 選択された選択肢のテキスト（タブ区切りの1列目）
# 例:
#   options=(
#     $'option1\t説明1'
#     $'option2\t説明2'
#   )
#   selected=$(select_one "${options[@]}")
#   echo "Selected: $selected"
# ────────────────────────────────────────────
select_one_or_zero() {
  require_stdin_tty || return 1
  require_fzf || return 1

  local options=()
  local prompt="選択肢から1つを選択 > "
  local preview='printf "\033[38;5;214m%s\033[0m\n" {2..}'
  local preview_window='down,3,wrap'
  while [ $# -gt 0 ]; do
    case "$1" in
    --prompt | -p)
      prompt="$2"
      shift 2
      ;;
    --preview | -v)
      preview="$2"
      shift 2
      ;;
    --preview-window | -w)
      preview_window="$2"
      shift 2
      ;;
    --)
      shift
      options+=("$@")
      break
      ;;
    *)
      options+=("$1")
      shift
      ;;
    esac
  done

  if [ ${#options[@]} -eq 0 ]; then
    echo "選択肢が提供されていません" >&2
    return 1
  fi

  local selected
  selected=$(
    printf '%s\n' "${options[@]}" |
      fzf --prompt "$prompt" \
        --delimiter=$'\t' \
        --with-nth=1 \
        --color='prompt:75,pointer:211,marker:84,header:italic:245,hl:84,hl+:84:reverse' \
        --bind='tab:toggle+down,shift-tab:toggle+up,ctrl-/:toggle-preview' \
        --pointer='▶' \
        --marker='✓ ' \
        --header="$(
          printf '%b%s%b' '\033[34m' 'Tab ' '\033[0m'
          echo -n '選択切替 / '
          printf '%b%s%b' '\033[34m' 'Shift+Tab ' '\033[0m'
          echo -n '選択切替（逆へ移動）/ '
          printf '%b%s%b' '\033[34m' 'ESC ' '\033[0m'
          echo -n '選択なしで続行 / '
          printf '%b%s%b' '\033[34m' 'Ctrl+/ ' '\033[0m'
          echo -n 'preview 切替'
        )" \
        --preview "$preview" \
        --preview-window="$preview_window"
  ) || selected=""
  printf '%s\n' "$selected" | cut -d$'\t' -f1
}

# ────────────────────────────────────────────
# 選択肢から1つを選択させる関数
# ecs で選択肢から選ばなかった場合は非ゼロで終了する
# 引数: 選択肢の配列（タブ区切りにすると、選択肢と説明を分けられる）
# 戻り値: 選択された選択肢のテキスト（タブ区切りの1列目）
# 例:
#   options=(
#     $'option1\t説明1'
#     $'option2\t説明2'
#   )
#   selected=$(select_one "${options[@]}")
#   echo "Selected: $selected"
# ────────────────────────────────────────────
select_one() {
  local selected
  selected=$(select_one_or_zero "$@") || return 1
  if [ -z "$selected" ]; then
    echo "選択されませんでした" >&2
    return 1
  fi
  printf '%s\n' "$selected"
}

# ────────────────────────────────────────────
# 選択肢から複数を選択させる関数
# ecs で選択肢から選ばなかった場合は空文字を返す
# 引数: 選択肢の配列（タブ区切りにすると、選択肢と説明を分けられる）
#      --prompt | -p: プロンプトを指定（デフォルト: "選択肢から複数を選択 > "）
#      --preview | -v: プレビューに表示するコマンド（デフォルト: 'printf "\033[38;5;214m%s\033[0m\n" {2..}'）
#      --preview-window | -w: fzf の --preview-window オプションの値（デフォルト: 'down,3,wrap'）
#      --: 選択肢の配列の開始を示す。これ以降の引数はすべて選択肢として扱われる。
# 戻り値: 選択された選択肢のテキスト（タブ区切りの1列目）を改行区切りで返す
# 例:
#   options=(
#     $'option1\t説明1'
#     $'option2\t説明2'
#   )
#   # 配列として受け取る場合は mapfile を使うとよい
#   mapfile -t selected < <(select_multi "${options[@]}")
#   printf 'Selected:\n%s\n' "${selected[@]}"
# ────────────────────────────────────────────
select_multi_or_zero() {
  require_stdin_tty || return 1
  require_fzf || return 1

  local options=()
  local prompt="選択肢から複数を選択 > "
  local preview='printf "\033[38;5;214m%s\033[0m\n" {2..}'
  local preview_window='down,3,wrap'
  while [ $# -gt 0 ]; do
    case "$1" in
    --prompt | -p)
      prompt="$2"
      shift 2
      ;;
    --preview | -v)
      preview="$2"
      shift 2
      ;;
    --preview-window | -w)
      preview_window="$2"
      shift 2
      ;;
    --)
      shift
      options+=("$@")
      break
      ;;
    *)
      options+=("$1")
      shift
      ;;
    esac
  done

  if [ ${#options[@]} -eq 0 ]; then
    echo "選択肢が提供されていません" >&2
    return 1
  fi
  local selected
  selected=$(
    printf '%s\n' "${options[@]}" |
      fzf --multi \
        --prompt "$prompt" \
        --delimiter=$'\t' \
        --with-nth=1 \
        --color='prompt:75,pointer:211,marker:84,header:italic:245,hl:84,hl+:84:reverse' \
        --bind='tab:toggle+down,shift-tab:toggle+up,ctrl-a:toggle-all,ctrl-d:deselect-all,ctrl-/:toggle-preview' \
        --pointer='▶' \
        --marker='✓ ' \
        --header="$(
          printf '%b%s%b' '\033[34m' 'Tab ' '\033[0m'
          echo -n '選択切替 / '
          printf '%b%s%b' '\033[34m' 'Shift+Tab ' '\033[0m'
          echo -n '選択切替（逆へ移動）/ '
          printf '%b%s%b' '\033[34m' 'ESC ' '\033[0m'
          echo -n 'フラグなしで続行 / '
          printf '%b%s%b' '\033[34m' 'Ctrl+A ' '\033[0m'
          echo -n '全選択 / '
          printf '%b%s%b' '\033[34m' 'Ctrl+D ' '\033[0m'
          echo -n '全解除 / '
          printf '%b%s%b' '\033[34m' 'Ctrl+/ ' '\033[0m'
          echo -n 'preview 切替'
        )" \
        --preview "$preview" \
        --preview-window="$preview_window"
  ) || selected=""

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    printf '%s\n' "${line%%$'\t'*}"
  done <<<"$selected"
}

# ────────────────────────────────────────────
# 選択肢から複数を選択させる関数
# ecs で選択肢から選ばなかった場合は非ゼロで終了する
# 引数: 選択肢の配列（タブ区切りにすると、選択肢と説明を分けられる）
# 戻り値: 選択された選択肢のテキスト（タブ区切りの1列目）を改行区切りで返す
# 例:
#   options=(
#     $'option1\t説明1'
#     $'option2\t説明2'
#   )
#   # 配列として受け取る場合は mapfile を使うとよい
#   mapfile -t selected < <(select_multi "${options[@]}")
#   printf 'Selected:\n%s\n' "${selected[@]}"
# ────────────────────────────────────────────
select_multi() {
  local selected
  selected=$(select_multi_or_zero "$@") || return 1

  if [ -z "$selected" ]; then
    echo "選択されませんでした" >&2
    return 1
  fi

  printf '%s\n' "$selected"
}

# ────────────────────────────────────────────
# 動作確認用のサンプルコード
# bash bash/public/61_fzf.bash を直接実行して動作確認できます
# ────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Running fzf selection sample..."
  sample_ops=(
    $'alpha\toption Alpha'
    $'beta\toption Beta'
    $'gamma\toption Gamma'
  )
  printf '%s%b%s%b\n' 'Selected from select_one: ' '\033[34m' \
    "$(select_one "${sample_ops[@]}" -v '')" '\033[0m'

  echo "Selected from select_multi:"
  mapfile -t selected < <(
    select_multi "$(fd --max-depth 2 .)" \
      --preview-window 'right,60%,wrap' \
      --preview 'printf "\033[1;33m── 選択対象a ──\033[0m\n"
        printf "  %s\n" {+}
        printf "\n\033[1;36m── ファイル/ディレクトリ ──\033[0m\n"
        if [[ -f {} ]]; then
          bat --color=always --style=full --line-range :120 {}
        else
          eza --tree --color=always {}
        fi'
  )
  for sel in "${selected[@]}"; do
    printf '%s%b%s%b\n' '- ' '\033[34m' "$sel" '\033[0m'
  done
fi
