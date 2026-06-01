#!/usr/bin/env bash

# 未認証 GitHub API のレート制限 (60 req/h) を回避するため、gh の OAuth トークンを引き継ぐ。
# 共有 IP 配下で `mise install` の attestation 検証が 403 になる事象への対策。
# 値は keychain から都度取得するため、このファイルにトークン実体は残らない。
# gh が未インストール / 未ログインの環境では何もしない。
#
# bash/.bashrc は public → private の順に読むため、brew shellenv が走る前にこのファイルが
# 評価される。command -v gh では見つからないので、想定パスを順に探索する。
__gh_bin=""
for __cand in \
  "$(command -v gh 2>/dev/null)" \
  /opt/homebrew/bin/gh \
  /usr/local/bin/gh \
  "$HOME/.linuxbrew/bin/gh" \
  /home/linuxbrew/.linuxbrew/bin/gh; do
  if [[ -n "${__cand}" && -x "${__cand}" ]]; then
    __gh_bin="${__cand}"
    break
  fi
done

if [[ -n "${__gh_bin}" ]]; then
  __gh_token="$("${__gh_bin}" auth token 2>/dev/null)"
  [[ -n "${__gh_token}" ]] && export GITHUB_TOKEN="${__gh_token}"
  unset __gh_token
fi
unset __gh_bin __cand
