---
allowed-tools: Bash(gh issue create:*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh label list:*), Bash(gh project:*), Bash(date:*), Bash(cat:*)
argument-hint: "<Issue タイトル> [--repo <owner/repo>] [--label <label>] [--assignee <user>] [--status <status>]"
description: "Issue を起票する"
---

# Issue 起票スキル

## デフォルト設定

以下は設定ファイルから読み込まれたデフォルト値です。
引数で上書きされない場合、この値を使用してください。

```json
!`cat ~/.claude/custom-config/create-issue-config.json 2>/dev/null || echo '{"repo":"org/repo","labels":[],"assignee":"","status":"","start_date":"today"}'`
```

もし `custom-config/create-issue-config.json` が存在しない場合は、ユーザーに以下の内容でファイルを作成するよう促してください。

```json
{
  "repo": "org/repo",
  "labels": [],
  "assignee": "",
  "status": "",
  "start_date": "today"
}
```

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

1. 起票後、GitHub Projects のフィールドを設定する
   - **Status**: 設定値（デフォルト: `In Progress`）に設定
   - **Start Date**: `start_date` が `today` の場合は `date +%Y-%m-%d` で今日の日付を取得して設定

   GitHub Projects のフィールド設定には `gh project` 関連サブコマンドを使用してください。

2. 起票した Issue の URL をユーザーに報告する
