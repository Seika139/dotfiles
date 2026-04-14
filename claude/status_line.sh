#!/bin/bash
# shellcheck disable=SC2154

# Claude Code のステータスライン表示スクリプト
# 公式ドキュメント: https://code.claude.com/docs/ja/statusline
# 参考: https://dev.classmethod.jp/articles/claude-code-statusline-context-usage-display/

# 色付けヘルパー関数
# 基本色（ANSI 16色）
red() { printf '\e[31m%s\e[0m' "$*"; }
green() { printf '\e[32m%s\e[0m' "$*"; }
yellow() { printf '\e[33m%s\e[0m' "$*"; }
blue() { printf '\e[34m%s\e[0m' "$*"; }
magenta() { printf '\e[35m%s\e[0m' "$*"; }
cyan() { printf '\e[36m%s\e[0m' "$*"; }
# スタイル
dim() { printf '\e[2m%s\e[0m' "$*"; }
bold() { printf '\e[1m%s\e[0m' "$*"; }
# RGB カスタムカラー（引数: R G B テキスト）
rgb() {
  local r=$1 g=$2 b=$3
  shift 3
  printf '\e[38;2;%d;%d;%dm%s\e[0m' "$r" "$g" "$b" "$*"
}
# よく使うカスタムカラー
orange() { rgb 250 180 100 "$*"; }
soft_green() { rgb 150 255 200 "$*"; }
soft_blue() { rgb 160 190 255 "$*"; }
pink() { rgb 255 150 200 "$*"; }

# Fine Bar + Gradient 表示関数
# 使用率(0-100)を受け取り、色付きバー + パーセント表示を返す
# バー幅: 7セル、緑→黄→赤のグラデーション
fine_bar() {
  local pct=${1:-0}
  local width=7
  local bar_chars=(▏ ▎ ▍ ▌ ▋ ▊ ▉ █)
  local filled_units=$((pct * width * 8 / 100))
  local full_blocks=$((filled_units / 8))
  local partial=$((filled_units % 8))
  local empty=$((width - full_blocks - (partial > 0 ? 1 : 0)))
  local result=""

  # 使用率に応じた色（緑→黄→赤グラデーション）
  local r g b
  if [ "$pct" -le 50 ] 2>/dev/null; then
    # 緑(80,220,100) → 黄(240,220,80)
    r=$((80 + (240 - 80) * pct / 50))
    g=220
    b=$((100 + (80 - 100) * pct / 50))
  else
    # 黄(240,220,80) → 赤(255,60,60)
    local p=$((pct - 50))
    r=$((240 + (255 - 240) * p / 50))
    g=$((220 + (60 - 220) * p / 50))
    b=$((80 + (60 - 80) * p / 50))
  fi

  # バー構築
  local i
  for ((i = 0; i < full_blocks; i++)); do
    result+="${bar_chars[7]}"
  done
  if [ "$partial" -gt 0 ]; then
    result+="${bar_chars[$((partial - 1))]}"
  fi
  for ((i = 0; i < empty; i++)); do
    result+=" "
  done

  printf '\e[38;2;%d;%d;%dm%s\e[0m' "$r" "$g" "$b" "$result"
}

# レートリミットのリセット時刻を残り時間に変換
reset_remaining() {
  local resets_at=$1
  if [ -z "$resets_at" ]; then
    echo "?"
    return
  fi
  local now
  now=$(date +%s)
  local diff=$((resets_at - now))
  if [ "$diff" -le 0 ]; then
    echo "now"
    return
  fi
  local hours=$((diff / 3600))
  local mins=$(((diff % 3600) / 60))
  if [ "$hours" -gt 0 ]; then
    printf '%d:%02d' "$hours" "$mins"
  else
    printf '%d' "$mins"
  fi
}

# 標準入力からJSON形式のデータを読み込む
input=$(cat)

