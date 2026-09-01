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

  # hold ファイルがあれば、指定バージョン以上の stable リリースが出るまで更新を保留する。
  # v1.2.1 が stable としてタグされ DB を未サポート schema へ勝手に移行した事故の再発防止。
  local hold_file="${HOME}/.local/state/bd-update.hold"
  if [ -f "$hold_file" ]; then
    local hold_ver
    hold_ver="$(head -n1 "$hold_file" | tr -d '[:space:]')"
    if [ -z "$hold_ver" ]; then
      printf "%s\n" "hold ファイルの内容が壊れています。hold を無視して更新処理を続行します。"
    elif [ "$(printf '%s\n%s\n' "$hold_ver" "$latest_ver" | sort -V | head -n1)" != "$hold_ver" ]; then
      printf "%s\n" "bd 更新は保留中です (v${hold_ver} 以上の stable リリース待ち、latest: v${latest_ver})。"
      return 0
    else
      rm -f "$hold_file"
      printf "%s\n" "bd 更新の保留を解除しました (v${latest_ver} が stable リリースされたため)。"
      if command -v gh >/dev/null 2>&1; then
        gh issue create --repo Seika139/alev \
          --title "bd 自動更新の hold を解除し v${latest_ver} へ更新する" \
          --body "$(
            cat <<EOF
hold（v1.3.0 以上の stable リリース待ち）が解除され、この後の daily 更新で bd が v${latest_ver} に置き換わります。

確認事項:
- [ ] 各リポジトリ（web-change-monitor / auto-invest / cookie-clicker）で \`bd list\` が正常動作すること（v1.3.0 は初回起動時に v53→v66 の guided migration が走ります）
- [ ] alev.service のログに bd 起因のエラーが無いこと
- [ ] 問題があれば \`~/.local/bin/bd\` を旧版に戻し hold ファイルを再作成すること

関連: https://github.com/Seika139/alev/issues/100
EOF
          )" >/dev/null 2>&1 || printf "%s\n" "通知 issue の作成に失敗しました（更新は継続）。"
      fi
    fi
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

# ccusage (pnpm global) を npm registry の最新版に更新する。
# bd と違い GitHub release ではなく npm registry 管理だが、グローバル JS は
# lifecycle script をデフォルトでブロックする pnpm で入れる方針のため pnpm add -g で更新する。
update_ccusage() {
  # 非対話起動 (cron 等) では PNPM_HOME 未設定で pnpm add -g が失敗するため補う。
  export PNPM_HOME="${PNPM_HOME:-${HOME}/.local/share/pnpm}"
  case ":${PATH}:" in
  *":${PNPM_HOME}:"*) ;;
  *) export PATH="${PNPM_HOME}:${PATH}" ;;
  esac

  if ! command -v pnpm >/dev/null 2>&1; then
    printf "%s\n" "pnpm が無いため ccusage 更新をスキップします。"
    return 1
  fi

  # 現在のバージョンを取得する（未導入なら空）。
  local current_ver=""
  if command -v ccusage >/dev/null 2>&1; then
    current_ver="$(ccusage --version 2>/dev/null |
      sed -n 's/^ccusage \([0-9][0-9.]*\).*/\1/p' | head -n1)"
  fi

  # registry の最新版を取得する。
  local latest_ver
  if ! latest_ver="$(pnpm view ccusage version 2>/dev/null)"; then
    printf "%s\n" "npm registry の取得に失敗しました。ccusage 更新をスキップします。"
    return 1
  fi
  if [ -z "$latest_ver" ]; then
    printf "%s\n" "最新バージョンの判定に失敗しました。ccusage 更新をスキップします。"
    return 1
  fi

  if [ "$current_ver" = "$latest_ver" ]; then
    printf "%s\n" "ccusage は最新です (${current_ver})。"
    return 0
  fi
  printf "%s\n" "ccusage を更新します: ${current_ver:-未導入} -> ${latest_ver}"

  # stdout は抑制しつつ、失敗時の stderr は残して原因を追えるようにする。
  if pnpm add -g "ccusage@${latest_ver}" >/dev/null; then
    printf "%s\n" "ccusage を ${latest_ver} に更新しました。"
  else
    printf "%s\n" "ccusage の更新に失敗しました。"
    return 1
  fi
}

printf "%b%s%b\n" "\\033[38;5;214m" "=== beads (bd) ===" "\\033[0m"
update_bd

printf "%b%s%b\n" "\\033[38;5;214m" "=== ccusage ===" "\\033[0m"
update_ccusage
