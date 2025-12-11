# Alembic

Alembicは、SQLAlchemyを基盤エンジンとして、リレーショナルデータベース用の変更管理スクリプトの作成、管理、および呼び出しを可能にします。

## プロジェクトに導入する

- 参考: <https://alembic.sqlalchemy.org/en/latest/tutorial.html>

uv を使用してAlembicをプロジェクトに追加するには、以下のコマンドを実行します。
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
```

`--template pyproject` を付与するオプションををつけずに実行した場合に生成される alembic.ini のうちの一部の情報が pyproject.toml に記載されます。

`alembic init` で追加されるファイル

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

## alembic.ini について

※ Windows ローカルで実行する場合、このファイルに cp932 で解釈できない文字（日本語）などが含まれているとエラーになる場合があるので、その場合は日本語を書かないようにしてください。

### script_location

マイグレーション環境の場所を指定します。
alembic init で作成した env.py や versions ディレクトリへのパスです。

```ini
script_location = %(here)s/alembic
```

### sqlalchemy.url

データベースへの接続文字列を設定します。
Alembic がデータベースに接続し、マイグレーションを実行するために使用します。

```ini
sqlalchemy.url = postgresql+psycopg://alembic:alembic@localhost:6543/alembic_sample
```

## Docker Compose で PostgreSQL を準備する

[compose.yml](./alembic-sample/docker-compose.yml) を用意してるのでこれを利用します。Alembic をローカルで試す際は、以下の手順でデータベースを起動します。

```bash
cd docs/alembic/alembic-sample
docker compose up -d
```

- デフォルトの接続情報は `alembic` ユーザー／パスワード、データベース名 `alembic_sample` です。
- ホスト側ポートは `6543` に公開されているので、`alembic.ini` では `postgresql+psycopg://alembic:alembic@localhost:6543/alembic_sample` を指定しています。
- 停止する場合は `docker compose down` を実行してください。永続化データは Docker ボリューム `postgres-data` に保存されます。

## alembic による疎通確認

PostgreSQL コンテナが起動している状態で、以下のコマンドを実行して Alembic がデータベースに接続できることを確認します。

```bash
$ uv run alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

## マイグレーションスクリプトを作成する

新しいマイグレーションスクリプトを作成するには、以下のコマンドを実行します。

```bash
uv run alembic revision -m "create users table"
```

すると alembic/versions/ ディレクトリに新しいマイグレーションスクリプトが作成されます。

## マイグレーションスクリプト

```python
"""create users table

Revision ID: 90e7511fbee5
Revises:
Create Date: 2025-12-11 16:44:51.175198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90e7511fbee5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
```

### upgrade 関数

データベーススキーマを新しいバージョンにアップグレードするための操作を定義します。

```python
def upgrade():
    op.create_table(
        'account',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
    )
```

### downgrade 関数

データベーススキーマを以前のバージョンにダウングレードするための操作を定義します。

```python
def downgrade():
    op.drop_table('account')
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

## upgrade / downgrade コマンド

最新のマイグレーションを適用するには `upgrade` コマンドを使用します。

```bash
uv run alembic upgrade head
```

最初のマイグレーションに戻すには `downgrade` コマンドを使用します。

```bash
uv run alembic downgrade base
```

リビジョン番号を明示的に参照する必要がある場合は、以下のようにします。

```bash
uv run alembic upgrade 90e7511fbee5
```

git のコミットハッシュのように、リビジョンIDの最初の数文字を使用しても問題ありません。

### 相対的なアップグレード/ダウングレード

現在のバージョンからNバージョン移動するには、`+N` を指定します。

```bash
uv run alembic upgrade +2
```

ダウングレードには負の値を使用します。

```bash
uv run alembic downgrade -1
```

### 現在のバージョンを確認する

```bash
$ uv run alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
90e7511fbee5 (head)
```

### マイグレーションの履歴を確認する

```bash
$ uv run alembic history
90e7511fbee5 (head) -> None, create users table
```

`-r` オプションを利用して履歴の一部を表示することもできます。

```bash
uv run alembic history -r[start]:[end]
```

start と end には以下のいずれかを指定できます。

- base, current, head などの特別なキーワード
- リビジョンID（の一部）
- `+N`, `-N` の相対指定
