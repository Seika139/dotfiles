# Makefile

<!-- markdownlint-disable MD024 -->
<!-- markdownlint-disable MD025 -->
<!-- markdownlint-disable MD036 -->

makefile はプロジェクトのビルド、テスト、デプロイなどのタスクを自動化するための設定ファイルである。
当初は C や C++ のビルドに利用されていたが、その汎用性の高さから、様々なタスクを自動化するために使用されている。

## シェルスクリプトとの違い

どちらもタスクの自動化するために利用されるが、依存関係の管理や自動追跡、効率的なビルドがあるという点で Makefile の方がビルドに特化しているといえる。
シェルスクリプトはより汎用的なスクリプト言語で、Makefile よりも柔軟性が高い。
Makefile とシェルスクリプトを組み合わせて使用することも可能である。

# Makefile を実行するのに必要なもの

## make コマンド

make コマンドは、Makefile に記述されたルールに従って、指定されたターゲットをビルドするためのコマンドである。
Unix 系の OS（Linux、macOS など）には標準でインストールされていることが多い。

## Makefile

make コマンドは `Makefile` または `makefile` という名前のファイルを探し、その中に記述されたルールに従って処理を実行する。

**目次**

- [Makefile](#makefile)
  - [シェルスクリプトとの違い](#シェルスクリプトとの違い)
- [Makefile を実行するのに必要なもの](#makefile-を実行するのに必要なもの)
  - [make コマンド](#make-コマンド)
  - [Makefile](#makefile-1)
- [Makefile の書き方](#makefile-の書き方)
  - [ターゲット](#ターゲット)
  - [疑似ターゲット](#疑似ターゲット)
  - [依存ターゲット](#依存ターゲット)
  - [コマンドを持たないターゲット](#コマンドを持たないターゲット)
  - [変数の定義](#変数の定義)
    - [簡易代入と即時代入の違い](#簡易代入と即時代入の違い)
  - [コメントアウト](#コメントアウト)
  - [改行](#改行)
    - [行を分けると別のシェルで実行される](#行を分けると別のシェルで実行される)
  - [Makefile で `$` を使うときの注意点](#makefile-で--を使うときの注意点)
  - [変数を引き継ぐ](#変数を引き継ぐ)
  - [コマンドを表示しない方法](#コマンドを表示しない方法)
  - [自動変数](#自動変数)
    - [ターゲット名 `$@`](#ターゲット名-)
    - [最初の依存ターゲット名 `$<`](#最初の依存ターゲット名-)
    - [すべての依存ターゲット名 `$^` `$+`](#すべての依存ターゲット名--)
    - [ターゲットよりもタイムスタンプが新しい依存ターゲット `$?`](#ターゲットよりもタイムスタンプが新しい依存ターゲット-)
    - [ターゲットのパターンマッチに一致する部分 `$*`](#ターゲットのパターンマッチに一致する部分-)
  - [Makefile のデバッグ](#makefile-のデバッグ)
    - [make -n](#make--n)
    - [warning 関数](#warning-関数)
  - [エラーを無視する](#エラーを無視する)
  - [組み込み関数](#組み込み関数)
  - [条件分岐](#条件分岐)
    - [if 関数](#if-関数)
    - [ifeq ディレクティブ](#ifeq-ディレクティブ)
    - [ifdef ディレクティブ](#ifdef-ディレクティブ)
- [参考](#参考)

# Makefile の書き方

```plain
ターゲット: 依存ターゲット
    コマンド
```

これが makefile の基本構造である。
この構造を「ルール」と呼ぶ。
コマンドはレシピとも呼ばれ、ターゲットをビルドするために実行されるコマンドである。コマンドは必ず **タブ** でインデントする。

ルールは複数記述することができ、 make コマンドは `make <ターゲット>` を実行することで、指定されたターゲットに対してルールを適用する。

```bash
make <ターゲット1> <ターゲット2> ...
```

とすることで、複数のターゲットを同時に実行できる。

## ターゲット

ターゲットは、ビルドする対象や実行するタスクを示す名前である。

```makefile
hello: hello.c
    gcc -o hello hello.c
```

上記の例では、`hello` がターゲットであり、`hello.c` というソースファイルをコンパイルして `hello` という実行ファイルを生成することを示している。

このように、ターゲットは基本的にその名前のファイルがコマンドによって生成されることを意図している。

## 疑似ターゲット

ターゲットとして、実際に存在しないファイル名を指定することができる。疑似ターゲット以外にもタスクと呼ばれることもある。
疑似ターゲットの書き方は以下のようになる。

```makefile
.PHONY: clean
clean:
    rm -f *.o hello
```

`.PHONY 疑似ターゲット名` と書くことで、`make` に対してこのターゲットは疑似ターゲットであることを明示する。（phony:「偽の」「まやかしの」）
上記の例では、`clean` が疑似ターゲットであり、`make clean` を実行すると、`*.o` と `hello` を削除するコマンドが実行される。
`.PHONY` を宣言しなくてもコマンドを実行することはできるが、疑似ターゲット名と同じ名前のファイルが存在する場合はコマンドが実行されない。
そのため、`.PHONY` を宣言することで、ターゲット名と同じ名前のファイルが存在してもコマンドが実行されることを保証する。

以降の説明では便宜上、疑似ターゲットと対比して「存在するファイル」のターゲットのことを **ファイルターゲット** と呼ぶことにする。

## 依存ターゲット

依存ターゲットは、ターゲットをビルドするために必要なファイルや他のターゲットを示す。
例えば、下記の例では `hello` ターゲットは `hello.c` に依存している。

```makefile
hello: hello.c
    gcc -o hello hello.c
```

ここで makefile が優秀なのは、依存ターゲットが変更された場合にのみ、ターゲットを再ビルドすることができる点である。
`make hello` を実行すると、`make` はまず `hello.c` の最終更新日時を確認し、もし `hello.c` が `hello` よりも新しい場合、`hello` を再ビルドする。
そうでない場合、`hello` はすでに最新の状態であるため、再ビルドは行われない。

## コマンドを持たないターゲット

複数の依存ターゲットをまとめて 1 つのターゲットとして扱うときに用いる。

```makefile
.PHONY: rebuild
rebuild: clean build ;
```

`make rebuild` を実行すると、`clean` と `build` のターゲットが順番に実行される。

```makefile
.PHONY: rebuild
rebuild: clean build
    # ←この行はタブ文字＋空文字列でコマンド行がないことを表す
```

と書き直すこともできるが、分かりにくいのでセミコロンを使うことが多い。

```makefile
.PHONY: all
all: ;
```

このルールは文字通り何もしない。
もしこれが Makefile の先頭に書いてあれば `make` を実行しても何も実行されない。
適切なデフォルトターゲットがない場合にユーザの誤操作を防ぐことができる。

## 変数の定義

Makefile では変数を定義することができる。
変数を参照するときは `$(変数名)` や `${変数名}` のように書く。
変数は慣例的に大文字で書く。

```makefile
VERSION = 1.0.0
IMMEDIATE := $(VERSION)
CONDITIONAL ?= 1.0.1
```

- 簡易代入 (`=`): 遅延評価される。
- 即時代入 (`:=`): 定義時に評価される。
- 条件付き代入 (`?=`): 未定義の場合のみ代入される。

### 簡易代入と即時代入の違い

```makefile
VAR1 = $(VAR2)
VAR2 = Hello

all:
    echo $(VAR1)  # ここで初めて VAR1 が評価され、"Hello" と出力される
```

簡易代入 (`=`) は変数が参照されるときに評価される。
変数が使用されるたびに右辺が評価されるので、右辺にシェルコマンドを記述した場合は参照のたびにコマンドが実行される。

即時代入 (`:=`) は変数が定義された時点で評価される。
そのため、定義前の変数を参照すると空になる。
また、再帰的な参照はできない。
右辺にシェルコマンドを記述した場合は、変数が定義された時点でコマンドが実行されて変数に格納される。

一般的にはデバッグや可読性の観点から、即時代入 (`:=`) を使用することが推奨される。

## コメントアウト

Makefile では `#` を使ってコメントアウトする。 `#` から行末までがコメントとして扱われる。

```makefile
# コメント
all: # コメント
    echo "Hello, World!" # コメント
```

## 改行

複数の依存ターゲットを記述する場合、通常はスペースで区切って一行に記述するが、数が多くて見づらい場合は改行できる。
改行する際には、行末にバックスラッシュ `\` をつける。

```makefile
target: dependency1 dependency2 dependency3 \
        dependency4 dependency5
    command
```

1 つのターゲットに対して複数のコマンドを記述する場合、各コマンドは異なる行に記述し、行頭には必ずタブ文字 (Tab) を入れる。
コマンドの途中で改行したい場合は、依存ターゲットと同様に行末にバックスラッシュ `\` を記述する。
後続の行は、視認性のためにタブやスペースなどでインデントすることが推奨される。
必ずしもタブである必要はない。

```makefile
target: dependency
    command1 \
        --long-option argument1 \
        --another-long-option argument2
    command2
    command3
```

複数の短いコマンドを一行にセミコロン `;` で区切って記述できるが、可読性の観点からあまり推奨されない。

```makefile
target: dependency
    command1; command2; command3
```

### 行を分けると別のシェルで実行される

Makefile のコマンドは、デフォルトでは `/bin/sh` で実行される。
行を分けると、コマンドは別のシェルで実行されるため、環境変数やカレントディレクトリなどが引き継がれない。

```makefile
example:
    VAR=1
    echo "$$VAR"
```

```bash
make example # 空文字列が出力される

```

上記の例では、`VAR=1` と `echo $VAR` は別のシェルで実行されるため、変数 `VAR` が出力されない。
セミコロン `;` で区切ると同じシェルで実行されるが、1 行が長くなるのでバックスラッシュ `\` を使って改行する。

```makefile
example:
    VAR=1; \
    echo "$$VAR"
```

```bash
$ make example
1
```

## Makefile で `$` を使うときの注意点

先述の例のようにコマンド内で変数の参照を行うなどの用途で `$` を使う場合は `$$` と記述する必要がある。
これは、Makefile の中で `$` は変数の参照を示すため、シェルに渡すときには `$` をエスケープする必要があるためである。

下記のように `$` を 1 つだけ書くと、Makefile の変数 `$V` と文字列 `AR` として解釈される。

```makefile
example:
    VAR=1
    echo "$VAR"
```

## 変数を引き継ぐ

前項からも分かるように、makefile 内のコマンドは make 自身とは別のシェルプロセスで実行される。
コマンド内のプロセスは親プロセスである make の環境変数を一部継承するが、makefile 内で定義した変数はデフォルトでは子プロセスに引き継がれない。

`export` キーワードを makefile の変数の定義前に書くことで、その変数が環境変数としてマークされて子プロセスに引き継がれる。これはコマンドの実行後に消失するので、 make コマンド自体を実行するシェルには影響を与えない。

```makefile
MY_LOCAL_VAR := hello_from_make
export MY_ENV_VAR := hello_from_env

test:
    @echo "Local variable in make: $(MY_LOCAL_VAR)"
    @sh -c 'echo "Local variable in shell: $$MY_LOCAL_VAR"'
    @echo "Environment variable in make: $(MY_ENV_VAR)"
    @sh -c 'echo "Environment variable in shell: $$MY_ENV_VAR"'
```

```bash
$ make test
Local variable in make: hello_from_make
Local variable in shell:
Environment variable in make: hello_from_env
Environment variable in shell: hello_from_env
```

上記の例では、`MY_LOCAL_VAR` は makefile 内で定義されたローカル変数であり、子プロセスには引き継がれないため、シェル内では空文字列として扱われる。
`MY_ENV_VAR` は `export` でエクスポートされた環境変数であり、子プロセスに引き継がれるため、シェル内でも同じ値が表示される。

## コマンドを表示しない方法

makefile のコマンドは実行される前にそのコマンドが表示される。コメントアウトも表示される。
コマンドを表示しないようにするには、コマンドの先頭に `@` を付ける。
バックスラッシュで改行する場合は行が続いているので、改行した行の先頭に `@` を付ける必要はない。

```makefile
example:
    # これはコメント
    echo "Hello"
    @echo "World"
```

```bash
$ make example
# これはコメント
echo "Hello"
Hello
World
```

## 自動変数

Makefile には、ターゲットや依存ターゲットに関連する自動変数がある。

### ターゲット名 `$@`

```makefile
aaa/bbb/foo:
    @echo $@     # => aaa/bbb/foo
    @echo $(@)   # => aaa/bbb/foo
    @echo $(@D)  # => aaa/bbb
    @echo $(@F)  # => foo
```

### 最初の依存ターゲット名 `$<`

```makefile
output/foo: input/bar input/baz
    @echo $<     # => input/bar
    @echo $(<)   # => input/bar
    @echo $(<D)  # => input
    @echo $(<F)  # => bar
```

### すべての依存ターゲット名 `$^` `$+`

`$^` はすべての依存ターゲット名を、`$+` は重複を含むすべての依存ターゲット名を示す。

```makefile
output/foo: input/bar input/baz input/baz
    @echo $^     # => input/bar input/baz
    @echo $(^)   # => input/bar input/baz
    @echo $(^D)  # => input input
    @echo $(^F)  # => bar baz
    @echo $+     # => input/bar input/baz input/baz
    @echo $(+)   # => input/bar input/baz input/baz
    @echo $(+D)  # => input input input
    @echo $(+F)  # => bar baz baz
```

### ターゲットよりもタイムスタンプが新しい依存ターゲット `$?`

```makefile
# ファイル foo よりも bar の方がタイムスタンプが新しく、
# ファイル foo よりも baz の方がタイムスタンプが古い、という状況のとき
output/foo: input/bar input/baz
    @echo $?     # => input/bar
    @echo $(?)   # => input/bar
    @echo $(?D)  # => input
    @echo $(?F)  # => bar
```

### ターゲットのパターンマッチに一致する部分 `$*`

関連するファイルを作成するときなどに役立つ。

```makefile
# ファイル lib/foo.c があって `make lib/foo.o` をする状況のとき
%.o: %.c
    @echo $*     # => lib/foo
    @echo $(*)   # => lib/foo
    @echo $(*D)  # => lib
    @echo $(*F)  # => foo
```

## Makefile のデバッグ

### make -n

make コマンドに `-n` オプションを付けると、実行されるコマンドを表示することができる。
`-n` オプションは `--just-print` の略で、実際にはコマンドを実行せずに表示するだけである。

### warning 関数

`$(warning)` は、Makefile の中で警告メッセージを表示するための関数である。
これを利用して make コマンドの実行時に変数の値を確認できる。

```makefile
$(warning MAKE = $(MAKE))  # => Makefile:1: MAKE = /Library/Developer/CommandLineTools/usr/bin/make
```

## エラーを無視する

Makefile のコマンドは、エラーが発生するとその時点で処理が中断される。
エラーを無視して処理を続行するには、コマンドの先頭に `-` を付ける。
例えば、特定のプログラムが存在しない場合にエラーが返る可能性がある rm -f コマンドや、エラーが発生しても後続の処理に影響がない場合などに使用する。

## 組み込み関数

Makefile には組み込み関数があり、変数の操作や文字列の操作、ファイルの操作などを行うことができる。
組み込み関数は `$(関数名 引数)` の形式で使用する。
ここでは代表的なものを紹介する。

```makefile
$(words <string>)    # 文字列の単語数を返す
$(word <n> <string>) # 文字列の n 番目の単語を返す
$(sort <list>)       # リストから重複を削除し、ソートして返す
$(shell <command>)   # コマンドを実行して標準出力を返す(標準エラー出力は返さない)
$(dir <file>)        # ファイルのディレクトリ部分を返す
```

## 条件分岐

### if 関数

```makefile
$(if <条件>, <真の処理>, <偽の処理>)
```

条件を評価し、その結果が空ではない文字列だった場合には真、空の文字列だった場合には偽とする。
真だった場合には真の式を評価し、その結果を if 関数の評価とする。
偽だった場合には偽の式を評価し、その結果を if 関数の評価とする。
偽だった場合でも、偽の式がなければ何も評価されない。
真の式と偽の式はどちらか一方しか評価されない。

### ifeq ディレクティブ

```makefile
ifeq (<条件>, <比較対象>)
    <真の処理>
else
    <偽の処理>
endif
```

`<条件>` と `<比較対象>` が完全一致する場合に `<真の処理>` を実行し、そうでない場合は `<偽の処理>` を実行する。else と `<偽の処理>` は省略可能。

### ifdef ディレクティブ

```makefile
ifdef <変数名>
    <真の処理>
else
    <偽の処理>
endif
```

`<変数名>` が定義されている場合に `<真の処理>` を実行し、そうでない場合は `<偽の処理>` を実行する。else と `<偽の処理>` は省略可能。

# 参考

- [自動化のための GNU Make 入門講座 - Makefile の基本：ルール](https://objectclub.jp/community/memorial/homepage3.nifty.com/masarl/article/gnu-make/rule.html)
- [Makefile の特殊変数・自動変数の一覧 | 晴耕雨読](https://tex2e.github.io/blog/makefile/automatic-variables)
- [Makefile の書き方 #Makefile - Qiita](https://qiita.com/ktamido/items/74d831365da136a41cac)
- [Make 覚書 #Makefile - Qiita](https://qiita.com/Ro3jin/items/27170827707e5136ee89)
- [Makefile の基本](https://zenn.dev/keitean/articles/aaef913b433677)
- [いまさら make](https://zenn.dev/kusaremkn/articles/84005016fca5df121b8e)
