# GitHub Actions Self-hosted Runner で Claude Code を動かす

## 背景

Claude Code を GitHub Actions 上で自動実行し、Issue の自動実装 (PoC) を試みた。

## 認証の問題と経緯

### 最初のアプローチ: IAM キーを GitHub Secrets に格納

Bedrock API の認証に使う IAM 認証情報を GitHub Secrets に格納し、
GitHub-hosted runner (`ubuntu-latest`) で実行する方式を試みた。

#### PoC での試行錯誤

1. **`--dangerouslySkipPermissions`** (キャメルケース) で実行 → `unknown option` エラー
   - Claude Code CLI はケバブケース (`--dangerously-skip-permissions`) が正式
2. **`--max-turns 50`** で実行 → `unknown option` エラー
   - 存在しないオプション。正しくは `--max-budget-usd` でコスト制限
3. **`us.anthropic.claude-sonnet-4-5-20250929-v1:0`** で実行 → 403 エラー
   - IAM ポリシーが US 推論プロファイルを許可していない
4. **`global.anthropic.claude-sonnet-4-5-20250929-v1:0`** で実行 → 403 エラー
   - Sonnet モデル自体へのアクセス権がない
5. **`global.anthropic.claude-opus-4-6-v1`** で実行 → 403 エラー
   - ローカルで動いている Opus でも 403

#### 原因の特定

`credential-process` の出力を調査した結果、以下が判明:

```json
{
  "AccessKeyId": "ASIA...",    // ASIA = 一時認証情報
  "SecretAccessKey": "...",
  "SessionToken": "...",       // SessionToken が存在
  "Expiration": "2026-03-17T14:10:30Z",  // 約11時間で期限切れ
  "Version": 1
}
```

- **`ASIA` プレフィックス**: 一時認証情報 (STS AssumeRole の結果)
- **`SessionToken` が必須**: `AWS_SESSION_TOKEN` なしでは認証できない
- **`Expiration` あり**: 定期的なリフレッシュが必要

ローカル環境の `env` に入っていた `AKIA*` キーは、`awsAuthRefresh` がキャッシュした
値の可能性があり、GitHub Secrets に格納しても期限切れで無効になる。

### 会社の AWS ルール (EPU) による制約

- **IAM User の新規作成は禁止** (EPU ルール)
- **IAM Role は `epu-` プレフィックス + `ExtendedPowerUserBoundary` が必須**
- Bedrock アカウント (`054657590879`) は Terraform 管理外

これらの制約により、「専用 IAM ユーザーの作成」や「GitHub OIDC → IAM Role」の
方式はすぐには実施できない。

### 結論: Self-hosted Runner

credential-process がローカルに存在する Self-hosted Runner なら、
毎回最新の一時認証情報を取得できる。

## PoC 結果

| 項目     | 結果                                               |
| :------- | :------------------------------------------------- |
| 実行時間 | 2m9s                                               |
| トリガー | Issue に `claude-auto` ラベル付与                  |
| Runner   | Self-hosted (WSL Ubuntu)                           |
| 認証     | credential-process → STS 一時認証情報              |
| モデル   | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| 成果物   | ブランチ作成 + PR 自動作成                         |
| 試行回数 | 7 回（下記の問題を順次修正）                       |

## 設計

```text
GitHub (cyg-ai-tech/.github)
  Issue に "claude-auto" ラベル付与
       | (webhook)
       v
WSL Ubuntu (Self-hosted Runner, ラベル: claude-code)
  +-- GitHub Actions Runner デーモン
  +-- credential-process → STS 一時認証情報を取得
  +-- Claude Code CLI
  +-- gh CLI
       |
       v
  Claude Code → Bedrock API (054657590879)
       |
       v
  PR 作成 → Issue にコメント
```

### ワークフローの認証フロー

```yaml
- name: Solve issue with Claude Code
  run: |
    # credential-process で一時認証情報を取得
    CREDS=$(/path/to/credential-process --profile ccwb-prod-apne-1)
    export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r '.AccessKeyId')
    export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r '.SecretAccessKey')
    export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r '.SessionToken')

    claude -p "..." --dangerously-skip-permissions --max-budget-usd 5
```

### GitHub-hosted vs Self-hosted の比較

| 項目               | GitHub-hosted            | Self-hosted (WSL)              |
| :----------------- | :----------------------- | :----------------------------- |
| 認証               | Secrets (固定キー)       | credential-process (動的)      |
| 一時認証情報の対応 | 不可 (期限切れ)          | 毎回取得で対応可能             |
| 環境構築           | 毎回クリーンインストール | 既存ツールが使える             |
| 可用性             | 常時                     | マシン起動中のみ               |
| ネットワーク       | GitHub が管理            | 自己管理 (社内 VPN 内でも動作) |
| コスト             | GitHub Actions 無料枠    | 電気代のみ                     |

## セットアップ手順

### 1. GitHub Actions Runner のインストール

