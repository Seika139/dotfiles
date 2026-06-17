#!/bin/bash

REMOTE_URL=$(git remote get-url origin 2>/dev/null) || {
  echo "ERROR: current directory is not a git repository with origin remote" >&2
  exit 1
}

case "$REMOTE_URL" in
https://github.com/*)
  REPO_PATH=${REMOTE_URL#https://github.com/}
  ;;
git@github.com:*)
  REPO_PATH=${REMOTE_URL#git@github.com:}
  ;;
ssh://git@github.com/*)
  REPO_PATH=${REMOTE_URL#ssh://git@github.com/}
  ;;
*)
  echo "ERROR: origin remote is not a github.com repository: $REMOTE_URL" >&2
  exit 1
  ;;
esac

REPO_PATH=${REPO_PATH%.git}
OWNER=${REPO_PATH%%/*}
REPO=${REPO_PATH#*/}

if [[ -z "$OWNER" || -z "$REPO" || "$OWNER" == "$REPO_PATH" ]]; then
  echo "ERROR: failed to parse owner/repo from origin remote: $REMOTE_URL" >&2
  exit 1
fi

h1() { printf "%b%s%b\n" "\033[38;5;205m" "$1" "\033[0m"; }
h2() { printf "%b%s%b\n" "\033[38;5;86m" "$1" "\033[0m"; }

h1 "GitHub Security Settings チェック"
printf "%s%b%s%b\n" "対象リポジトリ: " "\033[38;5;86m" "$OWNER/$REPO" "\033[0m"
printf "%s%b%s%b\n" "origin remote URL: " "\033[38;5;86m" "$REMOTE_URL" "\033[0m"
echo

usage() {
  cat <<USAGE
Usage: $(basename "$0") [section...]

Sections:
  auth         gh token の OAuth scope を見る
  repo         repo の security 設定だけを見る。引数なしのデフォルト
  code         Code Security / Code scanning / CodeQL を見る
  secret       Secret Protection を見る
  dependabot   Dependabot / Dependency graph を見る
  org          org / enterprise 側の強制設定を見る
  billing      課金対象 committer を見る
  all          すべて見る

Environment:
  GH_CACHE=1h    gh api のキャッシュ時間。デフォルトは 1h
  GH_CACHE=none  gh api のキャッシュを使わない

Examples:
  $(basename "$0")
  $(basename "$0") auth
  $(basename "$0") code secret
  $(basename "$0") all
USAGE
}

declare -A ENABLED=()

enable_section() {
  case "$1" in
  auth | repo | code | secret | dependabot | org | billing)
    ENABLED["$1"]=1
    ;;
  all)
    ENABLED[auth]=1
    ENABLED[repo]=1
    ENABLED[code]=1
    ENABLED[secret]=1
    ENABLED[dependabot]=1
    ENABLED[org]=1
    ENABLED[billing]=1
    ;;
  -h | --help | help)
    usage
    exit 0
    ;;
  *)
    echo "ERROR: unknown section: $1" >&2
    usage >&2
    exit 1
    ;;
  esac
}

section_enabled() {
  [[ -n "${ENABLED[$1]:-}" ]]
}

