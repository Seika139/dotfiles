---
name: "gh-link-subissues"
description: "GitHub Issue に Sub-issue を紐付けます。クロスリポジトリ対応。親 Issue の URL/番号と、子 Issue の URL/番号リストを指定してください。"
---

# GitHub Sub-issue 紐付けスキル

親 Issue に1つ以上の子 Issue を Sub-issue として紐付けます。
異なるリポジトリ間（クロスリポジトリ）でも紐付け可能です。

## 前提条件

- `gh` CLI がインストール・認証済みであること
- 対象リポジトリへのアクセス権があること

## 入力

ユーザーから以下の情報を収集してください：

- **親 Issue**: `owner/repo#number` 形式または GitHub URL
- **子 Issue（1つ以上）**: `owner/repo#number` 形式または GitHub URL のリスト

## 手順

### Step 1: Issue の Node ID を取得

各 Issue の Node ID を GitHub GraphQL API で取得します。
同一リポジトリの Issue はエイリアスを使って1回の API コールでまとめて取得できます。

```bash
# 単一 Issue の Node ID 取得
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) { id title }
  }
}' -f owner="OWNER" -f repo="REPO" -F number=NUMBER \
  -q '.data.repository.issue.id'
```

```bash
# 同一リポジトリの複数 Issue をエイリアスで一括取得
gh api graphql -f query='
query {
  repository(owner: "OWNER", name: "REPO") {
    i1: issue(number: 10) { id title }
    i2: issue(number: 20) { id title }
  }
}' -q '.data.repository'
```

### Step 2: addSubIssue mutation で紐付け

取得した Node ID を使い、各子 Issue を親 Issue に紐付けます。

```bash
gh api graphql -f query='
mutation($parent: ID!, $child: ID!) {
  addSubIssue(input: {issueId: $parent, subIssueId: $child}) {
    issue { id title }
    subIssue { id title }
  }
}' -f parent="PARENT_NODE_ID" -f child="CHILD_NODE_ID"
```

子 Issue が複数ある場合は、それぞれに対して mutation を実行してください。

### Step 3: 結果の確認

紐付けが成功したら、親 Issue と子 Issue のタイトルを表示して結果を報告してください。

## 注意事項

- `-f` は文字列パラメータ、`-F` は数値パラメータに使う（`number` は `Int!` 型なので `-F`）
- `-q` は jq フィルタで結果から特定フィールドを抽出する
- Node ID は `I_kwDO` で始まるグローバルに一意な識別子
- 既に紐付け済みの場合はエラーが返る
