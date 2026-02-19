---
allowed-tools: Bash(gh issue view:*), Bash(gh issue close:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(gh pr comment:*), Bash(gh project:*), Bash(gh repo view:*), Bash(git switch:*), Bash(git pull:*), Bash(git branch:*), Bash(git push:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(make:*), Bash(mise:*), Bash(date:*), Bash(cat:*)
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

2. Issue に紐づく PR と Issue に関連する Issue を検索する

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

## Step 3: 関連する Issue と PR の更新

### Step 3-1: Issue body から関連 Issue/PR を検出

Step 1 で取得済みの Issue body をパースし、関連する Issue・PR を抽出する。

1. Issue body 内の `#番号` や GitHub URL（`https://github.com/{owner}/{repo}/issues/{番号}` 等）、また Issue の Relationships を抽出する
   - コードブロック（` ``` ` で囲まれた部分）内の記述は除外する
2. 抽出した参照を以下のルールで分類する
   - Parent Issue: Relationships で Parent Issue として指定されているもの、または `## 依頼元` セクション内にある参照項目
   - Sub Issue: Relationships で Sub Issue として指定されているもの、または Issue 内で依頼先として明示的に記載されているもの（例: `- [ ] #123` などのタスクリスト形式）
   - **関連 Issue / 関連 PR**: それ以外のセクションにある参照
3. `#番号` が Issue か PR かの判定

   ```bash
   gh issue view {番号} --repo {repo} --json number 2>/dev/null
   # 失敗した場合
   gh pr view {番号} --repo {repo} --json number 2>/dev/null
   ```

4. 関連 Issue/PR が1件も見つからない場合は Step 3 全体をスキップする

### Step 3-2: メイン Issue の更新

本 Issue 自体の body を以下のように更新する。

a. タスクリストのチェック更新
b. `## プルリク` セクションの更新 → 作成された PR の URL を記載する

### Step 3-3: Parent Issue の更新

Parent Issue が存在する場合、その Issue body を以下のように更新する。Parent Issue が複数ある場合は、すべてのParent Issue に対して同様の更新を行う。

- Parent Issue 内に本 Issue への参照がある場合は、Step 3-2 と同様の更新を行う（タスクリストのチェック更新、`## プルリク` セクションの更新）
- Parent Issue 内に本 Issue への参照がない場合は、`## 関連 Issue` セクションを新たに作成し、そこに本 Issue への参照と PR URL を記載する
- Parent Issue に本 Issue で解決した内容と同等の内容であるチェックリストが存在する場合は、該当するチェックリスト項目をチェック済みに更新する

### Step 3-4: Sub Issue の更新

もし本 Issue に対して、未解決の Sub Issue が存在する場合は、Sub Issue の body を確認し、本 Issue だけをクローズしても問題ないかを判断する。
もし、Sub Issue の内容が本 Issue と密接に関連しており本 Issue のクローズと同時に Sub Issue もクローズすべきであると判断した場合は、Sub Issue にも Step 3-2 と同様の更新を行い、さらに Sub Issue 自体もクローズする。
逆に Sub Issue が未解決のまま本 Issue をクローズすることが不適切であると判断した場合は、ユーザーに確認を取る（例:「Sub Issue #123 は未解決ですが、本 Issue をクローズしてもよろしいですか？」）。

### Step 3-5: 関連 Issue の更新

上記以外の関連 Issue にコメントを投稿する。
body 更新に失敗した Parent Issue / Sub Issue にもフォールバックとしてコメントを投稿する。

```bash
gh issue comment {番号} --repo {repo} --body "🔗 関連 Issue #{番号} ({タイトル}) がクローズされました。
- PR: {PR URL}"
```

- `{番号}` と `{タイトル}` はクローズした Issue の情報
- `{PR URL}` は Step 1 で取得した紐づく PR の URL

### Step 3-6: 関連 PR にコメント

関連 PR に対して特筆すべき内容がある場合は、関連 PR にもコメントを投稿する。

```bash
gh pr comment {番号} --repo {repo} --body "コメント"
```

- `{番号}` と `{タイトル}` はクローズした Issue の情報

### エッジケース

- Parent Issue / Sub Issue や関連する Issue/PR が複数ある場合 → すべてに対して同様の更新を行う
- Parent Issue / Sub Issue や関連する Issue/PR がない場合はその項目の処理はスキップする
- API エラー → 報告してスキップ（後続処理は継続）
- `## プルリク` に同じ PR が既にある → 追記しない

## Step 4: GitHub Projects 更新

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

## Step 5: ブランチ片付け

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
- 関連更新: {更新した親Issue・コメントした Issue/PR の一覧}（該当なしの場合は「なし」）
```
