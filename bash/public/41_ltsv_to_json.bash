#!/bin/bash

# LTSV を JSON に変換する
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

# 使い方
# ltsv_json "input" > output
# ltsv_json < file > output
