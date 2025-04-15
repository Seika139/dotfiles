# Dockerfile

<!-- markdownlint-disable MD036 -->

※ [Dockerfile の概要 | Docker ドキュメント](https://docs.docker.com/build/concepts/dockerfile/)

- [Dockerfile](#dockerfile)
  - [Dockerfile の基本](#dockerfile-の基本)
  - [最初の行](#最初の行)
  - [FROM](#from)
  - [ベースイメージ](#ベースイメージ)
    - [Docker Hub](#docker-hub)
    - [他のレジストリ](#他のレジストリ)
    - [自前のイメージ](#自前のイメージ)
    - [他のビルドステージで利用したイメージ](#他のビルドステージで利用したイメージ)
  - [WORKDIR](#workdir)
  - [COPY](#copy)
    - [source](#source)
    - [destination](#destination)
    - [--from](#--from)
  - [ADD](#add)
  - [RUN](#run)
    - [Shell form と Exec form の違い](#shell-form-と-exec-form-の違い)
    - [--mount](#--mount)
      - [--mount=type=bind](#--mounttypebind)
      - [--mount=type=cache](#--mounttypecache)
      - [--mount=type=secret](#--mounttypesecret)
  - [CMD](#cmd)
  - [ARG](#arg)
    - [ARG のスコープ](#arg-のスコープ)
    - [FROM との相互作用](#from-との相互作用)
    - [注意点](#注意点)
  - [ENV](#env)
    - [ENV のスコープ](#env-のスコープ)
    - [ARG との相互作用](#arg-との相互作用)
  - [VOLUME](#volume)

## Dockerfile の基本

- Docker イメージをビルドするための指示書
- イメージの構築に必要な一連の命令（コマンド）を記述する
- 拡張子なしの `Dockerfile` という名前で保存する

## 最初の行

Dockerfile の最初の行にパーサーディレクティブを記述することが推奨されている。

```dockerfile
# syntax=docker/dockerfile:1
```

上記のように宣言することで Docker の BuildKit が最新の安定バージョンの Dockerfile syntax を使用してビルドを行う。

## FROM

```dockerfile
FROM <イメージ名>:<タグ>
FROM <イメージ名>:<タグ> AS <エイリアス名>
```

イメージのビルドはベースイメージに対して命令を実行して何らかの機能を追加し独自のイメージを作成することを指す。
その大元となるベースイメージを指定するのが `FROM` 命令である。

## ベースイメージ

ベースイメージの所在は主に下記の通りである。

### Docker Hub

基本的には Docker Hub にあるイメージを指定する。
Docker Hub は Docker 社が提供する公式のイメージリポジトリであり、さまざまなアプリケーションやサービスの公式イメージが公開されている。

### 他のレジストリ

Docker Hub 以外のレジストリにあるイメージを指定することもできる。
例えば、Google Container Registry や Amazon Elastic Container Registry などのクラウドプロバイダが提供するレジストリを利用することができる。

```dockerfile
FROM <レジストリのURL>/<イメージ名>:<タグ>
```

### 自前のイメージ

ローカルに保存されている自前のイメージを指定することもできる。

### 他のビルドステージで利用したイメージ

マルチステージビルドを利用する場合、他のビルドステージで利用したイメージを指定することもできる。

```dockerfile
FROM <イメージ名>:<タグ> AS <エイリアス名>
```

このようにすることで、ビルドステージ間でのファイルの受け渡しが可能になる。

## WORKDIR

```dockerfile
WORKDIR <ディレクトリ名>
```

以降の命令を `<ディレクトリ名>` で指定したディレクトリ内で実行する。
`<ディレクトリ名>` が存在しない場合は自動的に作成される。

WORKDIR 命令は複数回使用することができ、各命令の実行時に指定したディレクトリに移動する。
相対パスを指定した場合は、前の WORKDIR 命令で指定したディレクトリを基準にして移動する。
例えば、以下のように記述した場合は `/app/src` ディレクトリに移動する。

```dockerfile
WORKDIR /app
WORKDIR src
```

WORKDIR を使用しない場合、デフォルトの作業ディレクトリは `/` になる。
ただし、ベースイメージを使用している場合はそのイメージのデフォルトの作業ディレクトリが使用される。

## COPY

```dockerfile
COPY [オプション] <source>... <destination>

# パスにスペースが含まれる場合は下記のようにする
COPY [オプション] ["<source>", ... "<destination>"]
```

ビルドコンテキストからイメージ内の指定した場所にファイルやディレクトリをコピーする。
`<source>` はビルドコンテキスト内のパスを指定し、`<destination>` はイメージ内のパスを指定する。

### source

後述の `from` オプションを使用しない場合は `<source>` にはビルドコンテキスト内のファイルやディレクトリを指定する。
ビルドコンテキストとは `docker build` コマンドを実行する際に指定するディレクトリ、つまり Dockerfile が存在するディレクトリのことを指す。
`docker build` コマンドを実行する際に `-f` オプションで Dockerfile のパスを指定しない場合は、カレントディレクトリがビルドコンテキストとなる。

`<source>` はビルドコンテキストのルートからの相対パスで指定する。

下記のように複数の `<source>` を指定することもできる。

```dockerfile
COPY ./src ./doc /app/
```

### destination

`<destination>` はイメージ内のパスを指定する。
`<destination>` が存在しない場合は自動的に作成される。

`<destination>` は絶対パスまたは相対パスで指定することができる。
相対パスの場合は、前の WORKDIR 命令で指定したディレクトリを基準にして移動する。
例えば、以下のように記述した場合は `/app/src/` ディレクトリにコピーされる。

```dockerfile
WORKDIR /app
COPY ./src src/
```

ファイルをコピーする場合は末尾に `/` があるかないかで挙動が異なるので注意する。

```dockerfile
# abs というファイルに text.txt の内容がコピーされる
COPY test.txt abs

# abs/test.txt というファイルに test.txt の内容がコピーされる
COPY test.txt abs/

# abs ディレクトリに directory/ の内容がコピーされる（どっちでも同じ）
# つまり directory/text1.text は abs/text1.text になる
COPY directory abs
COPY directory abs/
```

### --from

`COPY` 命令は `--from` オプションを使用することで、イメージ、ビルドステージ、または名前付きコンテキストからファイルをコピーできる。

```dockerfile
COPY [--from=<image|stage|context>] <src> ... <dest>
```

マルチステージビルドのビルドステージからコピーするには、コピー元のステージ名を指定する。
下記の例では `scratch` ステージにおいて、`build` という名前のビルドステージから `/hello` を `/` にコピーしている。

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine AS build
COPY . .
RUN apk add clang
RUN clang -o /hello hello.c

FROM scratch
COPY --from=build /hello /
```

## ADD

```dockerfile
ADD [OPTIONS] <src> ... <dest>
ADD [OPTIONS] ["<src>", ... "<dest>"]
```

ADD 命令は、`COPY` と同様にファイルやディレクトリをイメージ内にコピーする命令だが、追加の機能がある。
これらの追加機能を利用する場合は `ADD` 命令を使用し、逆に使用しない場合は `COPY` 命令を使用することが推奨されている。

**追加の機能**

- ローカルの tar アーカイブを自動的に展開する
- リモート URL からファイルをダウンロードする
- Git リポジトリからファイルをクローンする

## RUN

RUN 命令は現在のイメージに対してコマンドを実行して新しいレイヤーを追加する。
下記のように Shell form と Exec form の 2 つの形式で記述することができる。

```dockerfile
# Shell form:
RUN [OPTIONS] <command> ...
# Exec form:
RUN [OPTIONS] [ "<command>", ... ]
```

### Shell form と Exec form の違い

一般的には、シンプルなコマンドや環境変数を使用する場合は Shell 形式が使いやすく、特定のシェル以外で実行したい場合やシェル処理を避けたい場合は Exec 形式を選ぶとよい。
詳細は <https://docs.docker.com/reference/dockerfile/#shell-and-exec-form> を参照。

**Shell form**

- シェル（デフォルトでは`/bin/sh -c`）を通して実行される
- 環境変数の展開やパイプ（`|`）、コマンドの連結（`&&`、`||`、`;`）などのシェル機能が使える
- 改行エスケープやヒアドキュメントを使って長いコマンドを複数行に分割できる

  ```dockerfile
  # 改行エスケープ
  RUN echo "Hello, World!" \
      && echo "This is a multi-line command."

  # ヒアドキュメント
  RUN <<EOF
  apt-get update
  apt-get install -y curl
  apt-get install -y git
  EOF
  ```

**Exec form**

- JSON 配列構文を使用し、シェルを介さずに直接実行される
- ダブルクォート（`"`）を使用する必要がある（シングルクォートは不可）
- 環境変数の展開などのシェル処理は自動的に行われない

### --mount

```dockerfile
RUN --mount=[type=<TYPE>][,option=<value>[,option=<value>]...]
```

#### --mount=type=bind

ファイルやディレクトリをビルドコンテナにバインドマウントする。基本的には読み取り専用。

```dockerfile
RUN --mount=type=bind,target=<マウントパス>,source=<ソースパス>,from=<ステージ名> <コマンド>
```

- `target`, `dst`, `destination`: マウント先のパスを指定する。
- `source`: `from` で指定したビルドステージのパスを指定する。
- `from`: `COPY` 命令と同様に、イメージ、ビルドステージ、または名前付きコンテキストを指定することができる。指定しない場合は、ビルドコンテキストのパスを指定する。
- `rw`, `readwrite`: マウントへの書き込みを許可する。（書き込まれたデータは破棄される）

#### --mount=type=cache

ビルド間で永続的なキャッシュを提供し、パッケージマネージャやコンパイラのキャッシュを高速化する。

```dockerfile
RUN --mount=type=cache,target=<キャッシュパス> <コマンド>
```

- `target`, `source`, `from` については `bind` と同様。
- `id`: キャッシュの識別子を指定する。省略した場合は、`<target>` のパスが使用される。
- `mode`: キャッシュディレクトリの権限を 8 進数で指定する。デフォルトは 0755。

#### --mount=type=secret

ビルドコンテナがトークンやプライベートキーなどの機密情報にアクセスできるようにする。

```dockerfile
RUN --mount=type=secret,id=<シークレットID>,target=<マウントパス> <コマンド>
```

- `id`: シークレットの ID（デフォルトは target のベース名）
- `target`, `dst`, `destination`: マウント先のパスを指定する。デフォルトでは `/run/secrets/<id>` にマウントされる。
- `required`: `true`の場合、シークレットが利用できないとエラーになる（デフォルトは `false`）

## CMD

コンテナが起動したときに実行されるコマンドを指定する。
RUN はイメージのビルド時に実行されるコマンドであるのに対し、CMD はコンテナの実行時に実行されるコマンドである。
複数の CMD 命令を指定した場合、最後の CMD 命令が有効になる。

```dockerfile
# 起動時に node ./src/index.js を実行する
CMD ["node", "./src/index.js"]
```

CMD 命令も RUN 命令と同様に Shell form と Exec form の 2 つの形式で記述することができが、CMD 命令は Exec form を使用することが推奨されている。

## ARG

ARG 命令はビルド時に使用する変数を定義するための命令である。

```dockerfile
ARG <name>[=<default value>] [<name>[=<default value>]...]
```

### ARG のスコープ

ARG は`Dockerfile`内で宣言された行から有効になる。
グローバルスコープで宣言された ARG は自動的にビルドステージに継承されない。

```dockerfile
# グローバルスコープでの宣言
ARG NAME="joe"

FROM alpine
# この時点ではNAME変数にアクセスできない
RUN echo "hello ${NAME}!"
```

ビルドステージで使用するには、そのステージ内で再度宣言する必要がある。

```dockerfile
# グローバルスコープでの宣言
ARG NAME="joe"

FROM alpine
# ビルドステージで変数を利用する
ARG NAME
RUN echo $NAME
```

### FROM との相互作用

ARG は FROM 命令の前に記述できる唯一の命令である。
FROM の前に宣言された ARG は、最初の FROM の後では使用できない。

```dockerfile
ARG CODE_VERSION=latest
FROM base:${CODE_VERSION}
```

FROM の前に宣言された ARG をビルドステージ内で使用するには、そのステージ内で再度宣言する必要がある。

```dockerfile
ARG VERSION=latest
FROM busybox:$VERSION
ARG VERSION
RUN echo $VERSION > image_version
```

### 注意点

ARG は機密情報を扱うためのものではない。ビルド引数は `docker history` コマンドで表示され、イメージに添付されるプロヴェナンス証明書にも含まれる可能性がある。
機密情報を安全に扱うには、`RUN --mount=type=secret` を使用する。

## ENV

ENV 命令は環境変数を定義するための命令である。環境変数はビルド時だけでなく、作成されたイメージから起動されたコンテナ内でも永続化される。
環境変数は `docker inspect` コマンドで確認することができる。

```dockerfile
ENV <key>=<value> [<key>=<value>...]
```

### ENV のスコープ

ENV 命令は Dockerfile 内で宣言された行から有効になり、それ以降の全ての命令、ビルドステージで有効になる。

### ARG との相互作用

ENV は同じ名前の ARG よりも優先される。

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
ENV CONT_IMG_VER=v1.0.0
RUN echo $CONT_IMG_VER
```

上記の例では、`docker build --build-arg CONT_IMG_VER=v2.0.1` としてビルドしても `CONT_IMG_VER` は `v1.0.0` になる。

下記のように ARG と ENV を組み合わせて使用することで、ビルド時に設定可能な環境変数を作成できる。

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
# ARG で指定された値がない場合はデフォルト値を使用する
ENV CONT_IMG_VER=${CONT_IMG_VER:-v1.0.0}
RUN echo $CONT_IMG_VER
```

## VOLUME

Dockerfile の VOLUME 命令は、コンテナ内にマウントポイントを作成し、外部からマウントされる匿名ボリュームを保持する場所としてマークするための命令である。

ボリュームマウントの詳細は [006_storage.md](006_storage.md) を参照。

```dockerfile
# JSON配列形式、またはプレーンな文字列で指定する
VOLUME ["/data"]
VOLUME /var/log /var/db
```
