---
name: respond-to-pr-reviews
description: "Pull Request にぶら下がったレビューコメント（人間・bot 問わず）を順番に捌き、妥当性判断 → 修正コード or 説明返信 → commit/push → 返信コメント → resolve conversation までを完走させるスキル。「PR のレビュー対応して」「PR #123 のコメントを全部捌いて」「まだ resolve されてないスレッドを片付けて」「CodeRabbit / Gemini のレビュー対応」といった依頼で必ず使う。単にコードを直して push するだけでは不十分で、各スレッドに対して「返信を残してから resolve する」ところまで含めて完走させる点が重要。PR が更新された後に新しいレビューが付いた場合も、skill 側でループして最後まで対応する。"
---

# PR レビュー対応スキル

Pull Request に付いたレビューコメントに対して、**妥当性判断 → 対応 → 返信 → resolve** の 1 サイクルを、全スレッドが片付くまでループするスキル。

## なぜこのスキルがあるのか

普通にコードを直して push するだけだと、以下のような見落としが起きる：

- **コード修正はしたが、スレッドに返信を残さない** → レビュアーは「見てくれた？」となる
- **コード修正はしたが、resolve されない** → 特に Gemini など自動 resolve しない bot で発生。PR 上が未解決スレッドだらけになる
- **対応不要と判断したがコメントしない** → レビュアーに理由が伝わらない
- **修正後に新しいレビューが付いたのに気づかない** → CI が追加レビューをトリガーする環境で発生

このスキルは上記を「必ず全スレッド resolve する」「必ず返信を残す」という workflow で防ぐ。

## 前提条件

- `gh` CLI が認証済み
- 対象リポジトリへの write 権限
- カレントブランチに対応する PR が存在する（または PR 番号が明示されている）

## ワークフロー概要

```
┌───────────────────────────────────────────┐
│ 1. 対象 PR を特定                          │
│ 2. 未 resolve のレビュースレッドを列挙     │
│ 3. 各スレッドに対して:                     │
│    a. 妥当性判断                           │
│    b-1. 妥当 → 修正 → commit → push        │
│    b-2. 不要 → 理由を明確化                │
│    c. スレッドに返信コメント               │
│    d. resolveReviewThread で resolve       │
│ 4. 再度スレッド一覧を取得                  │
│    新規レビューがあれば 2. に戻る          │
│    無ければ完了                            │
└───────────────────────────────────────────┘
```

## ステップ詳細

### 1. 対象 PR を特定

ユーザーが PR 番号を指定していればそれを使う。指定がなければカレントブランチから特定する。

```bash
# 引数で指定された場合
PR_NUMBER=13

# カレントブランチから特定（このコマンドは現ブランチの PR を返す）
PR_NUMBER=$(gh pr view --json number --jq '.number')
```

特定できなかったら skill を終了し、ユーザーに「対象 PR を教えてください」と聞く。

### 2. 未 resolve スレッドを列挙

**重要**: `gh pr view --comments` は body しか返さず `isResolved` を含まない。必ず GraphQL の `reviewThreads` を使う。

```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 10) {
            nodes {
              author { login }
              body
              createdAt
              url
            }
          }
        }
      }
    }
  }
}'
```

そして `isResolved == false` のスレッドだけを処理対象にする。`isOutdated` は無視する（コードが変わっていても会話は未解決というケースが多い）。

### 3. 各スレッドを処理

#### 3a. 妥当性判断

コメント本文を読み、以下のどれに該当するかを判断する：

| 判定 | 基準 | アクション |
|---|---|---|
| **Major / Critical** | アーキテクチャ変更、API 破壊、依存追加、ユーザー体験に影響する挙動変更 | **必ずユーザーに確認**してから進める |
| **Minor / Nit** | typo、ドキュメント微修正、コメント、軽い refactor、ログ改善 | 自律的に判断して OK |
| **不要** | 既に別の方法で解決済み、既存の設計意図と合わない、誤読による指摘 | 理由を明文化してユーザーに確認 |

bot レビューでは本文先頭に priority / severity (🔴 Major, 🟡 Minor など) が書かれていることが多いので、判断の一次情報にする。

#### 3b-1. 妥当 → 修正 → commit → push

1. 指摘箇所を `Read` で確認
2. `Edit` で修正
3. テスト・lint を実行（プロジェクトの方法を自動検出。例: `mise run test`、`uv run pytest`、`npm test`、`cargo test` など）
   - 失敗したら修正を続ける。ユーザー判断が必要なら一度止める
4. 関連する FB を 1 コミットにまとめる（独立性が高ければ分ける）
5. commit メッセージは日本語で簡潔に書く。**「〜のレビュー対応」だけではなく、何を直したかを書く**
   - 悪い例: `"PR レビュー対応"`
   - 良い例: `"hook のタイムアウトと OSError ハンドリングを追加"`
