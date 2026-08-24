# Basic 認証の学習サンプル

HTTP Basic 認証の `Authorization` ヘッダー、`401 Unauthorized`、`WWW-Authenticate` を実際に確認するための、依存なしの Python サンプルです。

このサーバーは `127.0.0.1` にだけ bind します。外部公開や本番利用は想定していません。

## 起動

`uv` をインストールした後、次を実行します。

```shell
cd docs/auth/basic-auth-sample
uv run python main.py
```

ポートを変える場合は `uv run python main.py --port 8080` を使います。

既定の学習用資格情報はユーザー名 `study-user`、パスワード `study-password` です。起動時に限り、次の環境変数で上書きできます。

```shell
$env:BASIC_AUTH_USERNAME = "alice"
$env:BASIC_AUTH_PASSWORD = "correct-horse:battery-staple"
uv run python main.py
```

PowerShell では上記のように設定します。資格情報はサーバーの起動時に一度だけ読み取られ、実行中に環境変数を変更しても反映されません。

## curl で確認する

```shell
curl -i http://127.0.0.1:8000/public
curl -i http://127.0.0.1:8000/protected

# -u は `-u username:password` で Basic 認証を行うオプションです。
curl -i -u study-user:study-password http://127.0.0.1:8000/protected

# -H は送信する HTTP ヘッダーを指定するオプションです。Basic 認証のヘッダーを自分で作る場合は次のようにします。
# basic 認証のヘッダーは `Authorization: Basic <Base64(username:password)>` です。
curl -i -H "Authorization: basic c3R1ZHktdXNlcjpzdHVkeS1wYXNzd29yZA==" http://127.0.0.1:8000/protected
```

2 行目では `401` と `WWW-Authenticate: Basic realm="Basic Auth Study"` が返ります。3 行目と 4 行目では `200` が返ります。4 行目の小文字 `basic` でも認証方式名は大文字・小文字を区別しないため有効です。

ブラウザで `http://127.0.0.1:8000/protected` を開くと、認証ダイアログが表示されます。資格情報を入力した後、成功時の本文を確認してください。

## 重要な注意点

`Basic <Base64(username:password)>` の Base64 は暗号化ではなく、誰でも復元できる符号化です。Basic 認証を使う通信には HTTPS が必須です。

このサンプルは Python 標準ライブラリの `http.server` を使います。`http.server` は本番用途向けではないため、本番システムでこの実装を利用しないでください。
