# ワークスペースの作成

- 参考: <https://alembic.sqlalchemy.org/en/latest/tutorial.html>

ここでは `alembic-sample` を例にします。

```bash
cd alembic-sample
uv init
uv add alembic psycopg[binary]
```

## alembic の初期化をする

```bash
# alembic というディレクトリが作成され、その中に設定ファイルやバージョン管理用のスクリプトが生成されます。
uv run alembic init alembic

# pyproject.toml を利用している場合は
uv run alembic init --template pyproject alembic
# とすると pyproject.toml に自動的に記述が追加されます。
```

追加されるファイル

```bash
$ tree .
.(project root)
├── alembic.ini # Alembic の設定ファイル
└── alembic/
    ├── env.py # Alembic のマイグレーションツールが呼び出されるたびに実行されるスクリプト
    ├── README
    ├── script.py.mako # 新しいマイグレーションスクリプトを生成するための mako テンプレート
    └── versions/
```

## マイグレーションスクリプトを作成する

新しいマイグレーションスクリプトを作成するには、以下のコマンドを実行します。

```bash
uv run alembic revision -m "create users table"
```

すると alembic/versions/ ディレクトリに新しいマイグレーションスクリプトが作成されます。

## PostgreSQL コンテナの起動

実際にマイグレーションを試すために、PostgreSQL データベースを起動します。

[compose.yml](./alembic-sample/docker-compose.yml) を用意してるのでこれを利用します。

```bash
docker compose up -d
```

- ユーザー名／パスワードは `alembic`、データベース名は `alembic_sample` です。
- 停止は `docker compose down` で行えます。

## 疎通確認

Alembic で PostgreSQL データベースに接続できるか確認します。

```bash
$ uv run alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

## マイグレーションの実行

```bash
$ uv run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 90e7511fbee5, create users table
```

## マイグレーションが実行されたことを確認する

```bash
# スキーマ一覧を取得
$ docker compose exec postgres psql -U alembic -d alembic_sample -c "\dt"
# これで users テーブルが表示されれば成功です。
$ docker compose exec postgres psql -U alembic -d alembic_sample -c "SELECT * FROM users LIMIT 1;"
# を実行し、列が取り出せるか確認する。
```