```bash
mkdir ~/actions-runner && cd ~/actions-runner
# GitHub の Settings > Actions > Runners から最新 URL を取得
curl -o actions-runner.tar.gz -L <RUNNER_URL>
tar xzf actions-runner.tar.gz
```

### 2. リポジトリレベルで登録

Org の Settings 権限がない場合はリポジトリレベルで登録できる。

```bash
# 登録トークンの取得（1時間で期限切れ）
gh api repos/<owner>/<repo>/actions/runners/registration-token --method POST --jq '.token'

# リポジトリレベルで登録
./config.sh \
  --url https://github.com/<owner>/<repo> \
  --token <REGISTRATION_TOKEN> \
  --labels claude-code,wsl-ubuntu \
  --name wsl-claude-runner \
  --work _work \
  --unattended
```

### 3. バックグラウンドで起動

```bash
# systemd が有効な場合
sudo ./svc.sh install
sudo ./svc.sh start

# または tmux
tmux new-session -d -s runner './run.sh'
```

### 4. ワークフローの設定

```yaml
runs-on: [self-hosted, claude-code]
```

### 5. actionlint のカスタムラベル登録

Self-hosted Runner のカスタムラベルを使う場合、actionlint がデフォルトで認識しないため
`.github/actionlint.yaml` に登録が必要。

```yaml
# .github/actionlint.yaml
self-hosted-runner:
  labels:
    - claude-code
    - wsl-ubuntu
```

## Self-hosted Runner の注意事項

### ローカル設定の干渉

Self-hosted Runner はローカルユーザーのホームディレクトリで実行されるため、
`~/.claude/settings.json` や `~/.claude/settings.local.json` の設定が
ワークフロー内の Claude Code にも適用される。

以下のような問題が発生しうる:

- `CLAUDE_CODE_MAX_OUTPUT_TOKENS` などの環境変数が不正な値だと起動に失敗する
- Stop Hook（Slack 通知など）がワークフロー実行時にも発火する
- `statusLine` の設定が CI 環境で不要なオーバーヘッドになる

#### 対策

ワークフローの `env` ブロックで明示的に上書きする:

```yaml
env:
  CLAUDE_CODE_MAX_OUTPUT_TOKENS: "16000"
  MAX_THINKING_TOKENS: "10000"
```

ローカルの `~/.claude/settings.json` を変更する場合は、
Runner のジョブにも影響することを意識する必要がある。

### Runner の可用性

- WSL / マシンが停止すると Runner もオフラインになる
- `nohup ./run.sh &` はマシン再起動で消える
- 永続化するには systemd サービスまたは tmux の自動起動を設定する

## 総括

### 成果

1. **GitHub Actions + Claude Code + Bedrock の組み合わせが動作することを実証した**
   - Issue にラベルを付けるだけで Claude Code がブランチ作成 → 実装 → PR 作成を自動実行
   - 2m9s で完了（テスト Issue の場合）
2. **Bedrock の認証フローを完全に解明した**
   - `credential-process` は STS 一時認証情報 (`ASIA*` + `SessionToken`) を返す
   - `awsAuthRefresh` がローカルセッション中にこれを定期的にリフレッシュしている
   - GitHub Secrets に固定キーを格納する方式は期限切れで動作しない
3. **Claude Code CLI のヘッドレスモードの仕様を把握した**
   - `-p` フラグで非対話実行
   - `--dangerously-skip-permissions` (ケバブケース) で全ツール自動承認
   - `--max-budget-usd` でコスト上限（`--max-turns` は存在しない）
   - `--verbose` でログ出力
4. **Self-hosted Runner のセットアップ手順と落とし穴を把握した**
   - リポジトリレベルの登録（Org 権限不要）
   - `~/.claude/settings.json` の干渉問題とその対策
   - actionlint のカスタムラベル登録

### 課題

1. **Self-hosted Runner はローカルマシン依存**
   - マシンが停止すると Actions が失敗する
   - 直接実行と比べて GitHub Actions を経由するメリットが薄い（1人利用の場合）
2. **GitHub-hosted Runner で動かすには認証の壁がある**
   - credential-process が STS 一時認証情報のため Secrets 方式が使えない
   - OIDC → IAM Role を作るには Bedrock アカウント (054657590879) への設定が必要
   - EPU ルールで IAM User 新規作成は不可
3. **ローカル設定の分離が不完全**
   - Self-hosted Runner がローカルの `~/.claude/settings.json` を読み込む
   - ワークフローの env で上書きできるが、設定変更のたびに影響を考慮する必要がある

### 今後の方向性

| 方向性                            | 説明                                                            | 条件                                     |
| :-------------------------------- | :-------------------------------------------------------------- | :--------------------------------------- |
| **直接実行の自動化**              | `/loop` やスクリプトで定期的に Issue を消化。現時点で最も現実的 | なし                                     |
| **GitHub-hosted Runner への移行** | OIDC 認証でクラウド実行。マシン依存なし                         | Bedrock アカウントに IAM Role 作成が必要 |
| **チーム展開**                    | 複数メンバーがラベル付与で Claude を利用                        | Self-hosted Runner の安定稼働が前提      |
