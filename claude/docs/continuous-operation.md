# Claude Code 継続稼働ガイド

Claude Code を可能な限り無駄な時間を使わずに継続的に稼働させるための戦略をまとめる。

## Claude が止まる主な原因と対策

| 原因                         | 影響度 | 対策                                             |
| :--------------------------- | :----: | :----------------------------------------------- |
| ユーザーへの確認待ち         |   高   | permissions 拡充、プロンプト設計で自律性を上げる |
| Bash コマンドの許可待ち      |   中   | `permissions.allow` にパターンを追加             |
| コンテキストウィンドウの枯渇 |   中   | タスク粒度を小さく、`/compact` を活用            |
| AWS 認証の期限切れ           |   低   | `awsAuthRefresh` で自動更新（設定済み）          |
| API タイムアウト             |   低   | `API_TIMEOUT_MS` を十分に設定（設定済み）        |

## 1. 許可設定（permissions）の最適化

自動稼働でボトルネックになるのは Bash コマンドの許可待ち。
`settings.json` の `permissions.allow` を拡充する。

### 追加検討すべきパターン

```jsonc
// Git 操作（/solve-issue の allowed-tools にはあるがグローバルにはない）
"Bash(git checkout:*)",
"Bash(git switch:*)",
"Bash(git push:*)",
"Bash(git add:*)",
"Bash(git commit:*)",
"Bash(git status:*)",
"Bash(git diff:*)",
"Bash(git log:*)",
"Bash(git pull:*)",
"Bash(git branch:*)",
"Bash(git stash:*)",

// GitHub CLI
"Bash(gh issue:*)",
"Bash(gh pr create:*)",
"Bash(gh pr view:*)",
"Bash(gh pr list:*)",

// 開発ツール
"Bash(npm:*)",       // or pnpm, bun
"Bash(uv:*)",
"Bash(ruff:*)",
"Bash(docker:*)",
"Bash(mise:*)"
```

### 安全性とのバランス

- `deny` リストは維持する（`rm -rf`, `sudo`, `git reset`, `gh repo delete` 等）
- `deny` は `allow` より優先されるため、`allow` を広げても `deny` がガードレールになる
- `defaultMode: "acceptEdits"` でファイル編集は自動承認済み

## 2. ヘッドレスモード（-p フラグ）

対話なしでスクリプトから Claude Code を実行する。

```bash
# 基本形
claude -p "Issue #42 を解決してPRを作成してください"

# 許可するツールを明示
claude -p "タスクの内容" \
  --allowedTools 'Bash(git:*)' 'Bash(gh:*)'

# 全ツール自動承認（リスクあり、deny リストとの併用推奨）
claude -p "タスクの内容" --dangerouslySkipPermissions
```

### ヘッドレスモードの注意点

- 標準出力にテキスト結果が返る（パイプ可能）
- `--output-format json` で構造化出力も可能
- `--max-turns` でターン数を制限できる（暴走防止）
- `--dangerouslySkipPermissions` 使用時でも `deny` リストは有効

## 3. 並列実行（git worktree）

複数の Issue を同時に処理する場合、同一リポジトリで並列実行すると
git の競合が発生する。`git worktree` で作業ディレクトリを分離する。

```bash
#!/bin/bash
# parallel-solve.sh

REPO_DIR="/path/to/repo"
WORKTREE_BASE="/tmp/claude-worktrees"
ISSUES=(42 43 44)

mkdir -p "$WORKTREE_BASE" logs

for issue in "${ISSUES[@]}"; do
  worktree="${WORKTREE_BASE}/issue-${issue}"

  # worktree を作成（main ブランチベース）
  git -C "$REPO_DIR" worktree add "$worktree" -b "feature/${issue}" main

  # 各 worktree で Claude を並列実行
  (
    cd "$worktree" || exit 1
    claude -p "/solve-issue ${issue}" \
      --dangerouslySkipPermissions \
      > "${REPO_DIR}/logs/issue-${issue}.log" 2>&1
  ) &
done

wait
echo "全 Issue の処理完了"

# worktree のクリーンアップ
for issue in "${ISSUES[@]}"; do
  git -C "$REPO_DIR" worktree remove "${WORKTREE_BASE}/issue-${issue}" --force
done
```

