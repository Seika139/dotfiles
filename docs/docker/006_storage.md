# Storage

Docker コンテナ内で作成されたすべてのファイルは、読み取り専用のイメージレイヤーの上にある書き込み可能なコンテナレイヤーに保存される。

※ [004_layer.md](./004_layer.md) を参照

コンテナが破棄されると、コンテナレイヤーも削除されるため、コンテナ内で作成されたファイルは失われる。
そのため、コンテナ内で作成されたファイルを永続化するためにはコンテナの外に保存する必要がある。
それを実現するための仕組みはいくつかあり、ここでは代表的な「ボリュームマウント」と「バインドマウント」について説明する。

- [Storage](#storage)
  - [ボリュームマウント](#ボリュームマウント)
    - [ボリュームマウントのユースケース](#ボリュームマウントのユースケース)
    - [匿名ボリュームと名前付きボリューム](#匿名ボリュームと名前付きボリューム)
    - [docker コマンドでのボリュームマウント](#docker-コマンドでのボリュームマウント)
    - [Dockerfile でのボリュームマウント](#dockerfile-でのボリュームマウント)
    - [docker compose でのボリュームマウント](#docker-compose-でのボリュームマウント)
      - [volumes の書き方](#volumes-の書き方)
    - [未使用のボリュームをすべて削除する](#未使用のボリュームをすべて削除する)
  - [バインドマウント](#バインドマウント)
    - [バインドマウントのユースケース](#バインドマウントのユースケース)
    - [docker コマンドでのバインドマウント](#docker-コマンドでのバインドマウント)
    - [Dockerfile でのバインドマウント](#dockerfile-でのバインドマウント)
    - [docker compose でのバインドマウント](#docker-compose-でのバインドマウント)
  - [参考](#参考)

## ボリュームマウント

ボリュームマウントは、Docker Daemon が管理するストレージ領域にデータを保存する仕組みである。

ボリュームデータはホスト上のファイルシステムに保存される。（例： Linux の場合は `/var/lib/docker/volumes`）
しかし、ボリューム内のデータを操作するには、ボリュームをコンテナにマウントする必要がある。
ボリュームデータへの直接アクセスや操作はサポートされておらず、未定義の動作であり、ボリュームまたはそのデータが予期せぬ方法で破損する可能性がある。

ボリュームは、パフォーマンスが重視されるデータ処理や長期保存のニーズに最適である。
ストレージの場所はデーモンホスト上で管理されるため、ボリュームはホストファイルシステムに直接アクセスする場合と同等のファイルパフォーマンスを提供する。

### ボリュームマウントのユースケース

- ホストマシンに依存しないのでバインドマウントよりも移植性が高い。
- Docker CLI コマンドまたは Docker API を使用してボリュームを管理できる。
- アプリケーションで高パフォーマンスの I/O が必要な場合。

### 匿名ボリュームと名前付きボリューム

ボリュームは、匿名ボリュームと名前付きボリュームの 2 種類に分類される。
匿名ボリュームにはランダムな名前が付けられ、その名前は特定の Docker ホスト内で一意であることが保証される。
`docker run` コマンドでコンテナを起動する際に `--rm` オプションを指定すると、コンテナが停止したときに匿名ボリュームも削除される。

### docker コマンドでのボリュームマウント

`docker run --mount` または `docker run -v` / `docker run --volume` を使用する。 `--mount` の方が新しいオプションで推奨されている。

```bash
docker run --mount type=volume[,src=<volume-name>],dst=<mount-path>
docker run --volume <volume-name>:<mount-path>
```

- `src`: ボリュームの名前を指定する。省略した場合は匿名ボリュームが作成される。
- `dst`: コンテナ内のマウントポイントを指定する。

### Dockerfile でのボリュームマウント

Dockerfile では `VOLUME` 命令を使用して匿名ボリュームを定義することができる。

```dockerfile
VOLUME [<mount-path>]
```

- `<mount-path>`: コンテナ内のマウントポイントを指定する。

### docker compose でのボリュームマウント

docker compose では `volumes` セクションを使用してボリュームを定義することができる。

```yml
services:
  frontend:
    image: node:lts
    volumes:
      - app:/home/node/app

volumes:
  app:
```

上記の例では `docker compose up` を始めて実行したときに `app` という名前のボリュームが作成され、コンテナの `/home/node/app` にマウントされる。2 回目以降の実行時には、すでに作成されたボリュームがマウントされる。
`docker compose down` を実行してもボリュームは削除されない。ボリュームを削除するには、`docker compose down --volumes` を実行する。

#### volumes の書き方

volumes の書き方は Short syntax と Long syntax の 2 種類がある。

Short syntax は簡潔に書けるが、Long syntax の方がオプション指定の自由度が高く設定が明示できて可読性が高い。

<!-- markdownlint-disable MD036 -->

**Short syntax**

```yml
services:
  frontend:
    image: node:lts
    volumes:
      - app:/home/node/app # ボリューム名:マウントパス
```

**Long syntax**

```yml
services:
  frontend:
    image: node:lts
    volumes:
      - type: volume
        source: app
        target: /home/node/app
```

### 未使用のボリュームをすべて削除する

```bash
docker volume prune
```

## バインドマウント

バインドマウントは、ホストのファイルシステム上の特定のディレクトリをコンテナにマウントする仕組みである。
バインドマウントでは方スト上からもコンテナ内からも同じファイルにアクセスできるため、どちらかの環境で変更を加えると、もう一方の環境でも変更が反映される。

### バインドマウントのユースケース

- Docker ホスト上の開発環境とコンテナ間でソース コードまたはビルド成果物を共有する。
- コンテナ内にファイルを作成または生成し、そのファイルをホストのファイルシステムに保存する場合。
- ホストマシンからコンテナへの設定ファイルの共有。Docker コンテナ上で DNS 解決をする場合、ホストマシンから各コンテナに `/etc/resolv.conf` をマウントする。

### docker コマンドでのバインドマウント

```bash
docker run --mount type=bind,src=<host-path>,dst=<container-path>
```

### Dockerfile でのバインドマウント

```dockerfile
RUN --mount=type=bind,target=<マウントパス>,source=<ソースパス>,from=<ステージ名> <コマンド>
```

詳細は [005_dockerfile.md](./005_dockerfile.md) を参照

### docker compose でのバインドマウント

```yml
services:
  app:
    volumes:
      - type: bind
        source: <host-path>
        target: <container-path>
```

## 参考

- [Volumes | Docker Docs](https://docs.docker.com/engine/storage/volumes/)
- [Bind mounts | Docker Docs](https://docs.docker.com/engine/storage/bind-mounts/)
- [Services top-level elements | Docker Docs](https://docs.docker.com/reference/compose-file/services/#volumes)
- [Docker の Volume がよくわからないから調べた #docker-compose - Qiita](https://qiita.com/aki_55p/items/63c47214cab7bcb027e0)
- [Docker のボリュームのマウントのされ方についてちょっとまとめました #Ubuntu - Qiita](https://qiita.com/daemokra/items/322270091cf41a853226)
