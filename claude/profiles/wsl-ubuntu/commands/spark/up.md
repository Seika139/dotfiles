# Spark ローカル環境の起動

Spark プロジェクトの全マイクロサービス（Auth, Patent Search, Conversation API, Frontend）をローカルで統合的に起動するスキルです。

## アーキテクチャの理解（重要）

Spark の全サービスは **2段階起動アーキテクチャ** を採用しています:

1. **コンテナ起動**: 全サービスの compose.yml は `command: ["sleep", "infinity"]` を設定しており、コンテナは起動するがサーバーは自動起動しない
2. **サーバー起動**: コンテナ内で `mise run server` 等を実行して初めてサーバーが起動する

`mise run start` はコンテナ起動（第1段階）のみ行います。サーバーの起動（第2段階）は `mise run dev`（tmux 版）か、手動で `docker exec` を使って行います。

### ポートマッピング（runtime プロファイル）

| サービス         | ホスト公開ポート | コンテナ内ポート |
| ---------------- | ---------------- | ---------------- |
| Auth Service     | 8002             | 8002             |
| Patent Search    | 8110             | 8000             |
| Conversation API | 8210             | 8200             |
| Frontend         | 8410             | 3100             |

## 前提条件

- Docker Desktop が起動していること
- mise がインストール済みであること
- 各サービスのリポジトリが `spark-local-integration` の兄弟ディレクトリとしてクローン済みであること

## Claude Code から直接実行する場合（推奨）

tmux を使わず、Claude Code のターミナルから直接実行できる非対話型コマンドです。

### 起動（コンテナのみ）

```bash
cd $(fd "local-integration" -- "$HOME" | head -n 1)
mise run start
```

各サービスに対して順次 `mise trust -a` → `mise run init` → `mise run up` を実行し、最後に `mise run status` で結果を表示します。

### 停止

```bash
mise run stop
```

各サービスに対して順次 `mise run down` を実行します。

### 完全クリーンアップ（ボリューム削除）

```bash
mise run teardown
```

確認プロンプトなしで全サービスを停止し、Docker ボリュームも削除します。

### 状態確認

```bash
mise run status
```

## ユーザーが手動で tmux を使う場合

tmux がインストール済みの場合、以下のコマンドで tmux セッションを使った起動も可能です。

### Docker Compose による起動（コンテナのみ）

```bash
mise run up
```

これにより tmux セッション "spark" が作成され、各サービスのコンテナが起動します。

### 開発モードでの起動（ホットリロード対応・サーバー起動含む）

```bash
mise run dev
```

`mise run dev` はコンテナ起動に加え、各サービス内でサーバーも起動します（2段階目も実行）。

### 停止・クリーンアップ（tmux 版）

| コマンド           | 説明                                                  |
| ------------------ | ----------------------------------------------------- |
| `mise run down`    | 全サービス停止（tmux 経由）                           |
| `mise run restart` | 全サービス再起動                                      |
| `mise run clean`   | 全サービス停止 + ボリューム削除（確認プロンプトあり） |

## 初回セットアップ

```bash
cd $(fd "local-integration" -- "$HOME" | head -n 1)
mise trust
mise setup
```

## 設定の検証

```bash
mise run config-verify
```

## アクセス URL

| サービス         | URL                     |
| ---------------- | ----------------------- |
| Frontend         | <http://localhost:8410> |
| Auth Service     | <http://localhost:8002> |
| Patent Search    | <http://localhost:8110> |
| Conversation API | <http://localhost:8210> |

## その他のコマンド

| コマンド                  | 説明                    |
| ------------------------- | ----------------------- |
| `mise run network-create` | Docker ネットワーク作成 |
| `mise run network-remove` | Docker ネットワーク削除 |

## トラブルシューティング

- **ヘルスチェックが「サーバー未起動」**: コンテナは起動済みですがサーバーが未起動です。`mise run dev` を実行するか、個別に `docker exec` でサーバーを起動してください。
- **ネットワークエラー**: `docker network rm spark-network` してから `mise run network-create`
- **完全リセット**: `mise run teardown` → `mise run network-remove` → `mise run start`

## 注意事項

- `mise run up` / `mise run down` は tmux セッションを作成するため、Claude Code のターミナルからは **バックグラウンドで実行できません**。Claude Code から操作する場合は `mise run start` / `mise run stop` を使ってください。
- 既に tmux セッション "spark" が存在する場合、`mise run up` / `mise run down` はそのセッションを再利用します。
