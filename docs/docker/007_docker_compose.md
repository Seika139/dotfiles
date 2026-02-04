# Docker Compose

Docker Compose は、複数の Docker コンテナを定義し、管理するためのツールである。
`compose.yaml` という設定ファイルを利用してサービスを定義し、単一のコマンドで全てを起動、停止、管理できる。

※ `docker-compose.yml` は古い書き方で、最近は `compose.yml` または `compose.yaml` が推奨されている。
※ `compose.yml` の書き方が最近変わったので、調べたときや AI が生成するものに古い書き方が混ざりがちなので注意。

- [Docker Compose](#docker-compose)
  - [特に重要なコマンド](#特に重要なコマンド)
  - [compose.yml の基本構造](#composeyml-の基本構造)
  - [version (deprecated)](#version-deprecated)
  - [name (top-level element)](#name-top-level-element)
  - [services (top-level element)](#services-top-level-element)
    - [build](#build)
    - [command](#command)
    - [configs](#configs)
    - [context](#context)
    - [depends\_on](#depends_on)
    - [env\_file](#env_file)
    - [environment](#environment)
    - [healthcheck](#healthcheck)
    - [image](#image)
    - [init](#init)
      - [init を使うメリット](#init-を使うメリット)
    - [networks](#networks)
    - [platform](#platform)
    - [ports](#ports)
    - [expose](#expose)
    - [pull\_policy](#pull_policy)
    - [restart](#restart)
    - [secrets](#secrets)
    - [tty](#tty)
    - [user](#user)
    - [volumes](#volumes)
    - [working\_dir](#working_dir)
  - [networks (top-level element)](#networks-top-level-element)
    - [ipam](#ipam)
  - [volumes (top-level element)](#volumes-top-level-element)
  - [configs \& secrets (top-level element)](#configs--secrets-top-level-element)

## 特に重要なコマンド

`compose.yml` に定義されているすべてのサービスを開始する。

```bash
docker compose up
```

実行中のサービスを停止して削除する。

```bash
docker compose down
```

実行中のコンテナの出力を監視して問題をデバッグする場合は、次のコマンドでログを表示する。
とくに、実行中のコンテナの出力を監視する場合は、`-f` オプションをつけると便利。

```bash
docker compose logs
```

すべてのサービスとその現在のステータスを一覧表示する。

```bash
docker compose ps
```

すべての Compose CLI コマンドの完全なリストについては、 [リファレンスドキュメント](https://docs.docker.com/reference/cli/docker/compose/) を参照。

## compose.yml の基本構造

かなり長いが、マスターするためにはこれくらいは必要。
ここでは代表的なセクションのみを紹介する。全部のセクションを知る場合は [Services top-level elements | Docker Docs](https://docs.docker.com/reference/compose-file/services/) を参照。

```yml
name: <project-name>

services:
  app:
    image: node:18-alpine
    pull_policy: never
    build:
      context: .
      dockerfile: ./Dockerfile
      secrets:
        - secret1
    commands:
      - npm install
      - npm run dev
    configs:
      - config1
    ports:
      - "${PORT:-8080}:80"
    working_dir: /app
    volumes:
      - type: bind
        source: .
        target: /app
    depends_on:
      - db

  db:
    platform: linux/amd64
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: todos
    healthcheck:
      test: "mysqladmin ping -h localhost"
      interval: 3s
      retries: 5
      start_period: 10s
    volumes:
      - type: volume
        source: db_data
        target: /var/lib/mysql
    restart: always
    networks:
      ipv4:
        ipv4_address: 192.168.2.0

networks:
  ipv4:
    ipam:
      driver: default
      config:
        - subnet: 192.168.0.0/21

volumes:
  db_data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/db_data
      o: bind

configs:
  config1:
    file: ./config1.txt

secrets:
  secret1:
    file: ./secret1.txt
```

## version (deprecated)

`version` は、Compose ファイルのバージョンを指定するオプションだが、最新の docker compose では非推奨となっている。
そのため、`version` セクションは書かない。

## name (top-level element)

プロジェクト名を指定する。
指定しない場合は compose.yml ファイルのあるディレクトリ名がプロジェクト名として使用される。

- `services` セクションは、アプリケーションの各サービスを定義する。
- `app` はサービスの名前で、任意の名前を付けることができる。
- `image` は使用する Docker イメージを指定する。

## services (top-level element)

`services` セクションは、アプリケーションの各サービスを定義する。
上記の例では、`app` と `db` の 2 つのサービスが定義されている。

### build

`build` セクションは、Dockerfile を使用してイメージをビルドするための設定を指定する。

詳細は [Compose Build Specification | Docker Docs](https://docs.docker.com/reference/compose-file/build/) を参照。

- `context` はビルドコンテキストを指定する。通常はプロジェクトのルートディレクトリを指定する。
- `dockerfile` は使用する Dockerfile のパスを指定する。ビルドコンテキスト内の相対パスで指定する。
- `secrets` はビルド時に使用するシークレットを指定する。シークレットは `secrets` セクションで定義されている必要がある。
- `args` はビルド時に渡す引数を指定する。これにより、Dockerfile 内の ARG 命令を上書きする。
- `target` はマルチステージビルドを使用する場合に、特定のビルドステージを指定するために使用する。

### command

`Dockerfile` 等で指定されるコンテナイメージのデフォルトコマンド `CMD` を上書きする。

### configs

イメージをリビルドせずにサービスの動作を調整できる。
サービスは `configs` で明示的に許可された設定にのみアクセスできる。
これはコンテナ起動時に Linux の場合は `/<config_name>`、Windows の場合は `C:\<config_name>` にマウントされることで実現される。このファイルのアクセス権はデフォルトで `0444` である。

### context

Dockerfile のビルドコンテキスト、またはリポジトリルートを指定する。（デフォルトは `.`）

指定された値が相対パスの場合、プロジェクトディレクトリからの相対パスとして解釈される。
ビルドコンテキストの定義に絶対パスを使用すると、Compose ファイルの移植性が損なわれるため、Compose は警告を表示する。

厳密には Docker イメージをビルドするときに Docker デーモンに送信されるファイルとディレクトリのセットを指す。

```plain
project-root
|__ docker
|   |__ Dockerfile
|   |__ compose.yml
|__ src
    |__ main.py
    |__ __init__.py
```

このようなディレクトリ構造の場合に、`src` ディレクトリ内のファイルをビルドコンテキストに含むためにはコンテキストに `..` を指定してリポジトリ全体をビルドコンテキストに含める必要がある。

```yml
build:
  context: ..
  dockerfile: docker/Dockerfile
```

### depends_on

`depends_on` セクションでサービスの起動順序を指定することができる。
これは、サービスが密接に連携しており、起動順序がアプリケーションの機能に影響を与える場合に便利である。
上記の例では、`app` サービスは `db` サービスに依存しているため、`db` サービスが起動してから `app` サービスが起動する。逆にサービスを停止する場合は、`app` サービスが先に停止される。

### env_file

`env_file` 属性は、コンテナに渡される環境変数を含む 1 つ以上のファイルを指定するために使用される。

```yml
env_file:
  - .env
  - ./config/.env
```

絶対パスを使用すると Compose ファイルの移植性が損なわれるため、compose ファイルのあるディレクトリからの相対パスを使用することが推奨される。
複数のファイルで同じ環境変数が定義されている場合、後に指定されたファイルの値が優先される。
`environment` セクションで宣言された環境変数はこれらの値を上書きする。値が空または未定義の場合でも、これは当てはまる。

### environment

コンテナに設定される環境変数を定義する。
配列形式またはマップ形式で指定できる。

```yml
# 配列形式
environment:
  - ENV_VAR1=value1
  - ENV_VAR2=value2

# マップ形式
environment:
  ENV_VAR1: value1
  ENV_VAR2: value2
```

### healthcheck

サービスコンテナが「正常」かどうかを判断するために実行されるチェックを宣言する。

- `test` は、コンテナのヘルスチェックを実行するコマンドを指定する。
- `interval` は、ヘルスチェックを実行する間隔を指定する。デフォルトは `30s`。
- `retries` は、ヘルスチェックが失敗した場合に再試行する回数を指定する。デフォルトは `3`。
- `start_period` は、コンテナが起動してからヘルスチェックを開始するまでの待機時間を指定する。デフォルトは `0s`。
- `timeout` は、ヘルスチェックコマンドのタイムアウト時間を指定する。デフォルトは `30s`。

### image

コンテナを起動するためのイメージを指定する。 `build` セクションでビルド方法を指定している場合は、`image` セクションは省略できる。

### init

コンテナ内で PID 1 として初期化プロセスを使用するために指定する。

<!-- markdownlint-disable MD033 -->

<details>
<summary>PID 1 とは</summary>
<div>

コンピューター内では全てのプロセスにプロセス ID (PID) が割り当てられる。
OS が起動したときに最初に立ち上がる特別なプロセスには PID 1 が割り当てられる。
このプロセスは、他の全てのプロセスの親プロセスとなり、システム全体の管理を行う。
たとえば、子プロセスが途中で動かなくなった場合（これを「ゾンビプロセス」と呼ぶ）、親プロセスがそれを検知して適切に処理する必要がある。

Docker コンテナは、OS の一部を切り取って作ったような独立した小さな世界であり、この中でもアプリケーションなどの主要なプロセスが動いている。
デフォルトの状態ではコンテナの中で最初に起動するプロセス（例えば、アプリケーションの実行ファイルなど）が PID 1 として動くことが多く、この場合は本来 PID 1 が持つべき責任（ゾンビプロセスの回収など）を、そのアプリケーションのプロセス自身が行う必要がある。

多くのアプリケーションは、このようなシステムの管理作業を専門としていないため、ゾンビプロセスがそのまま残り続け、コンテナのリソースを無駄に消費してしまう可能性がある。

そこで、`init` オプションを指定することで、コンテナ内で PID 1 として初期化プロセスを使用することができる。

```bash
docker container run --init [その他のオプション] イメージ名
```

この初期化プロセスは、`tini` という小さなプログラムをベースにしており、PID 1 として必要な以下の重要な役割をしっかりと果たす。

- ゾンビプロセスの回収: コンテナ内で動いている他のプロセスが途中で終了し、ゾンビプロセスになった場合、この初期化プロセスがそれを検知して適切に処理（回収）する。これにより、コンテナのリソースが無駄に消費されるのを防ぐ。
- シグナルの転送: コンテナを停止させるための命令（シグナル）が Docker から送られた場合、この初期化プロセスはそれをコンテナ内の適切なプロセスに正しく伝えて、安全なシャットダウンを促す。

</div>
</details>

#### init を使うメリット

- コンテナの安定性向上
  - ゾンビプロセスが溜まってリソースを圧迫するのを防ぎ、コンテナが安定して動作する可能性が高まる。
- プロセスの正常な終了
  - コンテナを停止させる際に、初期化プロセスが適切なプロセスに終了の指示を送ることで、アプリケーションが予期せぬ中断をせずに、後処理などを行ってから安全に終了できる可能性が高まる。
- PID 1 の責任を分離
  - アプリケーションのプロセスは本来の仕事に集中でき、システムの管理という余計な負担から解放される。

### networks

サービスコンテナが接続するネットワークを定義し、 `networks` セクションの最上位要素以下の内容を参照する。
networks については後述する。

### platform

サービスコンテナが実行されるターゲットプラットフォームを指定する。
これを指定しない場合、Docker はホストマシンのネイティブプラットフォームを使用する。

```yml
# 例
platform: darwin
platform: windows/amd64
platform: linux/arm64/v8
```

### ports

- 参照: [Docker Docs](https://docs.docker.com/reference/compose-file/services/#ports)

通常、インターネットやホストマシンのようにコンテナの外部からコンテナ内のサービスには直接アクセスできない。
そこでホストマシンの特定のポートをコンテナのポートに接続すると、コンテナの内外で双方向に通信が可能になる。
このようにコンテナ内外で通信を可能にするために何番のポートを何番のポートに接続するかを決めることをポートフォワーディングまたはポートマッピングと呼ぶ。
`ports` セクションは、ホストマシンとコンテナ間のポートマッピングを定義する。

例えばコンテナ内でウェブサーバーを80番ポートで起動しているとする。
ホストマシンの8080番ポートをコンテナの80番ポートにマッピングすると、ホストマシンの8080番ポートにアクセスすることで、コンテナ内のウェブサーバーにアクセスできるようになる。
つまり、ブラウザで `http://localhost:8080` にアクセスすると、コンテナ内のウェブサーバーが応答する。

```yml
# Short syntax
ports:
  - "8080:80"

# Long syntax
ports:
  - published: 8080
    target: 80
    protocol: tcp # tcp または udp。デフォルトは tcp
    mode: host
```

**docker compose run コマンドを使用する場合の注意点**

`docker compose run` コマンドはワンショットであるため、他のインスタンスとの衝突を防ぐためにポートマッピングが無効化される。
そのため、`docker compose run`を使用してサービスコンテナを起動する場合、`ports` セクションで定義されたポートマッピングは適用されない。
`docker compose run --service-ports` オプションを使用すると、`ports` セクションで定義されたポートマッピングを有効にできる。
ただし、複数のインスタンスを同時に起動する場合、ポートの競合が発生する可能性があるため注意が必要である。

**Short syntax**

`[HOST:]CONTAINER[/PROTOCOL]` の形式で指定する。常に引用符で囲む必要がある。

- `HOST`: `[IP:](ポート番号、またはその範囲)`
  - ホストマシンの IP アドレスとポート番号を指定する。省略した場合は全ての IP アドレスが対象となる。（`0.0.0.0`）
- `CONTAINER`: `(ポート番号、またはその範囲)`
  - コンテナ内のポート番号を指定する。
- `PROTOCOL`: `tcp` または `udp`。省略した場合はデフォルト値として `tcp` が使用される。

※ HOST と CONTAINER の両方でポート番号の範囲を指定する場合、同じ数のポートを指定する必要がある。
※ HOST のポート番号を省略した場合、Docker はランダムな空きポートをホストマシン側で割り当てる。

```yml
# 例
ports:
  - "3000" # コンテナの 3000 番ポートをホストマシンのランダムな空きポートにマッピング
  - "3000-3005" # コンテナの 3000-3005 番ポートをホストマシンのランダムな空きポート範囲にマッピング
  - "8000:8000" # ホストマシンの 8000 番ポートをコンテナの 8000 番ポートにマッピング
  - "9090-9091:8080-8081" # ホストマシンの 9090-9091 番ポートをコンテナの 8080-8081 番ポートにマッピング
  - "49100:22" # ホストマシンの 49100 番ポートをコンテナの 22 番ポートにマッピング
  - "8000-9000:80" # ホストマシンの 8000-9000 番ポートのすべてをコンテナの 80 番ポートにマッピング
  - "127.0.0.1:8001:8001" # ホストマシンのローカルホストの 8001 番ポートをコンテナの 8001 番ポートにマッピング
  - "127.0.0.1:5000-5010:5000-5010" # ホストマシンのローカルホストの 5000-5010 番ポートをコンテナの 5000-5010 番ポートにマッピング
  - "::1:6000:6000" # ホストマシンのローカルホストの IPv6 アドレスの 6000 番ポートをコンテナの 6000 番ポートにマッピング
  - "[::1]:6001:6001" # ホストマシンのローカルホストの IPv6 アドレスの 6001 番ポートをコンテナの 6001 番ポートにマッピング
  - "6060:6060/udp" # ホストマシンの 6060 番ポートをコンテナの 6060 番ポートにマッピング（UDPプロトコル）
```

**Long syntax**

Long Syntax を利用すると、Short Syntax では指定できない追加のオプションを設定できる。

- `target`: コンテナ内のポート番号を指定する。
- `published`: ホストマシンのポート番号を指定する。
- `host_ip`: ホストマシンの特定の IP アドレスを指定する。省略した場合は全ての IP アドレスが対象となる。（`0.0.0.0`）
- `protocol`: `tcp` または `udp`。省略した場合はデフォルト値として `tcp` が使用される。
- `mode`: Swarm セットアップでポートを公開する方法を指定する。
- `name`: サービス内でのポートの使用状況を文書化するために使用される、人間が判読できるポートの名前。

```yml
# 例
ports:
  - name: web
    target: 80
    host_ip: 127.0.0.1
    published: "8080"
    protocol: tcp
    app_protocol: http
    mode: host

  - name: web-secured
    target: 443
    host_ip: 127.0.0.1
    published: "8083-9000" # 8083から9000までの範囲のポートがすべて443にマッピングされる
    protocol: tcp
    app_protocol: https
    mode: host
```

### expose

`expose` セクションは、コンテナ内で実行されているサービスがリッスンしているポートを他のコンテナに公開するために使用される。
`ports` セクションと異なり、`expose` で指定されたポートはホストマシンには公開されない。
これは、同じ Docker ネットワークに接続されている他のコンテナからのみアクセス可能であることを意味する。
例えば compose.yml ファイル内で Web アプリケーションとデータベースを起動する際にデータベースのポートを `expose` で指定すると Web アプリケーションからはデータベースにアクセスできるが、ホストマシンからは直接データベースにアクセスできない。

**注**: expose セクションを利用しなくても、そもそも同じネットワーク内のコンテナ間ではポートはデフォルトで開放されているため、`expose` セクションはあくまでドキュメント的な意味合いが強い。

```yml
services:
  web:
    image: my-web-app
    ports:
      - "80:80"
  db:
    image: my-database
    expose:
      - "5432"
```

### pull_policy

イメージをプルする開始する際のポリシーを指定する。

- `always`: 常にレジストリからイメージをプルする
- `never`: レジストリからイメージをプルせず、プラットフォームのキャッシュを使用する。キャッシュされたイメージがない場合はエラーになる。
- `missing (default)`: キャッシュされたイメージがない場合のみ、レジストリからイメージをプルする。キャッシュが存在する場合はそれを使用する。`if_not_present` と同じ動作をするが、こちらは古い書き方。
- `build`: イメージをビルドする。既にイメージがある場合もビルドする。
- `daily`: 最後のプルから 24 時間以上経過している場合にイメージをプルする。
- `weekly`: 最後のプルから 7 日以上経過している場合にイメージをプルする。

### restart

コンテナの終了時にプラットフォームが適用するポリシーを定義する。

- `no`: コンテナが終了しても再起動しない。デフォルトの動作。
- `always`: コンテナが終了した場合、常に再起動する。

詳細は [docker container run | Docker Docs](https://docs.docker.com/reference/cli/docker/container/run/#restart) を参照。

### secrets

トップレベル要素の `secrets` セクションで定義されたシークレットをサービスに渡す。
コンテナの実行時に使用するシークレットはこちらを使用し、ビルド時のみに使用するシークレットは `build` セクションで指定する。

secrets は `/run/secrets` ディレクトリにマウントされ、コンテナ内のアプリケーションはこのパスを通じてシークレットにアクセスできる。
そのため、下記の例では `/run/secrets/mysql_root_password` というパスでシークレットにアクセスできる。

※注: この例は機密情報の取り扱いとしては適切なものではない。

```yml
services:
  app:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/mysql_root_password
    secrets:
      - mysql_root_password

secrets:
  mysql_root_password:
    file: ./my_secret.txt
```

### tty

サービスのコンテナを tty モードで実行するように設定する。

### user

コンテナ内で実行されるプロセスのユーザーを指定する。
デフォルトはイメージによって指定され、設定されていない場合は root ユーザーで実行される。

### volumes

サービスコンテナからアクセス可能なマウントホストパスまたは名前付きボリュームを定義する。
マウントがホストパスであり、単一のサービスでのみ使用される場合は、サービス定義の一部として宣言できる。
ボリュームを複数のサービスで共有する場合は、最上位のボリュームセクションで定義する必要がある。

### working_dir

`Dockerfile` で指定された作業ディレクトリ `WORKDIR` を上書きする。

## networks (top-level element)

サービス間の通信を管理する。

※ [Networks top-level elements | Docker Docs](https://docs.docker.com/reference/compose-file/networks/)

ネットワークについての詳細は [008_network.md](./008_network.md) を参照。

### ipam

カスタム IPAM 設定を指定する。

- `driver`: デフォルトではない、カスタム IPAM ドライバーを指定する。
- `config`: 0 個以上の構成要素を持つリスト。各構成要素には次のものが含まれます。
  - `subnet`: ネットワークセグメントを表す CIDR 形式のサブネット
  - `ip_range`: コンテナ IP を割り当てる IP の範囲
  - `gateway`: マスターサブネットの IPv4 または IPv6 ゲートウェイ
  - `aux_addresses`: ネットワークドライバがホスト名から IPv4 または IPv6 へのマッピングとして使用する補助的な IPv4 または IPv6 アドレス
- `options`: キーと値のマッピングとしてのドライバー固有のオプション。

## volumes (top-level element)

`volumes` セクションは、サービス間で共有されるボリュームを定義する。
指定しない場合はコンテナエンジンのデフォルト設定が使用される。

ボリュームマウントについては [006_storage.md](./006_storage.md) を参照。

## configs & secrets (top-level element)

各サービスコンテナ内にファイルがマウントされることで、コンテナが configs と secrets にアクセスできるようになる。
secrets は機密情報を扱うのに特化した configs という位置付けである。

configs はコンテナの `/<config_name>` にマウントされる。
secrets はコンテナの `/run/secrets/<secret_name>` にマウントされる。
どちらもデフォルトでは mode 0444 でマウントされる。

```yml
configs:
  config1:
    file: ./config1.txt

secrets:
  secret1:
    file: ./secret1.txt
```
