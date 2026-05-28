#!/bin/bash

#MISE description="APM CLI が利用可能であることを確認する"
#MISE quiet=true
#MISE hide=true

if ! command -v apm &>/dev/null; then
  printf "%b%s%b%s\n" "\033[1;31m" "✘ Error" "\033[0m" ": APM CLI is not installed or not in PATH." >&2
  printf "%s%b%s%b%s\n" "  See " "\033[1;34m" \
    "https://microsoft.github.io/apm/quickstart/" "\033[0m" " to install APM CLI:" >&2
  exit 1
fi
