---
allowed-tools: Bash(gh issue create:*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh label list:*), Bash(gh project:*), Bash(gh api:*), Bash(date:*), Bash(cat:*)
argument-hint: "<Issue タイトル> [--repo <owner/repo>] [--label <label>] [--assignee <user>] [--status <status>]"
description: "Issue を起票する"
---

# Issue 起票スキル

## デフォルト設定

以下は設定ファイルから読み込まれたデフォルト値です。
引数で上書きされない場合、この値を使用してください。

```json
!`cat ~/.claude/custom-config/create-issue-config.json 2>/dev/null || echo '{"repo":"org/repo","project":{"owner":"","number":0,"status":"","done_status":"Done","start_date":"today"},"labels":[],"assignee":""}'`
```

もし `custom-config/create-issue-config.json` が存在しない場合は、ユーザーに以下の内容でファイルを作成するよう促してください。

```json
{
  "repo": "org/repo",
  "project": {
    "owner": "org-or-user-name",
    "number": 1,
    "status": "",
    "done_status": "Done",
    "start_date": "today"
  },
  "labels": [],
  "assignee": ""
}
```

- `repo`: Issue を起票するリポジトリ（形式: `owner/repo`）
- `project.owner`: GitHub Projects のオーナー（Organization 名またはユーザー名）
- `project.number`: GitHub Projects の番号
- `project.status`: Issue 起票時に設定する Status の値
- `project.done_status`: Issue クローズ時に設定する Status の値
- `project.start_date`: `"today"` の場合、起票時に今日の日付を Start Date に設定

## 引数のパースルール

`$ARGUMENTS` には以下の形式で値が渡されます。

```text
<Issue タイトル> [--repo <owner/repo>] [--label <label>] [--assignee <user>] [--status <status>]
```

- `--` で始まるフラグとその直後の値はオプションとして取り出す
- フラグに該当しない部分が Issue タイトルになる
- 指定されなかったオプションはデフォルト設定の値を使用する
- `--label` は複数回指定可能。1つでも指定された場合、デフォルトの labels は上書きされる

### 例

```text
/create-issue S3連携の配線を接続する
→ タイトル: "S3連携の配線を接続する", その他はデフォルト値

/create-issue バグ修正 --repo other/repo --label bug --label urgent
→ タイトル: "バグ修正", repo: "other/repo", labels: ["bug", "urgent"]

/create-issue 新機能追加 --assignee another-user --status Todo
→ タイトル: "新機能追加", assignee: "another-user", status: "Todo"
```

## Issue テンプレート

以下のテンプレートに従って Issue 本文を作成してください。

```markdown
## 概要

{ユーザーの指示内容や会話コンテキストに基づいて概要を記述}

## 完了条件

{ユーザーの指示内容に基づいて完了条件を記述}

## プルリク

（なし）

## 依頼元

（なし）
```

## 起票手順

1. `$ARGUMENTS` をパースし、タイトルとオプションを取り出す
2. デフォルト設定とマージする（引数で指定された値が優先）
3. ユーザーに概要と完了条件の内容を確認する。情報が不足している場合は質問する
4. 以下のコマンドで Issue を起票する

```bash
gh issue create \
  --repo {repo} \
  --title "{タイトル}" \
  --label "{label1}" --label "{label2}" \
  --assignee {assignee} \
  --body "$(cat <<'EOF'
## 概要

{概要}

## 完了条件

{完了条件}

## プルリク

（なし）

## 依頼元

（なし）
EOF
)"
```

1. 起票後、`project` 設定が存在する場合は GitHub Projects のフィールドを設定する
   - `project.owner` と `project.number` で対象の GitHub Project を特定する
   - **Status**: `project.status` の値に設定
   - **Start Date**: `project.start_date` が `today` の場合は `date +%Y-%m-%d` で今日の日付を取得して設定

   GitHub Projects のフィールド設定には `gh project` 関連サブコマンドを使用してください。
   プロジェクトの特定には `--owner {project.owner}` と プロジェクト番号 `{project.number}` を使用してください。

2. 会話のコンテキストから親 Issue が特定できる場合は、ユーザーに確認の上、親子関係を設定する

   ```bash
   # 親 Issue の node ID を取得
   gh issue view {親Issue番号} --repo {repo} --json id --jq '.id'

   # 子 Issue（今起票した Issue）を親に紐づけ
   gh api graphql -f query='
   mutation {
     addSubIssue(input: {
       issueId: "{親IssueのnodeID}"
       subIssueUrl: "{起票したIssueのURL}"
     }) {
       issue { number title }
       subIssue { number title }
     }
   }'
   ```

3. 起票した Issue の URL をユーザーに報告する
