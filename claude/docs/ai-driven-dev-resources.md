# AI-Driven Development Loop — 必要リソース一覧

個人利用を前提とした、全レイヤーのリソースチェックリスト。
GitHub アカウントと 24 時間稼働の Ubuntu マシンがあることを前提とする。

## 1. GitHub 関連

### アカウント・プラン

| リソース          | 必須/推奨 | 備考                                                 |
| :---------------- | :-------: | :--------------------------------------------------- |
| GitHub アカウント |   必須    | 前提                                                 |
| GitHub Pro プラン |   推奨    | Private リポで Actions 3,000分/月。Free でも 2,000分 |
| GitHub Projects   |   必須    | タスクキューとして使用。無料で利用可能               |

### リポジトリ構成

| リポジトリ                  | 用途                                    | 可視性     |
| :-------------------------- | :-------------------------------------- | :--------- |
| 対象プロジェクト(複数可)    | 実装対象のコードベース                  | Private OK |
| `.github` リポ (Org の場合) | Dispatcher/Worker の reusable workflows | Private OK |
| dotfiles (任意)             | Claude Code の設定・スキル管理          | Private OK |

### Personal Access Token (PAT)

| トークン                      | スコープ                      | 用途                                                |
| :---------------------------- | :---------------------------- | :-------------------------------------------------- |
| `PUSH_AND_RUN_WORKFLOW_TOKEN` | `repo`, `workflow`, `project` | git push, PR 作成, workflow dispatch, Projects 更新 |

`github.token` (GITHUB_TOKEN) では:

- 作成した PR が後続 CI をトリガーしない
- 他リポジトリへのアクセスができない
- Projects の更新ができない

そのため PAT が必要。Fine-grained PAT 推奨。

### GitHub Projects の設定

| フィールド | 型            | 値                                                   |
| :--------- | :------------ | :--------------------------------------------------- |
| Status     | Single select | Backlog, Ready, In progress, Waiting, Done, Canceled |
| Priority   | Single select | P0, P1, P2                                           |
| Size       | Single select | XS, S, M, L, XL                                      |
| Start date | Date          | 自動設定                                             |
| End date   | Date          | 自動設定                                             |

### ラベル (各リポジトリ)

| ラベル        | 用途                                   |
| :------------ | :------------------------------------- |
| `claude-auto` | Dispatcher の自動実行対象を示す (任意) |

## 2. LLM アクセス

### Claude (いずれか1つ)

| 方式                  | コスト   | 特徴                                                     |
| :-------------------- | :------- | :------------------------------------------------------- |
| Anthropic API 直接    | 従量課金 | 最もシンプル。API キーのみ                               |
| AWS Bedrock           | 従量課金 | AWS アカウント必要。企業利用に適する                     |
| Claude Max/Pro プラン | 月額固定 | API アクセスではなく対話用。ヘッドレスモードでの利用不可 |

**推奨: Anthropic API 直接**（個人利用なら最もシンプル）

| 必要な Secret                   | 値                                    |
| :------------------------------ | :------------------------------------ |
| `ANTHROPIC_API_KEY`             | Anthropic API キー (API 直接の場合)   |
| `BEDROCK_AWS_ACCESS_KEY_ID`     | AWS アクセスキー (Bedrock の場合)     |
| `BEDROCK_AWS_SECRET_ACCESS_KEY` | AWS シークレットキー (Bedrock の場合) |

### 他の LLM (クロスレビュー・コスト最適化用、任意)

| プロバイダ | 用途                      | 必要な Secret    |
| :--------- | :------------------------ | :--------------- |
| OpenAI     | GPT-4o でのクロスレビュー | `OPENAI_API_KEY` |
| Google     | Gemini でのレビュー       | `GOOGLE_API_KEY` |

最初は Claude のみで十分。クロスレビューは後から追加可能。

### コスト見積もり (月額目安)

| モデル       | 1 Issue あたり目安 | 月 50 Issue | 月 100 Issue |
| :----------- | :----------------- | :---------- | :----------- |
| Haiku (XS/S) | $0.05〜0.20        | $2.5〜10    | $5〜20       |
| Sonnet (M)   | $0.30〜1.00        | $15〜50     | $30〜100     |
| Opus (L/XL)  | $1.00〜5.00        | $50〜250    | $100〜500    |

実際のコストは Issue の複雑さ・コードベースの大きさに大きく依存する。
`--max-budget-usd` で Issue ごとの上限を設定して管理する。

## 3. Ubuntu マシン (24 時間稼働)

### ハードウェア要件

| 項目         | 最低     | 推奨       | 備考                      |
| :----------- | :------- | :--------- | :------------------------ |
| CPU          | 2 コア   | 4 コア以上 | 並列 Worker 数に比例      |
| メモリ       | 4 GB     | 8 GB 以上  | Claude Code + git 操作    |
| ディスク     | 20 GB    | 50 GB 以上 | 複数リポジトリの checkout |
| ネットワーク | 常時接続 | 常時接続   | API 呼び出し + git push   |

### 用途

| 役割               | 説明                                         |
| :----------------- | :------------------------------------------- |
| Self-hosted Runner | GitHub Actions の分数を消費しない            |
| ローカル cron 実行 | Dispatcher をローカルで動かす選択肢          |
| 開発環境           | 対話モードでの `/discover`, `/scaffold` 実行 |

### Self-hosted Runner の設定