if [[ $# -eq 0 ]]; then
  enable_section repo
else
  for section in "$@"; do
    enable_section "$section"
  done
fi

GH_CACHE=${GH_CACHE:-1h}

gh_api() {
  if [[ "$GH_CACHE" == "none" ]]; then
    gh api "$@"
  else
    gh api --cache "$GH_CACHE" "$@"
  fi
}

REPO_JSON=
AUTH_RESPONSE=

cleanup() {
  if [[ -n "${REPO_JSON:-}" && -f "$REPO_JSON" ]]; then
    rm -f "$REPO_JSON"
  fi
  if [[ -n "${AUTH_RESPONSE:-}" && -f "$AUTH_RESPONSE" ]]; then
    rm -f "$AUTH_RESPONSE"
  fi
}
trap cleanup EXIT

repo_json() {
  command -v jq >/dev/null 2>&1 || {
    echo "ERROR: jq is required to reuse repo API response" >&2
    exit 1
  }

  if [[ -z "${REPO_JSON:-}" ]]; then
    REPO_JSON=$(mktemp)
    gh_api "repos/$OWNER/$REPO" >"$REPO_JSON" || exit 1
  fi
}

repo_jq() {
  repo_json
  jq "$1" "$REPO_JSON"
}

repo_jq_raw() {
  repo_json
  jq -r "$1" "$REPO_JSON"
}

auth_response() {
  if [[ -z "${AUTH_RESPONSE:-}" ]]; then
    AUTH_RESPONSE=$(mktemp)
    gh api user -i >"$AUTH_RESPONSE" || exit 1
  fi
}

oauth_scopes() {
  auth_response
  awk '
    BEGIN { IGNORECASE = 1 }
    /^x-oauth-scopes:/ {
      sub(/^[^:]*:[[:space:]]*/, "")
      sub(/\r$/, "")
      print
      exit
    }
  ' "$AUTH_RESPONSE"
}

has_oauth_scope() {
  local scope=$1

  oauth_scopes |
    tr "," "\n" |
    sed "s/^[[:space:]]*//;s/[[:space:]]*$//" |
    grep -Fxq "$scope"
}

show_auth_scope() {
  local scopes

  h2 "gh token の OAuth scope:"
  scopes=$(oauth_scopes)

  if [[ -z "$scopes" ]]; then
    echo "X-OAuth-Scopes: unavailable"
    echo "admin:org: unknown"
    echo "fine-grained token や GitHub App token では OAuth scope header だけでは判定できない場合があります。"
    return
  fi

  echo "X-OAuth-Scopes: $scopes"

  if has_oauth_scope "admin:org"; then
    echo "admin:org: present"
  else
    echo "admin:org: missing"
    echo "classic gh token なら必要に応じて: gh auth refresh -s admin:org"
  fi
}

if section_enabled auth; then
  h1 "0. GitHub auth"
  show_auth_scope
fi

if section_enabled repo; then
  h1 "1. 全体入口: repo の security 設定"
  # gh api repos/$OWNER/$REPO --jq '.security_and_analysis'
  repo_jq_raw '
    if .security_and_analysis == null then
      "security_and_analysis\t\tunavailable"
    else
      .security_and_analysis | to_entries[] | "\(.key)\t\t\(.value.status // .value)"
    end
  ' | column -t
fi

if section_enabled code; then
  h1 "2. Code Security / Code scanning / CodeQL"

  echo
  h2 "2-1. Code Security の repo-level 状態:"
  repo_jq '(.security_and_analysis // {}).code_security // "unavailable"'

  echo
  h2 "2-2. Code scanning default setup の状態:"
  gh_api "repos/$OWNER/$REPO/code-scanning/default-setup" --jq .

  echo
  h2 "2-3. Code scanning alerts が使えるか:"
  gh_api "repos/$OWNER/$REPO/code-scanning/alerts?per_page=1" --jq .

  echo
  h2 "2-4. Actions 側に dynamic CodeQL / Code Quality があるかを見る:"
  gh_api "repos/$OWNER/$REPO/actions/workflows" --jq '.workflows[] | select(.path | test("codeql|code-scanning|code-quality"; "i")) | {name,path,state,id}'
fi

if section_enabled secret; then
  h1 "3. Secret Protection"

  echo
  h2 "3-1. 主要状態"
  repo_jq '
    if .security_and_analysis == null then
      "unavailable"
    else
      {
        secret_scanning: .security_and_analysis.secret_scanning.status,
        push_protection: .security_and_analysis.secret_scanning_push_protection.status,
        ai_detection: .security_and_analysis.secret_scanning_ai_detection.status,
        non_provider_patterns: .security_and_analysis.secret_scanning_non_provider_patterns.status,
        validity_checks: .security_and_analysis.secret_scanning_validity_checks.status,
        delegated_bypass: .security_and_analysis.secret_scanning_delegated_bypass.status,
        delegated_alert_dismissal: .security_and_analysis.secret_scanning_delegated_alert_dismissal.status
      }
    end
  '

  echo
  h2 "3-2. 実際に alerts が読めるか:"
  gh_api "repos/$OWNER/$REPO/secret-scanning/alerts?per_page=5" --jq 'map({number,state,secret_type,validity,created_at})'

  echo
  h2 "3-3. Custom patterns は権限や org 設定に依存しますが、見るなら:"
  gh_api "repos/$OWNER/$REPO/secret-scanning/custom-patterns" --jq .
  gh_api "orgs/$OWNER/secret-scanning/custom-patterns" --jq .
fi

if section_enabled dependabot; then
  h1 "4. Dependabot"

  echo "Dependabot alerts が有効かは HTTP status で見るのが確実です。"

  gh_api "repos/$OWNER/$REPO/vulnerability-alerts" -i

  echo "204 No Content なら Dependabot alerts 有効です。"

  h2 "Dependabot security updates:"

  gh_api "repos/$OWNER/$REPO/automated-security-fixes" --jq .

  h2 "Dependabot alerts の実データ:"

  gh_api "repos/$OWNER/$REPO/dependabot/alerts?per_page=10" --jq 'map({number,state,dependency:.dependency.package.name,ecosystem:.dependency.package.ecosystem,severity:.security_advisory.severity})'

  h2 "Dependency graph / SBOM が取れるか:"

  gh_api "repos/$OWNER/$REPO/dependency-graph/sbom" --jq '{name:.sbom.name, packages:(.sbom.packages|length)}'

  h2 "Dependabot version updates は API の on/off というより .github/dependabot.yml の有無と内容で確認します。"

  gh_api "repos/$OWNER/$REPO/contents/.github/dependabot.yml" --jq '.content' | base64 -d

  h2 "ローカル repo なら単に:"

  sed -n '1,240p' .github/dependabot.yml
fi

if section_enabled org; then
  h1 "5. org / enterprise 側の強制設定"

  show_auth_scope

  h2 "repo に適用されている Code Security configuration:"

  gh_api "repos/$OWNER/$REPO/code-security-configuration" --jq .

  h2 "org の security configurations 一覧:"

  gh_api "orgs/$OWNER/code-security/configurations" --jq .

  echo "これは admin:org や security manager 相当がないと 403/404 になりがちです。"
fi

if section_enabled billing; then
  h1 "6. 課金対象 committer の確認"

  show_auth_scope

  h2 "billing 権限があるなら:"
  echo "これは通常 admin:org 以上が必要です。今回の手元トークンでは権限不足で見えませんでした。"

  gh_api "orgs/$OWNER/settings/billing/advanced-security?advanced_security_product=secret_protection"
  gh_api "orgs/$OWNER/settings/billing/advanced-security?advanced_security_product=code_security"
fi
