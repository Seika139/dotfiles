---
name: "respond-pr"
description: "PR のレビューコメントに対して、妥当性判断・修正・返信・resolveReviewThread まで完走させる。Claude command /respond-pr 相当を Codex CLI で実行する。"
metadata:
  short-description: "PR のレビューコメントに対して、妥当性判断・修正・返信・resolveReviewThread まで完走させる"
---

<!-- codex-profile-generated-from-prompt: prompts/respond-pr.md -->

# respond-pr

この skill は Claude command `/respond-pr` から変換した Codex 用 command skill です。

## Codex での呼び出し

Codex CLI では `/respond-pr` ではなく、`$respond-pr` または `/skills` からこの skill を呼び出してください。
引数は `$respond-pr` の後ろに自然文として続けます。

```text
$respond-pr <arguments>
```

元 prompt 内の `$ARGUMENTS` や slash command 表記は、`$respond-pr` の後ろに書かれた引数として解釈してください。
Claude 専用の `allowed-tools` メタデータや `!` command interpolation は Codex では自動適用されないため、必要な情報は通常の shell command で確認してください。

## 元 prompt

## Respond to PR Reviews

Pull Request のレビュースレッドを順番に捌き、**返信コメント投稿 + `resolveReviewThread` GraphQL mutation** まで完走させるコマンド。

このコマンドは `~/.codex/skills/respond-to-pr-reviews/` スキルのエントリーポイント。**必ずスキルの `SKILL.md` を最初に読み、その手順に従う**。ここで手順を重複記載しない（スキル本体の更新が常に真実）。

### 引数

- 第 1 引数（省略可）: PR 番号 or URL。例: `42` / `https://github.com/org/repo/pull/42`
- 省略時: `gh pr view --json number --jq '.number'` でカレントブランチの PR を取得

### 必ず守る原則（`SKILL.md` のエッセンス）

1. **`reviewThreads` GraphQL で未 resolve を取得**する（`gh pr view --comments` では `isResolved` が取れない）
2. **bot の指摘を鵜呑みにしない**。`npm view` などで現行版を独立検証してから判断する
3. **完走条件**: 各スレッドに対して
   - 妥当性判断（Major は原則ユーザー確認、Minor は自律判断）
   - 修正 or 明示的な「修正不要」の理由付き返信
   - **返信コメント（`reply_to_thread.sh`）** ← 忘れやすい
   - **`resolveReviewThread`（`resolve_thread.sh`）** ← 忘れやすい
4. push 後に新レビューが入ったら再取得してループ
5. レビューに無い別問題（CI failure 等）を見つけた場合、PR スコープに直接関係するものだけバンドルし、関係ないものはユーザーに報告のみ

### スクリプト

スキルに 3 つのラッパーあり：

- `~/.codex/skills/respond-to-pr-reviews/scripts/list_unresolved_threads.sh <pr> [repo]`
- `~/.codex/skills/respond-to-pr-reviews/scripts/reply_to_thread.sh <pr> <comment-db-id> <body> [repo]`
- `~/.codex/skills/respond-to-pr-reviews/scripts/resolve_thread.sh <thread-node-id>`

### 実行手順

1. `ARGUMENT` から PR 番号を決定（省略時はカレントブランチから）
2. `SKILL.md` を `Read` で読み込む
3. スキルのワークフロー（対象 PR 特定 → 未 resolve 列挙 → 各スレッド処理 → 再取得ループ）に従う
4. 完了後、「処理したスレッド / 追加コミット / 未 resolve 残 / CI 状況」を報告

**注意**: このコマンドは skill へのエントリであり、実際の判断は skill の本体に委ねる。skill を改善したら自動的にコマンドの挙動も追従する。
