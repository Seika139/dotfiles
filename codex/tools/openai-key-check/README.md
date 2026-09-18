# openai-key-check (Go)

OpenAI API key を使って、OpenAI API の読み取り endpoint に接続できるかを確認するための依存ランタイム不要の CLI です。
API key を表示・保存せず、結果は機械処理しやすい JSON で標準出力に出力します。

## このツールで確認できること

このツールは、API key を使って次の3つを確認するためのものです。

1. OpenAI API に接続でき、基本的な読み取り確認が成功するかを調べます。これは API key が少なくとも読み取り用の API に到達できるかを見るための目安です。
2. 指定したモデルを個別に確認します。通常の確認だけでは、特定のモデルが利用できることまでは分かりません。
3. API key に紐づく利用者と組織を確認します。氏名、組織名、組織タイトルなどが表示されるため、ログや共有先に出す場合は注意してください。

## 前提

- ビルドには Go 1.27.1（少なくとも Go 1.27 系）を使用します。
- 実行時に Go や外部ライブラリは不要です。
- macOS、Linux、Windows の amd64 / arm64 向けにビルドできます。

## ローカルビルド

このディレクトリで実行します。

```sh
go test ./...
go vet ./...
mkdir -p dist
go build -trimpath -o dist/openai-key-check .
```

生成されたバイナリは `dist/` に置かれ、`dist/` は `.gitignore` の対象です。

### クロスビルド

`CGO_ENABLED=0` により、C コンパイラに依存しないバイナリを作ります。macOS / Linux / Windows の各 amd64 / arm64 用の例は次のとおりです。

```sh
mkdir -p dist

CGO_ENABLED=0 GOOS=darwin  GOARCH=amd64 go build -trimpath -o dist/openai-key-check-darwin-amd64 .
CGO_ENABLED=0 GOOS=darwin  GOARCH=arm64 go build -trimpath -o dist/openai-key-check-darwin-arm64 .
CGO_ENABLED=0 GOOS=linux   GOARCH=amd64 go build -trimpath -o dist/openai-key-check-linux-amd64 .
CGO_ENABLED=0 GOOS=linux   GOARCH=arm64 go build -trimpath -o dist/openai-key-check-linux-arm64 .
CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -trimpath -o dist/openai-key-check-windows-amd64.exe .
CGO_ENABLED=0 GOOS=windows GOARCH=arm64 go build -trimpath -o dist/openai-key-check-windows-arm64.exe .
```

バイナリは実行時の Go のバージョンに依存しませんが、OS と CPU アーキテクチャに対応した成果物が必要です。
バイナリにしても、OS の信頼済み CA 証明書、DNS、時計、ネットワーク経路の状態は固定されません。
macOS のコード署名・公証や Windows SmartScreen への対応も、配布時の別要件です。

## 目的別の使い方

### 1. API key の基本的な利用可否を確認する

引数なしで実行すると、従来互換の標準チェックを行います。

```sh
./dist/openai-key-check
```

API に接続できたか、HTTP status、エラーがある場合の種類とコード、取得できたモデル数を短い JSON で確認できます。
詳細なモデル一覧や安全な response header も確認したい場合は `--verbose` を追加します。

```sh
./dist/openai-key-check --verbose
```

同じ処理を明示的に指定する場合は `models` サブコマンドを使います。

```sh
./dist/openai-key-check models
./dist/openai-key-check models --verbose
```

### 2. 特定のモデルを確認する

`--check-model MODEL` を追加すると、基本チェックに加えて指定したモデルも確認します。

```sh
./dist/openai-key-check --check-model gpt-4o-mini
./dist/openai-key-check models --check-model gpt-4o-mini
```

基本チェックが成功していても、すべてのモデルを利用できるとは限りません。
特定のモデルを確認したい場合は、このオプションを指定してください。`--verbose` と組み合わせることもできます。

### 3. API key に紐づく利用者と組織を確認する

`identity` を指定すると、API key に紐づく利用者と組織の情報を確認します。
この処理は基本チェックとは別の確認で、モデル一覧は取得しません。

```sh
./dist/openai-key-check identity
```

利用者・組織の追加情報も確認したい場合は `--verbose` を指定します。

```sh
./dist/openai-key-check identity --verbose
```

`identity` の通常出力には、利用者の `id`、人間が読みやすい UTC の `created`、`name`、組織ごとの `id`・`name`・`title` が含まれます。
`--verbose` では、これらに加えて `created_unix` など、あらかじめ許可した追加フィールドを出力します。
API から返された未知のフィールドや応答本文全体は出力しません。

## 共通オプション

次のオプションは、`models` と `identity` のどちらでも使えます。

- `--api-key-stdin`: API key を標準入力から受け取ります。対話で安全に入力する場合は、このオプションを付けずに実行してください。入力中の key は画面に表示されません。
- `--timeout SECONDS`: 通信のタイムアウトを秒で指定します。既定値は15秒です。
- `--organization ORG_ID`: OpenAI の組織を指定します。
- `--project PROJECT_ID`: OpenAI のプロジェクトを指定します。
- `--verbose`: 通常出力に加えて、各機能で許可された詳細情報を出力します。

```sh
./dist/openai-key-check --api-key-stdin < key.txt
./dist/openai-key-check identity --api-key-stdin < key.txt
./dist/openai-key-check --organization org_... --project proj_...
./dist/openai-key-check --timeout 30
./dist/openai-key-check --api-key-stdin --check-model gpt-4o-mini --timeout 10 < key.txt
```

