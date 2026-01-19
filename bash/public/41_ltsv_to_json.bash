#!/bin/bash

# LTSV を JSON に変換するメソッドたち
# 上に記載してあるものほど高速・推奨

# 使い方
# 1. パイプから標準入力として渡す場合
# 例: grep 'id:123' http.ltsv | ltsv_to_json > output.json
# 例: echo -e "id:1\thost:local" | ltsv_to_json

# 2. ファイルからリダイレクトで渡す場合
# 例: ltsv_to_json < http.ltsv > output.json

ltsv_to_json_jq() {
  cat | jq -R -r '
    split("\t")
    | map(
        capture("(?<k>[^:]+):(?<v>.*)")
        | {(.k): .v}
      )
    | add
  ' | jq -s '.'
}

ltsv_to_json_awk() {
  awk -F'\t' '
  BEGIN {
    print "["
  }
  {
    # 2行目以降の処理の前にカンマを追加
    if (NR > 1) { print "," }

    printf "  {"
    for (i = 1; i <= NF; i++) {
      # 最初の ":" で分割（値の中に ":" が含まれるケースに対応）
      pos = index($i, ":")
      if (pos > 0) {
        key = substr($i, 1, pos - 1)
        val = substr($i, pos + 1)

        # JSONのダブルクォートをエスケープ（簡易版）
        gsub(/"/, "\\\"", val)

        printf "\"%s\": \"%s\"%s", key, val, (i == NF ? "" : ", ")
      }
    }
    printf "}"
  }
  END {
    print "\n]"
  }
  '
}

ltsv_to_json_fast() {
  echo '['
  local first_line=true
  IFS=$'\n'
  while read -r line; do
    local first=true
    if [ "$first_line" = false ]; then
      echo ','
    fi
    echo '{'
    IFS=$'\t' read -ra pairs <<<"$line"
    for pair in "${pairs[@]}"; do
      IFS=":" read -r key value <<<"$pair"
      if [[ $value == "{"* ]]; then
        if [ "$first" = true ]; then
          printf '  "%s": %s' "$key" "$value"
          first=false
        else
          echo ","
          printf '  "%s": %s' "$key" "$value"
        fi
      else
        if [ "$first" = true ]; then
          printf '  "%s": "%s"' "$key" "$value"
          first=false
        else
          echo ","
          printf '  "%s": "%s"' "$key" "$value"
        fi
      fi
    done
    first_line=false
    echo
    echo -n '}'
  done
  echo
  echo -n ']'
}

ltsv_to_json() {
  echo '['
  local first_line=true
  while IFS=$'\n' read -ra line; do
    local first=true
    if [ $first_line == false ]; then
      echo ','
    fi
    echo '{'
    IFS=$'\t' read -ra pairs <<<"$line"
    for pair in "${pairs[@]}"; do
      IFS=":" read key value <<<"$pair"
      if [[ $value == "{"* ]]; then
        if [ $first == true ]; then
          echo -n "  \"$key\": $value"
          first=false
        else
          echo ","
          echo -n "  \"$key\": $value"
        fi
      else
        if [ $first == true ]; then
          echo -n "  \"$key\": \"$value\""
          first=false
        else
          echo ","
          echo -n "  \"$key\": \"$value\""
        fi
      fi
    done
    first_line=false
    echo
    echo -n '}'
  done
  echo
  echo -n ']'
}
