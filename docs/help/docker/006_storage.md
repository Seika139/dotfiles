# Storage

Docker コンテナ内で作成されたすべてのファイルは、読み取り専用のイメージレイヤーの上にある書き込み可能なコンテナレイヤーに保存される。

※ [004_layer.md](./004_layer.md) を参照

コンテナが破棄されると、コンテナレイヤーも削除されるため、コンテナ内で作成されたファイルは失われる。
そのため、コンテナ内で作成されたファイルを永続化するためにはコンテナの外に保存する必要がある。
それを実現するための仕組みはいくつかあり、ここでは代表的な「ボリュームマウント」と「バインドマウント」について説明する。

- [Storage](#storage)
  - [docker compose の Long syntax と Short syntax](#docker-compose-の-long-syntax-と-short-syntax)
    - [Long syntax](#long-syntax)
    - [Short syntax](#short-syntax)
  - [ボリュームマウント](#ボリュームマウント)
    - [ボリュームマウントのユースケース](#ボリュームマウントのユースケース)
    - [匿名ボリュームと名前付きボリューム](#匿名ボリュームと名前付きボリューム)
      - [名前付きボリュームを推奨するケース](#名前付きボリュームを推奨するケース)
      - [匿名ボリュームを推奨するケース](#匿名ボリュームを推奨するケース)
    - [docker コマンドでのボリュームマウント](#docker-コマンドでのボリュームマウント)
    - [Dockerfile でのボリュームマウント](#dockerfile-でのボリュームマウント)
    - [docker compose でのボリュームマウント](#docker-compose-でのボリュームマウント)
    - [ボリュームの削除](#ボリュームの削除)
    - [未使用のボリュームをすべて削除する](#未使用のボリュームをすべて削除する)
  - [バインドマウント](#バインドマウント)
    - [バインドマウントのユースケース](#バインドマウントのユースケース)
    - [docker コマンドでのバインドマウント](#docker-コマンドでのバインドマウント)
    - [Dockerfile でのバインドマウント](#dockerfile-でのバインドマウント)
    - [docker compose でのバインドマウント](#docker-compose-でのバインドマウント)
    - [consistency](#consistency)
  - [tmpfs マウント](#tmpfs-マウント)
  - [参考](#参考)

## docker compose の Long syntax と Short syntax

先ず、docker compose でのボリュームマウントとバインドマウントの定義方法に Long syntax と Short syntax の 2 種類があることを説明する。
実は Long syntax と Short syntax では裏で異なる動作をする。
エラーの発見しやすさや可読性の観点から Long syntax の使用が推奨されている。

### Long syntax

```yml
volumes:
  # ホストの ./data ディレクトリをコンテナの /app/data にバインドマウントする
  - type: bind
    source: ./data
    target: /app/data

  # 名前付きボリューム my_volume をコンテナの /app/volume_data にマウントする
  - type: volume
    source: my_volume
    target: /app/volume_data

  # 匿名ボリュームをコンテナの /app/anon_volume_data にマウントする
  - type: volume
    target: /app/anon_volume_data

volumes:
  my_volume: # 名前付きボリュームを使う場合はトップレベルの volumes セクションで定義する
```

### Short syntax

```yml
volumes:
  # ホストの ./data ディレクトリをコンテナの /app/data にバインドマウントする
  - ./data:/app/data

  # 名前付きボリューム my_volume をコンテナの /app/volume_data にマウントする
  - my_volume:/app/volume_data

  # 匿名ボリュームをコンテナの /app/anon_volume_data にマウントする
  - /app/anon_volume_data

volumes:
  my_volume: # 名前付きボリュームを使う場合はトップレベルの volumes セクションで定義する
```

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
名前付きボリュームではコンテナ起動時にその名前のボリュームが存在しない場合は新規作成され、存在する場合は既存のボリュームが使用される。
一方で匿名ボリュームでは、コンテナ起動時に常に新しいボリュームが作成される。

#### 名前付きボリュームを推奨するケース

- データベースやアプリケーションのアップロードファイルなど、永続化が必要なデータを保存する場合。
- 複数のコンテナ間でデータを共有する場合。
- ボリュームの管理やバックアップを容易にしたい場合。

#### 匿名ボリュームを推奨するケース

- 一時的なデータやキャッシュなど、永続化が不要なデータを保存する場合。
- コンテナのライフサイクルに合わせてデータを管理したい場合。
- 高速化が必要な一時領域を作る。
  - バインドマウントだと遅いディレクトリを、Docker管理下（Linuxネイティブ速度）に逃がす際に使います。

```yml
# 匿名ボリュームの例（node_modulesをホストから隔離する定番手法）
services:
  web:
    build: .
    volumes:
      - .:/app # バインドマウント（ソースコード用）
      - /app/node_modules # 匿名ボリューム（ホストの同名フォルダで上書きされるのを防ぐ）
```

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

### ボリュームの削除

| コマンド                              | 説明                                                                                 |
| :------------------------------------ | :----------------------------------------------------------------------------------- |
| `docker compose stop`                 | 実行中のコンテナを停止する                                                           |
| `docker compose down`                 | コンテナを停止して削除するがボリュームは削除しない                                   |
| `docker compose down --volumes/-v`    | compose.yml で定義されたボリュームを削除する                                         |
| `docker volume rm <volume-name>`      | 指定した名前のボリュームを削除する                                                   |
| `docker volume ls`                    | すべてのボリュームの一覧を表示する                                                   |
| `docker volume inspect <volume-name>` | 指定した名前のボリュームの詳細情報を表示する                                         |
| `docker compose run --rm`             | 新しいコンテナを起動してコマンドを実行し、終了後にコンテナと匿名ボリュームを削除する |

### 未使用のボリュームをすべて削除する

```bash
docker volume prune
```

このコマンドを実行すると「実行中・停止中のコンテナに紐づくボリューム」以外の未使用のボリュームが匿名・名前付き問わずすべて削除される。

```bash
# 匿名ボリュームの形式（64文字ハッシュ）に一致するものだけを削除するコマンド
docker volume rm $(docker volume ls -qf dangling=true | command grep -E '^[a-f0-9]{64}$')
```

## バインドマウント

バインドマウントは、ホストのファイルシステム上の特定のディレクトリをコンテナにマウントする仕組みである。
バインドマウントでは方スト上からもコンテナ内からも同じファイルにアクセスできるため、どちらかの環境で変更を加えると、もう一方の環境でも変更が反映される。

**パスの指定方法**

- `src` (source): ホスト上のディレクトリのパスを指定する。これは絶対パス、または compose ファイルからの相対パスで指定する。（GitHub で共有される場合は相対パスがおすすめ）
- `dst` (destination) または `target`: コンテナ内のマウントポイントを指定する。

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

### consistency

macOS や Windows の Docker Desktop でのみ適用される設定。
macOS や Windows では、Linux カーネル上で動く Docker とホスト OS の間でファイルシステムが異なるため、ファイルを共有する際にオーバーヘッド（負荷）が発生する。
特に node_modules や vendor ディレクトリのように、大量の小さなファイルを頻繁に読み書きする開発環境では、この同期処理がボトルネックとなり、動作が非常に重くなることがある。
そのような場合に、`consistency` オプションを使用してホスト OS とコンテナ間でファイルシステムの整合性をどのように扱うか指定する。

- `consistent` (デフォルト): ホストとコンテナ間でファイルシステムの整合性を保証する。
- `cached`:
  - コンテナがホストのファイルシステム情報をキャッシュする。
  - コンテナがホストのファイルを読み取り操作が高速化されるが、ホストの変更がコンテナに即座に反映されない可能性がある。
  - ソースコードの編集など、ホスト側で頻繁に変更が行われる場合に有効。
- `delegated`:
  - コンテナ側の書き込みを優先し、ホストへの同期を後回しにする。
  - コンテナによる書き込み操作が高速化されるが、コンテナの変更が即座にホストへ反映されない可能性がある。
  - ログや一時ファイル出力など、コンテナ側で頻繁にファイルを作成・更新する場合に有効。

**例**

```yml
# Short syntax の場合
services:
  web:
    image: node:20
    volumes:
      # ホストのソースコードを読み込む際は 'cached' がおすすめ
      - .:/app:cached
      # 大量のログを書き出すような場合は 'delegated' がおすすめ
      - ./logs:/app/logs:delegated

# Long syntax の場合
services:
  web:
    image: node:20
    volumes:
      - type: bind
        source: .
        target: /app
        consistency: cached
      - type: bind
        source: ./logs
        target: /app/logs
        consistency: delegated
```

## tmpfs マウント

tmpfs マウントは、コンテナの一時的なデータ保存に使用されるメモリ内のファイルシステムを提供する仕組み。

- メモリ上にデータを展開するため、ディスクへの書き込みが発生しない。
- 物理ディスクを消耗させず、読み書きが圧倒的に速いが、その代わりホストのメモリを消費する。コンテナを止めると中身はきれいさっぱり消える。

tmpfs マウントは、コンテナのライフサイクルにわたってデータを保持しないため、一時的なデータやキャッシュの保存に適している。

```yml
services:
  frontend:
    image: node:lts
    volumes:
      # tmpfs マウントをコンテナの /app/tmpfs_data にマウントする
      - type: tmpfs
        target: /app/tmpfs_data
```

## 参考

- [Volumes | Docker Docs](https://docs.docker.com/engine/storage/volumes/)
- [Bind mounts | Docker Docs](https://docs.docker.com/engine/storage/bind-mounts/)
- [Services top-level elements | Docker Docs](https://docs.docker.com/reference/compose-file/services/#volumes)
- [Docker の Volume がよくわからないから調べた #docker-compose - Qiita](https://qiita.com/aki_55p/items/63c47214cab7bcb027e0)
- [Docker のボリュームのマウントのされ方についてちょっとまとめました #Ubuntu - Qiita](https://qiita.com/daemokra/items/322270091cf41a853226)
- [Compose ファイル version 3 リファレンス — Docker-docs-ja 24.0 ドキュメント](https://docs.docker.jp/compose/compose-file/compose-file-v3.html#volumes)
- [ボリューム・マウント（共有ファイルシステム）のためのパフォーマンス・チューニング — Docker-docs-ja 19.03 ドキュメント](https://docs.docker.jp/docker-for-mac/osxfs-caching.html)
