---
allowed-tools: Bash(gh issue view:*), Bash(gh issue close:*), Bash(gh issue edit:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh project:*), Bash(gh repo view:*), Bash(git switch:*), Bash(git pull:*), Bash(git branch:*), Bash(git push:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(make:*), Bash(mise:*), Bash(date:*), Bash(cat:*)
argument-hint: "<Issue 番号 or URL> [--repo <owner/repo>]"
description: "Issue のクローズ・動作確認・ブランチ片付けを行う"
---

# Close Issue

`/solve-issue` で作成した PR がマージされた後の動作確認・GitHub Projects 更新・ブランチ片付けを一連で行います。

## デフォルト設定

以下は設定ファイルから読み込まれたデフォルト値です。
引数で上書きされない場合、この値を使用してください。

```json
!`cat ~/.claude/custom-config/create-issue-config.json 2>/dev/null || echo '{"repo":"","labels":[],"assignee":"","status":"","done_status":"Done","start_date":"today"}'`
```

repo の指定がない場合、カレントリポジトリを対象とします。

`done_status` が設定ファイルに存在しない場合は `"Done"` をデフォルト値として使用してください。

## 引数のパースルール

```text
/close-issue <Issue 番号 or URL> [--repo <owner/repo>]
```

- 引数は必須（Issue 番号または GitHub Issue URL）
- `--repo`: 対象リポジトリを指定（省略時はデフォルト設定 → カレントリポジトリの順で決定）

### 例

```text
/close-issue 42
→ Issue #42 に紐づく PR のマージ確認 → 動作確認 → Projects 更新 → ブランチ片付け

/close-issue 42 --repo other-org/other-repo
→ other-org/other-repo の Issue #42 を対象に実行

/close-issue https://github.com/org/repo/issues/42
→ URL から Issue 番号とリポジトリを自動抽出して実行
```

---

## Step 1: Issue & PR 情報の取得

1. Issue の情報を取得する

   ```bash
   gh issue view {番号} --repo {repo} --json number,title,state,body,labels,assignees
   ```

2. Issue に紐づく PR を検出する

   ```bash
   gh pr list --repo {repo} --search "{Issue番号}" --state merged --json number,title,headRefName,state,mergedAt,url
   ```

   見つからない場合は `--state all` でも検索し、マージされていない PR があるか確認する。

3. 判定ロジック
   - マージ済み PR が見つかった場合 → 次のステップへ進む
   - PR が存在するがマージされていない場合 → ユーザーに状況を報告して中断する
   - PR が見つからない場合 → ユーザーに報告して中断する

---

## Step 2: 動作確認

1. デフォルトブランチを自動検出する

   ```bash
   gh repo view --repo {repo} --json defaultBranchRef --jq '.defaultBranchRef.name'
   ```

2. デフォルトブランチに切り替え、最新化する

   ```bash
   git switch {デフォルトブランチ}
   git pull
   ```

3. PR の変更内容をユーザーに提示する

   ```bash
   gh pr view {PR番号} --repo {repo} --json files,additions,deletions
   ```

4. テストタスクの確認と実行を提案する
   - `mise.toml` や `Makefile` にテストタスクが定義されている場合は、実行を提案する
   - テストが存在しない場合はスキップする

5. ユーザーに動作確認の結果を確認する
   - 問題がある場合は、対応方法をユーザーと相談する
   - 問題がない場合は次のステップへ進む

---

## Step 3: GitHub Projects 更新

1. Issue が追加されている Project を特定する

   ```bash
   gh project item-list --owner {owner} --format json | ...
   ```

   または Issue のメタデータから Project 情報を取得する。

2. **Status** を `done_status`（デフォルト: `"Done"`）に更新する

   ```bash
   gh project item-edit --project-id {project-id} --id {item-id} --field-id {status-field-id} --single-select-option-id {done-option-id}
   ```

3. **End Date** を今日の日付に設定する

   ```bash
   gh project item-edit --project-id {project-id} --id {item-id} --field-id {end-date-field-id} --date "$(date +%Y-%m-%d)"
   ```

   Projects に追加されていない場合や更新に失敗した場合は、ユーザーに報告してスキップする。

---

## Step 4: ブランチ片付け

1. PR の head ブランチ名を取得する（Step 1 で取得済み）
2. リモートの feature ブランチを削除する

   ```bash
   git push origin --delete {ブランチ名}
   ```

3. ローカルの feature ブランチを削除する

   ```bash
   git branch -d {ブランチ名}
   ```

   - リモートブランチが既に削除されている場合はスキップする
   - ローカルブランチが存在しない場合はスキップする
   - 削除前にユーザーに確認は不要（マージ済みのため安全に削除可能）

---

## Step 5: 報告

実行結果をユーザーに報告する。

```text
✅ Issue のクローズ処理が完了しました。

- Issue: {Issue URL}
- PR: {PR URL}（マージ済み）
- ブランチ: {ブランチ名}（削除済み）
- Projects: Status → {done_status}, End Date → {今日の日付}
```