6. `git push` で同一ブランチに push

#### 3b-2. 修正不要 → 理由を明確化

以下のどれかに当てはまることを確認：

- 既存の設計意図と矛盾する（「この実装は意図的」）
- 別の場所で既に解決済み（「〜の箇所で対応済み」）
- コストに見合わない（「影響範囲が小さく、修正コストと釣り合わない」）
- 誤読による指摘（「このコードは実際には〜なので問題ない」）

必ず**具体的な理由**を用意する。定型文「問題ありません」では伝わらない。

#### 3c. スレッドに返信コメント

**これが一番抜けやすいステップ**。修正した場合でも、不要と判断した場合でも、必ず返信を残す。

返信は `gh api` でスレッドに対して post する：

```bash
# review comment に reply するには、元コメントの id が必要
gh api --method POST \
  "repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_ID/replies" \
  -f body="..."
```

返信の書き方：

| 状況 | 返信例 |
|---|---|
| 修正した | `ご指摘ありがとうございます。〜の commit (SHA) で対応しました。` + 補足 |
| 修正不要 | `ご指摘ありがとうございます。〜の理由でこの実装を維持します。` |
| 部分対応 | `〜の部分は反映しました。〜は別 PR で扱います（理由: XXX）。` |

#### 3d. resolveReviewThread で resolve

**`gh` CLI には resolve コマンドが無い**ので、GraphQL で叩く。`scripts/resolve_thread.sh` を使うか、以下を直接実行：

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread { isResolved }
  }
}' -f threadId="$THREAD_ID"
```

返り値が `isResolved: true` になっていることを確認する。

### 4. 新規レビューの検知 → ループ

push すると CI 経由で新しい bot レビューが付くことがある（CodeRabbit は push 毎に再レビューする）。全スレッドを resolve した後、もう一度 Step 2 のクエリを叩いて、未 resolve スレッドが増えていないか確認する。

- 増えていたら → Step 3 に戻る
- 増えていなかったら → 完了報告（「N 件のスレッドを resolve しました」）

無限ループ防止のため、**同じ内容のレビューが繰り返し付く場合は 2 周目で止めてユーザーに相談する**。

## 重要な注意点

### GraphQL 必須の操作

以下は `gh` CLI のサブコマンドが無いため、GraphQL 経由で叩く必要がある：

- `reviewThreads` の取得（`isResolved` を含む）
- `resolveReviewThread` mutation
- `unresolveReviewThread` mutation

`scripts/resolve_thread.sh` と `scripts/list_unresolved_threads.sh` に便利スクリプトを用意してある。

### bot の違い

| bot | 修正後の自動 resolve | 備考 |
|---|---|---|
| CodeRabbit | ✅ 自動で resolve してくれる | `fix committed` のような返信にすると resolve する |
| Gemini Code Assist | ❌ 自動 resolve しない | 必ず明示的に resolve する |
| CodeX | 状況による | 様子を見つつ明示 resolve を推奨 |
| 人間レビュアー | ❌ レビュアー自身が resolve するのが本来の流儀 | 返信だけして resolve は相手に任せるのが無難な場合もある |

**人間レビュアーのコメントに対しては、返信を残した後 resolve するかはユーザーに確認する**。自分から resolve すると「ちゃんと議論が終わったの？」という印象を与えることがある。

### push 後の CI レース

push 直後に CI が走り始め、新しい bot レビューが数分後に付くことがある。Step 4 のループでスレッドを再取得するタイミングは、push から少なくとも 1〜2 分は待つのが良い。待たない場合は「CI 完走後に再チェック」とユーザーに伝えて一旦止める。

### 既に別 Claude が対応している場合

たまに「別のセッションが同じ PR を触っている」ことがある。最初に `git log origin/<branch> -5` でリモートの最新コミットを確認し、**自分のローカル作業より先に進んでいたら一度 pull してから判断する**。diverged なら skill を止めてユーザーに報告。

## 完了報告の形式

skill 完走時は以下を報告する：

```
## PR #N レビュー対応完了

- 処理したスレッド数: X
  - 修正対応: Y スレッド (commit SHA の一覧)
  - 修正不要: Z スレッド (判断理由付き)
- 追加 push: N commits
- 未 resolve 残: 0 件 (または「人間レビュアー N 件は返信のみ、resolve は相手に委ねる」)
- CI 状況: ALL GREEN / 〜 待ち
```

## 参考スクリプト

- `scripts/list_unresolved_threads.sh <pr-number>` — 未 resolve スレッドを JSON で出力
- `scripts/resolve_thread.sh <thread-id>` — スレッドを resolve
- `scripts/reply_to_thread.sh <comment-id> <body>` — スレッドに返信

これらは GraphQL / gh api のラッパー。直接呼んでも良い。
