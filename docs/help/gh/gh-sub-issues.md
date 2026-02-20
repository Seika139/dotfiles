# gh api graphql: Sub-issues (親子 Issue)

GitHub の Sub-issues 機能を GraphQL API で操作する方法。
REST API (`gh issue view --json`) では parent/subIssues は取得できないため、`gh api graphql` を使う必要がある。

## 前提: カレントディレクトリに依存しない

`gh api graphql` はクエリ内の `repository(owner, name)` で対象リポジトリを指定するため、**どのディレクトリからでも実行可能**。
`gh issue view` のようにカレントディレクトリの git リモートから推定する仕組みはない。

```bash
# 例: dotfiles リポジトリにいても task_management の Issue を操作できる
~/dotfiles $ gh api graphql -f query='{ repository(owner: "org", name: "repo") { issue(number: 1) { title } } }'
```

## 取得

### parent と subIssues を一括取得

```bash
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    issue(number: {番号}) {
      id
      number
      title
      state
      url
      parent {
        id
        number
        title
        state
        url
        body
        repository { nameWithOwner }
      }
      subIssues(first: 50) {
        totalCount
        nodes {
          id
          number
          title
          state
          url
          repository { nameWithOwner }
        }
      }
    }
  }
}'
```

- `parent`: 単一オブジェクト。親がない場合は `null`
- `subIssues`: Connection 型。ページネーション対応
- `repository.nameWithOwner`: クロスリポジトリの親子関係にも対応

### ページネーション（subIssues が 50 件以上ある場合）

```bash
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    issue(number: {番号}) {
      subIssues(first: 50, after: "{endCursor}") {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          number
          title
          state
        }
      }
    }
  }
}'
```

`pageInfo.hasNextPage` が `true` の間、`endCursor` を `after` に渡して繰り返す。

## 設定

### 親子関係を追加（addSubIssue）

```bash
# Issue URL で指定する方法（node ID 不要で手軽）
gh api graphql -f query='
mutation {
  addSubIssue(input: {
    issueId: "{親IssueのnodeID}"
    subIssueUrl: "https://github.com/{owner}/{repo}/issues/{番号}"
  }) {
    issue { number title }
    subIssue { number title }
  }
}'
```

```bash
# node ID で指定する方法
gh api graphql -f query='
mutation {
  addSubIssue(input: {
    issueId: "{親IssueのnodeID}"
    subIssueId: "{子IssueのnodeID}"
  }) {
    issue { number title }
    subIssue { number title }
  }
}'
```

- `issueId`（必須）: 親 Issue の node ID
- `subIssueId` または `subIssueUrl`: 子 Issue の指定（どちらか一方）
- `replaceParent`: `true` にすると既存の親を置き換える

### 親子関係を削除（removeSubIssue）

```bash
gh api graphql -f query='
mutation {
  removeSubIssue(input: {
    issueId: "{親IssueのnodeID}"
    subIssueId: "{子IssueのnodeID}"
  }) {
    issue { number title }
    subIssue { number title }
  }
}'
```

## node ID の取得方法

```bash
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    issue(number: {番号}) {
      id       # => "I_kwDO..." のような文字列
      number
      title
    }
  }
}'
```

`gh issue view` でも取得可能:

```bash
gh issue view {番号} --repo {owner}/{repo} --json id --jq '.id'
```