# 各種情報を一括取得（jq呼び出しを最小化）
eval "$(echo "$input" | jq -r '
  @sh "model=\(.model.display_name // "Claude")",
  @sh "model_id=\(.model.id // "")",
  @sh "version=\(.version // "")",
  @sh "input_tokens=\(.context_window.total_input_tokens // "0")",
  @sh "output_tokens=\(.context_window.total_output_tokens // "0")",
  @sh "used=\(.context_window.used_percentage // "0")",
  @sh "cost_usd=\(.cost.total_cost_usd // "0")",
  @sh "duration_ms=\(.cost.total_duration_ms // "0")",
  @sh "lines_added=\(.cost.total_lines_added // "0")",
  @sh "lines_removed=\(.cost.total_lines_removed // "0")",
  @sh "current_dir=\(.workspace.current_dir // "unknown")",
  @sh "project_dir=\(.workspace.project_dir // "unknown")",
  @sh "rl_5h_used=\(.rate_limits.five_hour.used_percentage // "")",
  @sh "rl_5h_resets=\(.rate_limits.five_hour.resets_at // "")",
  @sh "rl_7d_used=\(.rate_limits.seven_day.used_percentage // "")",
  @sh "rl_7d_resets=\(.rate_limits.seven_day.resets_at // "")"
')"

# コンテキスト使用率の色分け（Fine Bar + 数値）
used_int=${used%.*}
used_bar=$(fine_bar "$used_int")
if [ "$used_int" -ge 80 ] 2>/dev/null; then
  used_pct=$(red "${used_int}%")
elif [ "$used_int" -ge 50 ] 2>/dev/null; then
  used_pct=$(yellow "${used_int}%")
else
  used_pct=$(green "${used_int}%")
fi

# モデル別コスト閾値（USD）
# Opus: 高単価のため低め / Sonnet: 中間 / Haiku: 安価のため低め
case "$model_id" in
*opus*)
  cost_lv_1=5.00
  cost_lv_2=10.00
  cost_lv_3=15.00
  cost_lv_4=20.00
  cost_lv_5=30.00
  cost_lv_6=40.00
  ;;
*haiku*)
  cost_lv_1=0.15
  cost_lv_2=0.30
  cost_lv_3=0.45
  cost_lv_4=0.60
  cost_lv_5=0.80
  cost_lv_6=1.00
  ;;
*)
  cost_lv_1=0.60
  cost_lv_2=1.20
  cost_lv_3=1.80
  cost_lv_4=2.40
  cost_lv_5=3.20
  cost_lv_6=4.00
  ;; # Sonnet 等
esac

# コストの色分け（awk 1回で判定）
cost_fmt=$(printf '$%.2f' "$cost_usd")
cost_level=$(awk "BEGIN {
  c=$cost_usd
  if      (c >= $cost_lv_6) print 6
  else if (c >= $cost_lv_5) print 5
  else if (c >= $cost_lv_4) print 4
  else if (c >= $cost_lv_3) print 3
  else if (c >= $cost_lv_2) print 2
  else if (c >= $cost_lv_1) print 1
  else print 0
}")
# 水色 → 青紫 → 紫 → マゼンタ → 赤のグラデーション
case "$cost_level" in
0) cost_colored=$(rgb 100 200 255 "$cost_fmt") ;; # 水色
1) cost_colored=$(rgb 120 150 255 "$cost_fmt") ;; # 青
2) cost_colored=$(rgb 150 120 255 "$cost_fmt") ;; # 青紫
3) cost_colored=$(rgb 180 100 240 "$cost_fmt") ;; # 紫
4) cost_colored=$(rgb 220 80 180 "$cost_fmt") ;;  # マゼンタ
5) cost_colored=$(rgb 250 60 100 "$cost_fmt") ;;  # 赤寄りピンク
6) cost_colored=$(rgb 255 40 40 "$cost_fmt") ;;   # 赤
esac

# セッション経過時間（分:秒）
duration_sec=$((duration_ms / 1000))
duration_min=$((duration_sec / 60))
duration_s=$((duration_sec % 60))
duration_fmt=$(printf '%dm %02ds' "$duration_min" "$duration_s")

# コード変更量の色付け
lines_changed=""
if [ "$lines_added" -gt 0 ] || [ "$lines_removed" -gt 0 ]; then
  lines_changed="$(green "+${lines_added}") $(red "-${lines_removed}")"
fi

