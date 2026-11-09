#!/usr/bin/env bash

# 未認証 GitHub API のレート制限 (60 req/h) を回避するため、gh の OAuth トークンを引き継ぐ。
# 共有 IP 配下で `mise install` の attestation 検証が 403 になる事象への対策。
# 値は keychain から都度取得するため、このファイルにトークン実体は残らない。
# gh が未インストール / 未ログインの環境では何もしない。
#
# bash/.bashrc は public → private の順に読み、brew shellenv と mise activate より先に
# このファイルが評価されるため、Homebrew と mise の実体パスも探索する。
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

__gh_token=""
if [[ -n "${__gh_bin}" ]]; then
  __gh_token="$("${__gh_bin}" auth token 2>/dev/null)"
fi

if [[ -z "${__gh_token}" ]]; then
  __mise_bin=""
  for __cand in \
    "$(command -v mise 2>/dev/null)" \
    /opt/homebrew/bin/mise \
    /usr/local/bin/mise \
    "$HOME/.local/bin/mise"; do
    if [[ -n "${__cand}" && -x "${__cand}" ]]; then
      __mise_bin="${__cand}"
      break
    fi
  done

  if [[ -n "${__mise_bin}" ]]; then
    __mise_gh_dir="$("${__mise_bin}" -C "$HOME" where gh 2>/dev/null)"
    if [[ -n "${__mise_gh_dir}" && -x "${__mise_gh_dir}/bin/gh" ]]; then
      __gh_bin="${__mise_gh_dir}/bin/gh"
      __gh_token="$("${__gh_bin}" auth token 2>/dev/null)"
    fi
  fi
fi

[[ -n "${__gh_token}" ]] && export GITHUB_TOKEN="${__gh_token}"
unset __gh_token
unset __gh_bin __mise_bin __mise_gh_dir __cand
