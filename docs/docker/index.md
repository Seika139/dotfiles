# イメージ・コンテナの管理

poetry で Python のソースコードを管理しつつ、作成したソースコードを Docker コンテナ上で実行するケースを例にしながら、Docker のイメージ・コンテナの管理方法を説明します。

プロジェクトの構成は以下のようになっていると仮定します。

```plaintext
.
├── Dockerfile
├── compose.yml
├── pyproject.toml
├── poetry.lock
├── Makefile
├── src
│   └── main.py
└── tests
    └── test_main.py
```

**compose.yml** は以下のような内容です。

```yml
project:
  build:
    context: .
    dockerfile: Dockerfile
  volumes:
    - .:/app # ホストのカレントディレクトリをコンテナの/appにマウントします
```

## イメージ

Dockerイメージは、アプリケーションの実行に必要なファイルシステムのスナップショットです。
ソースコードや依存関係が変更された場合、Dockerイメージを更新する必要があります。

```bash
docker compose build
docker compose build <service_name> # 特定のサービスのみをビルドする
```

## コンテナ

コンテナは Docker イメージを実行したインスタンスです。
コンテナ自体を直接「更新」するという概念はあまりありません。
通常は、新しいイメージを作成し、その新しいイメージから新しいコンテナを起動することで更新を行います。

```bash
docker compose up -d # バックグラウンドでコンテナを起動する。
docker compose up    # フォアグラウンドでコンテナを起動する。ログなどを確認したい場合に使う。
docker compose up -d <service_name> # 特定のサービスのみを起動
```

ただし、実行中のコンテナ内で設定ファイルなどを変更した場合、それはコンテナ固有の状態となります。
これらの変更を永続化したい場合は、以下のいずれかの方法を検討します。

- ボリュームの使用:
  - ホストPCのディレクトリやDockerの管理するボリュームをコンテナにマウントし、設定ファイルなどの永続化したいデータをボリュームに保存します。
- 設定の外部化:
  - 環境変数や外部設定ファイル（コンテナ起動時にマウントするなど）を利用し、コンテナイメージ自体を変更せずに設定を調整できるようにします。
- 新しいイメージへの反映:
  - コンテナ内での変更が重要な場合は、その状態を反映した新しいイメージを作成することを検討します（推奨される頻度は低いですが、docker commit コマンドで可能です）。

```bash
docker compose down # コンテナを停止して削除する
docker compose down --volumes/-v # compose.yml で定義された名前付きボリュームを削除する
docker compose down --rmi all # コンテナとボリューム、イメージを削除する
```