```bash
# GitHub Actions Runner のインストール
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.XXX.X/actions-runner-linux-x64-2.XXX.X.tar.gz
tar xzf ./actions-runner-linux-x64.tar.gz

# リポジトリまたは Org レベルで登録
./config.sh --url https://github.com/{owner} --token {TOKEN}

# サービスとして登録（24 時間稼働）
sudo ./svc.sh install
sudo ./svc.sh start
```

Self-hosted Runner を使う場合、GitHub Actions の分数制限は完全に回避できる。

## 4. ソフトウェア

### 必須

| ツール          | 用途                   | インストール                               |
| :-------------- | :--------------------- | :----------------------------------------- |
| Claude Code     | LLM 実行エンジン       | `npm install -g @anthropic-ai/claude-code` |
| Node.js (22+)   | Claude Code の実行環境 | `mise use node@22`                         |
| git             | バージョン管理         | `apt install git`                          |
| gh (GitHub CLI) | Issue/PR/Projects 操作 | `apt install gh`                           |

### 推奨

| ツール | 用途                               | インストール                  |
| :----- | :--------------------------------- | :---------------------------- |
| mise   | タスクランナー・ツール管理         | `curl https://mise.run \| sh` |
| jq     | JSON 処理 (GraphQL レスポンス解析) | `apt install jq`              |
| Docker | プレビュー環境の構築               | `apt install docker.io`       |
| uv     | Python プロジェクト管理            | `mise use uv`                 |

### 任意 (クロスレビュー用)

| ツール             | 用途                             |
| :----------------- | :------------------------------- |
| Codex CLI (OpenAI) | Claude のコードを GPT でレビュー |

## 5. 通知・コミュニケーション

### 必須ではないが強く推奨

| サービス             | 用途                                 | 設定                 |
| :------------------- | :----------------------------------- | :------------------- |
| Slack                | Worker の完了/失敗通知、レビュー依頼 | Incoming Webhook URL |
| GitHub Notifications | PR レビュー依頼                      | デフォルトで有効     |
| メール               | フォールバック通知                   | GitHub 設定          |

Slack Webhook URL は GitHub Secrets に格納:

| Secret              | 値                            |
| :------------------ | :---------------------------- |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` |

Slack がなくても GitHub の通知だけで運用可能だが、
レビュー待ち PR の検知速度が落ちる（= ブロッキング時間が増える）。

## 6. GitHub Actions ワークフロー

### Dispatcher (定期実行)

```yaml
# .github/workflows/dispatcher.yml
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:
```

必要な環境変数・Secrets:

- `PUSH_AND_RUN_WORKFLOW_TOKEN` — Projects 読み取り + Worker 起動
- Projects の owner / number — 対象プロジェクトの特定

### Worker (Issue 実行)

```yaml
# .github/workflows/worker.yml
on:
  workflow_dispatch:
    inputs:
      issue_url: { required: true, type: string }
      issue_number: { required: true, type: string }
      repo: { required: true, type: string }
      size: { required: false, type: string, default: "M" }
```

必要な環境変数・Secrets:

- `ANTHROPIC_API_KEY` または `BEDROCK_AWS_ACCESS_KEY_ID` + `BEDROCK_AWS_SECRET_ACCESS_KEY`
- `PUSH_AND_RUN_WORKFLOW_TOKEN` — git push, PR 作成、Status 更新
- `SLACK_WEBHOOK_URL` — 通知 (任意)

## 7. チェックリスト

### Phase 1: 最小構成（まず動かす）

- [ ] GitHub アカウント + PAT 作成 (repo, workflow, project スコープ)
- [ ] LLM の API キー取得 (Anthropic API or Bedrock)
- [ ] Ubuntu マシンに必須ツールをインストール (Claude Code, Node.js, git, gh, jq)
- [ ] GitHub Projects を作成 (Status, Priority, Size フィールド)
- [ ] Worker ワークフローを作成してテスト (手動 dispatch で 1 Issue を処理)
- [ ] GitHub Secrets を登録 (API キー, PAT)

### Phase 2: 自動化（定期実行）

- [ ] Dispatcher ワークフローを作成 (cron 15分)
- [ ] Self-hosted Runner を設定 (分数制限の回避)
- [ ] Slack Webhook を設定 (通知)
- [ ] ガードレールを設定 (max-budget-usd, concurrency group)

### Phase 3: 最適化（コスト・品質）

- [ ] Size ベースのモデルルーティングを実装
- [ ] クロスレビューを導入 (別モデルでのレビュー)
- [ ] PR コメント → 自動修正ループを実装
- [ ] バッチレビュー + AI サマリーを実装
- [ ] KPI の計測を開始 (Waiting→Done 時間、Issue/日、コスト/Issue)

## 8. 月額コスト概算

| 項目                       | Free 構成            | 推奨構成                   |
| :------------------------- | :------------------- | :------------------------- |
| GitHub                     | Free ($0)            | Pro ($4/月)                |
| LLM API (月 50 Issue 目安) | Sonnet 中心: $15〜50 | Haiku+Sonnet 混合: $10〜30 |
| Ubuntu マシン              | 既存 ($0)            | 既存 ($0)                  |
| Slack                      | Free ($0)            | Free ($0)                  |
| **合計**                   | **$15〜50/月**       | **$14〜34/月**             |

LLM コストが支配的。Size ベースのモデルルーティングで最適化する。
