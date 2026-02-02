#!/usr/bin/env bash

monitor_stacks() {
  local cmd
  local query_conditions=""

  # 複数の引数を||で結合したcontains条件を構築
  for stack_name in "$@"; do
    if [[ -n "$query_conditions" ]]; then
      query_conditions="$query_conditions || contains(StackName, \\\`$stack_name\\\`)"
    else
      query_conditions="contains(StackName, \\\`$stack_name\\\`)"
    fi
  done
  if [[ ! -z "$query_conditions" ]]; then
    query_conditions="?$query_conditions"
  fi

  cmd="aws cloudformation describe-stacks \
    --profile dev_base_read_only \
    --region ap-northeast-1 \
    --output json \
    --query \"Stacks[$query_conditions][StackName, StackStatus, CreationTime, LastUpdatedTime]\" \
    |  jq -r \".[] | @tsv\" | column -t | grep -v '_COMPLETE '"
  cmd_compressed=$(echo "$cmd" | tr -s ' ')
  echo "Executing command: $cmd_compressed"
  watch -n 20 "$cmd_compressed"
}

# Usage example:
# monitor_stacks: 全スタックについて監視
# monitor_stacks service-product-env another-stack-name: or条件で特定のスタックを監視
