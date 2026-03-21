# Spark ローカル環境の状態確認

Spark プロジェクトのローカル環境で何が立ち上がっているかを包括的に確認するスキルです。

## アーキテクチャの理解（重要）

Spark の全サービスは **2段階起動アーキテクチャ** を採用しています:

1. **コンテナ起動**（`mise run start` / `mise run up`）: Docker コンテナが `sleep infinity` で起動する。この段階ではサーバーは動いていない。
2. **サーバー起動**（`mise run dev` / tmux パネル内で手動実行）: コンテナ内で `mise run server` 等を `docker exec` 経由で実行して初めてサーバーが起動する。

そのため、コンテナが `running` 状態でもヘルスチェックが「サーバー未起動」と表示されるのは**正常動作**です。

## 確認手順

### 1. 作業ディレクトリに移動

```bash
cd $(fd "local-integration" -- "$HOME" | head -n 1)
```

### 2. 統合ステータス確認（推奨）

ネットワーク・コンテナ・ヘルスチェック・tmux セッション・URL を一括表示:

```bash
mise run status
```

### 3. 個別確認コマンド

必要に応じて個別に確認する場合:

#### コンテナ状態の詳細確認

```bash
# 通常表示（JSON）
mise run ps

# 詳細表示（テーブル形式）
mise run ps -- -v -t

# 全データ JSON 出力
mise run ps -- -a
```

#### ヘルスチェック

```bash
mise run health
```

#### ポート使用状況

```bash
mise run ports
```

#### Docker ネットワーク状態

```bash
mise run network-status
```

#### 個別サービスのログ確認

```bash
mise run logs-auth
mise run logs-patent
mise run logs-conversation
mise run logs-frontend
```

#### 全サービスのログをフォロー

```bash
mise run logs
```

## 結果の読み方

### コンテナ状態

- **running**: コンテナは起動済み（ただしサーバーが動いているとは限らない）
- **exited**: 停止済み（エラーの可能性あり）
- **restarting**: 再起動中（起動に失敗している可能性）

### ヘルスチェック（3段階判定）

- **✓ OK**: サーバーが HTTP に正常応答
- **△ サーバー未起動**: コンテナは `running` だがサーバープロセスが未検出（`sleep infinity` 状態）
- **△ 起動中**: サーバープロセスは検出されたが HTTP 応答がまだない（起動途中）
- **✗ コンテナ未起動**: コンテナ自体が `running` でない

### ポート一覧（runtime プロファイル）

各 compose.yml の `ports` 設定に基づく実際のポートマッピングです。

| サービス         | ホスト公開ポート | コンテナ内ポート | ヘルスチェック URL             |
| ---------------- | ---------------- | ---------------- | ------------------------------ |
| Auth Service     | 8002             | 8002             | <http://localhost:8002/health> |
| Patent Search    | 8110             | 8000             | <http://localhost:8110/health> |
| Conversation API | 8210             | 8200             | <http://localhost:8210/health> |
| Frontend         | 8410             | 3100             | <http://localhost:8410>        |

## 注意事項

- `mise run status` はターミナル上で実行可能で、Claude Code から直接実行して結果を解析できます。
- `mise run ps -- -a` の JSON 出力はプログラムでのパースに適しています。
- コンテナが `running` でヘルスチェックが「サーバー未起動」の場合、`mise run dev` でサーバーを起動してください。