# 日時
current_date=$(date '+%Y-%m-%d')
current_time=$(date '+%H:%M')

# Git 情報の取得
git_info=""
if cd "$current_dir" 2>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null; then
  branch_name=$(git branch --show-current 2>/dev/null || echo "detached")
  git_info="$(orange "($branch_name")"

  # uncommitted changes
  uc=""
  if [[ -n $(git status -s 2>/dev/null) ]]; then
    uc="$(yellow '*')"
  fi

  # commits ahead
  # shellcheck disable=SC1083
  ahead=$(git rev-list '@{u}..HEAD' 2>/dev/null | wc -l | tr -d ' ')
  ah=""
  if [[ $ahead -gt 0 ]]; then
    ah+="$(green "+$ahead")"
  fi
  if [[ -n "$uc$ah" ]]; then
    git_info+=" "
  fi
  git_info+="${uc}${ah}$(orange ")")"
fi

# ホームディレクトリを ~ に短縮（表示用。cd 等で使った後に変換する）
project_dir="${project_dir/#$HOME/\~}"
current_dir="${current_dir/#$HOME/\~}"

# ステータスライン表示
# Line 1: ctx + 5h + 7d（バー・使用率・リセット時刻）
line1="$(cyan ctx:) ${used_bar} ${used_pct}"
if [ -n "$rl_5h_used" ]; then
  rl_5h_int=${rl_5h_used%.*}
  rl_5h_bar=$(fine_bar "$rl_5h_int")
  rl_5h_reset=$(reset_remaining "$rl_5h_resets")
  if [ "$rl_5h_int" -ge 80 ] 2>/dev/null; then
    rl_5h_pct=$(red "${rl_5h_int}%")
  elif [ "$rl_5h_int" -ge 50 ] 2>/dev/null; then
    rl_5h_pct=$(yellow "${rl_5h_int}%")
  else
    rl_5h_pct=$(green "${rl_5h_int}%")
  fi
  line1+=" $(dim '|') $(cyan '5h:') ${rl_5h_bar} ${rl_5h_pct} "
  line1+="$(soft_blue "${rl_5h_reset}")"
fi
if [ -n "$rl_7d_used" ]; then
  rl_7d_int=${rl_7d_used%.*}
  rl_7d_bar=$(fine_bar "$rl_7d_int")
  rl_7d_reset=$(reset_remaining "$rl_7d_resets")
  if [ "$rl_7d_int" -ge 80 ] 2>/dev/null; then
    rl_7d_pct=$(red "${rl_7d_int}%")
  elif [ "$rl_7d_int" -ge 50 ] 2>/dev/null; then
    rl_7d_pct=$(yellow "${rl_7d_int}%")
  else
    rl_7d_pct=$(green "${rl_7d_int}%")
  fi
  line1+=" $(dim '|') $(cyan '7d:') ${rl_7d_bar} ${rl_7d_pct} "
  line1+="$(soft_blue "${rl_7d_reset}")"
fi
printf '%b\n' "$line1"

# Line 2: コスト・トークン・コード変更量・モデル
line2="$(cyan cst:) ${cost_colored}"
line2+=" $(dim '|') $(cyan tkn:)"
line2+=" i:$(soft_green "${input_tokens}")"
line2+=" o:$(soft_green "${output_tokens}")"
if [ -n "$lines_changed" ]; then
  line2+=" $(dim '|') ${lines_changed}"
fi
line2+=" $(dim '|') $(soft_green "$model")"
line2+=" $(dim '|') $(soft_green "$version")"
printf '%b\n' "$line2"

# Line 3: プロジェクト・経過時間・日時
line3="$(cyan prj:) $(soft_blue "$project_dir")"
line3+=" $(dim '|') $(soft_blue "${duration_fmt}")"
line3+=" $(dim '|') $(soft_blue "${current_date} ${current_time}")"
printf '%b\n' "$line3"

# Line 4: cwd・ブランチ・Git状態
line4="$(cyan cwd:) $(soft_green "$current_dir")"
if [ -n "$git_info" ]; then
  line4+=" ${git_info}"
fi
printf '%b\n' "$line4"
