#!/usr/bin/env bash

# GitHub CLI の補完を有効化する
if command -v gh &>/dev/null; then
  eval "$(gh completion -s bash)"
fi

# =============================================================================
# GitHub CLI ログイン・認証関連エイリアス
# =============================================================================
alias gal='gh auth login'  # GitHub CLI ログイン
alias gas='gh auth status' # GitHub CLI 認証ステータス確認

# =============================================================================
# GitHub CLI ブランチ保護・ルールセット関連エイリアス
# =============================================================================
# 依存コマンド:
#   - gh  : GitHub CLI (https://cli.github.com/)
#   - jq  : JSON パーサー (https://stedolan.github.io/jq/)
# =============================================================================

# -----------------------------------------------------------------------------
# _gh_current_repo - 現在のリポジトリ名を取得（内部ヘルパー関数）
# -----------------------------------------------------------------------------
# 使い方:
#   repo=$(_gh_current_repo)
# 戻り値:
#   "owner/repo" 形式のリポジトリ名
#   リポジトリ外では空文字を返す
# -----------------------------------------------------------------------------
_gh_current_repo() {
  gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null
}

# -----------------------------------------------------------------------------
# gh-branch-rules - ブランチ保護ルールとルールセットのサマリを表示
# -----------------------------------------------------------------------------
# 使い方:
#   gh-branch-rules              # 現在のリポジトリ
#   gh-branch-rules owner/repo   # 指定したリポジトリ
# 出力:
#   - Legacy Protection: main ブランチの従来型保護ルール
#   - Rulesets: リポジトリに設定されたルールセット一覧
# -----------------------------------------------------------------------------
gh-branch-rules() {
  local repo="${1:-$(_gh_current_repo)}"
  if [[ -z "$repo" ]]; then
    echo "Error: Not in a git repository or repository not specified"
    return 1
  fi

  echo "=== Branch Protection Rules for ${repo} ==="
  echo ""
  echo "--- Legacy Protection ---"
  gh api "repos/${repo}/branches/main/protection" 2>/dev/null |
    jq '{
          required_reviews: .required_pull_request_reviews.required_approving_review_count,
          dismiss_stale_reviews: .required_pull_request_reviews.dismiss_stale_reviews,
          require_code_owners: .required_pull_request_reviews.require_code_owner_reviews,
          required_status_checks: .required_status_checks.contexts,
          enforce_admins: .enforce_admins.enabled
        }' || echo "No legacy branch protection configured"

  echo ""
  echo "--- Rulesets ---"
  gh api "repos/${repo}/rulesets" --jq '.[] | "[\(.enforcement)] \(.name) (ID: \(.id))"' 2>/dev/null ||
    echo "No rulesets found"
}

# -----------------------------------------------------------------------------
# gh-rulesets - ルールセットの一覧と各ルールセットの詳細を表示
# -----------------------------------------------------------------------------
# 使い方:
#   gh-rulesets              # 現在のリポジトリ
#   gh-rulesets owner/repo   # 指定したリポジトリ
# 出力:
#   各ルールセットについて以下を表示:
#   - 名前と enforcement 状態（active/disabled/evaluate）
#   - ターゲット（branch/tag）
#   - 対象ブランチパターン
#   - 適用されているルール一覧
# -----------------------------------------------------------------------------
gh-rulesets() {
  local repo="${1:-$(_gh_current_repo)}"
  if [[ -z "$repo" ]]; then
    echo "Error: Not in a git repository or repository not specified"
    return 1
  fi

  echo "=== Rulesets for ${repo} ==="
  echo ""

  gh api "repos/${repo}/rulesets" --jq '.[].id' 2>/dev/null | while read -r id; do
    gh api "repos/${repo}/rulesets/${id}" 2>/dev/null | jq -r '
        "## \(.name) [\(.enforcement)]",
        "Target: \(.target)",
        "Branches: \(.conditions.ref_name.include | join(", "))",
        "Rules:",
        (.rules[] | "  - \(.type)"),
        ""
      '
  done || echo "Failed to fetch rulesets. Check your repository name and permissions."
}

# -----------------------------------------------------------------------------
# gh-ruleset-detail - 特定のルールセットの詳細情報を JSON 形式で表示
# -----------------------------------------------------------------------------
# 使い方:
#   gh-ruleset-detail 12345              # 現在のリポジトリで、ルールセットIDを指定
#   gh-ruleset-detail owner/repo 12345   # リポジトリとルールセットIDを指定
# 引数:
#   引数が1つ（数字）の場合: ルールセットID
#   引数が2つの場合: $1=リポジトリ名, $2=ルールセットID
#   ルールセットIDは gh-branch-rules で確認可能
# 出力:
#   - name: ルールセット名
#   - enforcement: 適用状態
#   - target: 対象（branch/tag）
#   - conditions: 対象ブランチパターン
#   - rules: 各ルールとそのパラメータ
# -----------------------------------------------------------------------------
gh-ruleset-detail() {
  local repo ruleset_id

  # 引数が1つで数字の場合は ruleset_id とみなす
  if [[ $# -eq 1 && "$1" =~ ^[0-9]+$ ]]; then
    repo="$(_gh_current_repo)"
    ruleset_id="$1"
  else
    repo="${1:-$(_gh_current_repo)}"
    ruleset_id="${2:?Ruleset ID is required}"
  fi

  if [[ -z "$repo" ]]; then
    echo "Error: Not in a git repository or repository not specified"
    return 1
  fi

  gh api "repos/${repo}/rulesets/${ruleset_id}" 2>/dev/null |
    jq '{name, enforcement, target, conditions: .conditions.ref_name, rules: [.rules[] | {type, parameters}]}'
}