`--organization` と `--project` は、それぞれ OpenAI の組織・プロジェクトを指定するための request header として送信されます。`--check-model MODEL` はモデル確認専用で、`identity` では使えません。

## 出力の見方

通常出力は、確認結果を機械処理しやすい短い JSON です。`--verbose` を指定すると、通常出力に加えて確認に役立つ詳細が増えます。

### 基本チェックの出力

通常は、確認結果、HTTP status、HTTP エラーの種類とコード、取得できたモデル数を出力します。

```json
{
  "schema_version": 3,
  "status": "endpoint_accessible",
  "models_endpoint": {
    "outcome": "endpoint_accessible",
    "status": 200,
    "model_count": 1
  }
}
```

`--verbose` では、許可された response header、モデル一覧、一覧が100件を超えた場合の `models_truncated` も出力します。
`--check-model` を指定した場合は、指定したモデルの確認結果が `model_endpoint` に追加されます。

### identity の出力

`identity` の通常出力では、次の情報を確認できます。

- 利用者: `id`、UTC RFC 3339 形式の `created`、`name`
- 組織: 組織ごとの `id`、`name`、`title`。上流応答に `created` が存在する場合は、組織の `created` も UTC RFC 3339 形式で出力します。

短い成功例:

```json
{
  "schema": "openai-key-check/identity",
  "schema_version": 1,
  "status": "endpoint_accessible",
  "identity_endpoint": {"outcome": "endpoint_accessible", "status": 200},
  "identity": {
    "id": "user_example",
    "created": "2026-08-28T12:26:12Z",
    "name": "Example User",
    "orgs": [{"id": "org_example", "name": "Example Org", "title": "Example"}]
  }
}
```

`identity --verbose` では、`created_unix` や API 応答に含まれる追加情報のうち、出力を許可したフィールドだけを追加します。
氏名、組織名、組織タイトルなどを含むため、結果をログに保存したり他人へ共有したりする前に内容を確認してください。

### 結果の状態

通常の成功は `status: "endpoint_accessible"`、HTTP による拒否は `status: "rejected"`、ネットワークなどの理由で判定できない場合は `status: "indeterminate"` です。
API key、Authorization header、response body 全文、raw error message は出力しません。

## 確認できないこと・注意点

HTTP 200 は、対象の確認先に読み取りアクセスできたことを示す目安です。次のことまでは保証しません。

- 残高や課金状態
- 実際に推論リクエストを実行できること
- すべてのモデルやすべての API 機能を利用できること
- API key が将来も有効であること

特定のモデルを確認するには `--check-model MODEL` が必要です。基本チェックだけでは、特定モデルの利用可否は判断できません。

`identity` が返すのは、通常の API key で認証された利用者・組織の情報です。
キーの管理画面上の owner、キー名、最終利用日時などを取得する Admin API のキー管理情報とは別物であり、このツールの `identity` には含めません。

## 技術的な補足

基本チェックは `/v1/models` を使い、`--check-model MODEL` を指定した場合だけ `/v1/models/MODEL` も確認します。
`identity` は `/v1/me` だけを使い、`/v1/models` は呼び出しません。

`/v1/models` が HTTP 200 を返し、応答の `data` を配列として解析できた場合だけ、通常出力にモデル総数を出力します。
`--verbose` を指定した場合は、モデル一覧の各項目に含まれるモデル ID、`owned_by`、取得できた `created` / `shutdown_date` も出力します。
応答が不正な JSON、`data` が欠落・`null`・配列以外、または本文が1 MiBを超えて解析できない場合は、到達成功を保ったまま `metadata_unavailable: true` を出力します。
未知の metadata を空配列や0件として扱いません。

`--verbose` のモデル一覧は最大100件です。100件を超えた場合は `models_truncated: true` を出力します。
`identity` の応答についても、本文の読み取り・JSON 解析・または1 MiBのサイズ上限に失敗した場合は、到達結果を保持したまま `identity_metadata_unavailable: true` を出力します。
値を推測して補完することはありません。

`identity` に `--check-model` を指定することはできません。

API key を command-line argument（argv）や環境変数に置かないでください。シェル履歴、プロセス一覧、CI のログや設定へ漏れる可能性があります。
`--api-key-stdin` を使う場合も、`key.txt` のアクセス権や保存場所に注意し、不要になった平文ファイルは削除してください。

## 終了コード

| コード | 意味 |
| ---: | --- |
| 0 | 確認対象 endpoint へのアクセス成功 |
| 2 | 引数または入力 key のエラー |
| 10 | HTTP 401（認証拒否） |
| 11 | HTTP 403（権限拒否） |
| 12 | HTTP 429（rate limit 等） |
| 13 | その他の HTTP エラー |
| 14 | ネットワークまたはプロセス起動を判定できない |

## 環境隔離と安全設計

API key や HTTP 通信を扱う子プロセスは、起動時に既存の環境変数を引き継がず、内部 marker だけの環境で再起動した後に環境をクリアします。
そのため `OPENAI_API_KEY`、proxy、TLS 関連設定、`GODEBUG` などのローカル環境変数に依存しません。標準入力・標準出力・標準エラー出力は引き継ぎます。

key は端末では非表示で読み取り、非対話時は `--api-key-stdin` の標準入力だけから読み取ります。
リダイレクトは追従せず、HTTP body は 1 MiB までに制限します。
TLS 検証や redirect 無効化などの通信設定もプログラム側で明示しています。

## テスト

```sh
go test ./...
go vet ./...
```

テストは入力検証、HTTP status と redirect、safe header、JSON metadata の要約、本文サイズ上限、秘密情報の出力抑止、環境隔離条件を確認します。
