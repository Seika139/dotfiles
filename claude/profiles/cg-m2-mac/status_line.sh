#!/bin/bash

# Claude Code のステータスライン表示スクリプト
# 公式ドキュメント: https://code.claude.com/docs/ja/statusline
# 参考: https://dev.classmethod.jp/articles/claude-code-statusline-context-usage-display/

# 標準入力からJSON形式のデータを読み込む
input=$(cat)

# 各種情報を取得
model=$(echo "$input" | jq -r '.model.display_name // "Claude"')
input_tokens=$(echo "$input" | jq -r '.context_window.total_input_tokens // "0"')
output_tokens=$(echo "$input" | jq -r '.context_window.total_output_tokens // "0"')
duration_ms=$(echo "$input" | jq -r '.cost.total_api_duration_ms // "0"')

# コンテキスト使用率の計算
# context_size=$(echo "$input" | jq -r '.context_window.context_window_size')
# usage=$(echo "$input" | jq '.context_window.current_usage')
# if [ "$usage" != "null" ]; then
#   current_tokens=$(echo "$usage" | jq '.input_tokens + .cache_creation_input_tokens + .cache_read_input_tokens')
#   percent_used=$((current_tokens * 100 / context_size))
# else
#   percent_used="0"
# fi

# 上記の方法は以下のように簡略化可能
used=$(echo "$input" | jq -r '.context_window.used_percentage // "0"')

# レイテンシを秒に変換（小数点1桁）
latency=$(echo "$duration_ms" | awk '{printf "%.1f\n", $1 / 1000}')
if [ -z "$latency" ]; then
  latency="-"
else
  latency="${latency}s"
fi

# ディレクトリ情報
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // "unknown"')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir // "unknown"')

# ステータスライン表示
echo "Context: ${used}% used | Tokens in: ${input_tokens} / out: ${output_tokens} | Total API Latency: ${latency} | ${model}"
echo "Project dir: ${project_dir} | Current dir: ${current_dir}"