### worktree の利点

- 各 Claude セッションが完全に独立したファイルシステムで動作
- ブランチの切り替え競合が発生しない
- `.git` は共有されるため、ディスク使用量は最小限

## 4. オーケストレーション戦略

### パターン A: ローカル cron + /loop

```plain
/loop 5m "gh issue list --label 'claude-auto' --state open --limit 1 の Issue を取得して /solve-issue を実行"
```

- 手軽だが、セッション維持が必要
- コンテキストウィンドウを消費し続ける

### パターン B: GitHub Actions

```yaml
# .github/workflows/claude-auto.yml
name: Claude Auto Solve
on:
  issues:
    types: [labeled]

jobs:
  solve:
    if: contains(github.event.label.name, 'claude-auto')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Code
        run: |
          claude -p "/solve-issue ${{ github.event.issue.number }}" \
            --dangerouslySkipPermissions
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

- Issue にラベルを付けるだけで自動実行
- セッション管理不要、完全にステートレス
- Bedrock 利用時は AWS 認証の設定が必要

### パターン C: スクリプト + Stop Hook による連鎖実行

Stop Hook でタスクキューの次のタスクを開始する方式。

```bash
#!/bin/bash
# ~/.claude/hooks/on-stop.sh
MAX_RETRIES=10
COUNTER_FILE="/tmp/claude-auto-counter"

# カウンターで無限ループを防止
count=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
if [ "$count" -ge "$MAX_RETRIES" ]; then
  echo "最大実行回数に達しました" | notify-slack
  rm -f "$COUNTER_FILE"
  exit 0
fi

# 未処理の Issue があれば次を開始
next_issue=$(gh issue list --label 'claude-auto' --state open --limit 1 --json number --jq '.[0].number')
if [ -n "$next_issue" ]; then
  echo $((count + 1)) > "$COUNTER_FILE"
  claude -p "/solve-issue ${next_issue}" --dangerouslySkipPermissions &
fi
```

注意: 無限ループ防止のガードレール（カウンター、コスト上限）が必須。

## 5. コンテキスト管理

長時間セッションでは context window が枯渇する。

### 対策

| 手法                   | 説明                                                   |
| :--------------------- | :----------------------------------------------------- |
| 1セッション = 1 Issue  | タスク粒度を小さくして、セッションを使い切る前に完了   |
| `/compact`             | 手動でコンテキストを圧縮。`/loop` との組み合わせも可能 |
| サブエージェント活用   | 調査系タスクを Agent ツールに委譲してメインを節約      |
| ヘッドレスモードで分離 | 各タスクを独立セッションで実行（コンテキスト共有なし） |

## 6. コスト最適化

### モデルの使い分け

| モデル | 用途                                   | コスト目安（入力/出力） |
| :----- | :------------------------------------- | :---------------------- |
| Opus   | 複雑な設計判断、大規模リファクタリング | 最高                    |
| Sonnet | 一般的な実装、バグ修正                 | 中                      |
| Haiku  | 定型タスク、フォーマット、単純な修正   | 最低                    |

### 設定での切り替え

```bash
# セッション内でモデル切り替え
/model sonnet   # 実装フェーズ
/model opus     # 設計判断フェーズ
```

ヘッドレスモードでは環境変数で指定:

```bash
ANTHROPIC_MODEL="us.anthropic.claude-sonnet-4-5-20250929-v1:0" \
  claude -p "単純な修正タスク"
```

## 7. 監視と通知

### 現在の設定（Stop Hook → Slack）

```jsonc
// settings.json の hooks.Stop
{
  "command": "curl -s -X POST ... Slack Webhook"
}
```

### 拡張案: 停止理由の分類

Stop Hook に渡される環境変数を活用して、停止理由に応じた通知を分岐できる。

## 推奨アーキテクチャ

```plain
GitHub Issues (label: claude-auto)
         |
         v
  オーケストレータ (GitHub Actions / cron)
         |
    +----+----+----+
    |    |    |    |
    v    v    v    v
  Claude sessions (git worktree で分離)
    |    |    |    |
    v    v    v    v
  Pull Requests
         |
         v
  Slack 通知 → 人間レビュー
```
