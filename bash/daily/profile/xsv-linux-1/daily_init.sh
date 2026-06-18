#!/usr/bin/env bash
#
# xsv-linux-1 profile の日次処理。
# このマシンは ~/.local/bin 直置きをツールの流儀にしているため、
# mise/brew に頼らず GitHub release から直接 bd を更新する。
# 将来ツールが増えたらこのファイルに追記する。

set -uo pipefail

# beads (bd) を GitHub release の最新版に更新する。
# checksums.txt で sha256 検証してから ~/.local/bin/bd を atomic に置換する。
update_bd() {
  local repo="gastownhall/beads"
  local install_path="${HOME}/.local/bin/bd"

  if ! command -v curl >/dev/null 2>&1; then
    printf "%s\n" "curl が無いため bd 更新をスキップします。"
    return 1
  fi

  # GitHub API はレート制限があるため token があれば添える（任意）。
  local -a curl_auth=()
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    curl_auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi

  # 最新リリースの tag を取得する。
  local api_json latest_tag latest_ver
  if ! api_json="$(curl -fsSL "${curl_auth[@]}" "https://api.github.com/repos/${repo}/releases/latest")"; then
    printf "%s\n" "GitHub API の取得に失敗しました。bd 更新をスキップします。"
    return 1
  fi
  latest_tag="$(printf '%s\n' "$api_json" |
    sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)"
  latest_ver="${latest_tag#v}"
  if [ -z "$latest_ver" ]; then
    printf "%s\n" "最新バージョンの判定に失敗しました。bd 更新をスキップします。"
    return 1
  fi

  # 現在のバージョンを取得する（未導入なら空）。
  local current_ver=""
  if command -v bd >/dev/null 2>&1; then
    current_ver="$(bd version 2>/dev/null |
      sed -n 's/^bd version \([0-9][0-9.]*\).*/\1/p' | head -n1)"
  fi

  if [ "$current_ver" = "$latest_ver" ]; then
    printf "%s\n" "bd は最新です (${current_ver})。"
    return 0
  fi
  printf "%s\n" "bd を更新します: ${current_ver:-未導入} -> ${latest_ver}"

  # arch を release の asset 命名に合わせる。
  local arch
  case "$(uname -m)" in
  x86_64 | amd64) arch="amd64" ;;
  aarch64 | arm64) arch="arm64" ;;
  *)
    printf "%s\n" "未対応の arch: $(uname -m)。bd 更新をスキップします。"
    return 1
    ;;
  esac

  local asset="beads_${latest_ver}_linux_${arch}.tar.gz"
  local base="https://github.com/${repo}/releases/download/${latest_tag}"

  local tmp
  if ! tmp="$(mktemp -d)"; then
    printf "%s\n" "一時ディレクトリの作成に失敗しました。"
    return 1
  fi
  # shellcheck disable=SC2064
  trap "rm -rf '${tmp}'" RETURN

  if ! curl -fsSL "${curl_auth[@]}" -o "${tmp}/${asset}" "${base}/${asset}"; then
    printf "%s\n" "アセットのダウンロードに失敗しました: ${asset}"
    return 1
  fi
  if ! curl -fsSL "${curl_auth[@]}" -o "${tmp}/checksums.txt" "${base}/checksums.txt"; then
    printf "%s\n" "checksums.txt のダウンロードに失敗しました。"
    return 1
  fi

  # sha256 検証（検証できない環境では更新しない fail-closed）。
  if ! command -v sha256sum >/dev/null 2>&1; then
    printf "%s\n" "sha256sum が無いため検証できません。bd を更新しません。"
    return 1
  fi
  if ! (cd "$tmp" && grep -E "[[:space:]]${asset}\$" checksums.txt | sha256sum -c - >/dev/null 2>&1); then
    printf "%s\n" "チェックサム検証に失敗しました。bd を更新しません。"
    return 1
  fi

  # 展開して bd バイナリを取り出す。
  if ! tar -xzf "${tmp}/${asset}" -C "$tmp"; then
    printf "%s\n" "アセットの展開に失敗しました。"
    return 1
  fi
  local extracted
  extracted="$(find "$tmp" -type f -name bd | head -n1)"
  if [ -z "$extracted" ]; then
    printf "%s\n" "展開物に bd が見つかりません。"
    return 1
  fi

  # 検証済みバイナリを atomic に置換する。
  chmod +x "$extracted"
  mkdir -p "$(dirname "$install_path")"
  if mv -f "$extracted" "$install_path"; then
    printf "%s\n" "bd を ${latest_ver} に更新しました。"
  else
    printf "%s\n" "bd の置換に失敗しました。"
    return 1
  fi
}

printf "%b%s%b\n" "\\033[38;5;214m" "=== beads (bd) ===" "\\033[0m"
update_bd
