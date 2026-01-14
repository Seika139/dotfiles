# Go Modules

他のプログラミングと Go では「モジュール」や「パッケージ」の用語の意味が異なります。

一般的には「ライブラリ > パッケージ > モジュール」のように階層的に分類されますが、Go では「モジュール > パッケージ」のように分類されます。

※ ライブラリは Go ではあまり使われない用語です。

- [Go Modules](#go-modules)
  - [Module と Package](#module-と-package)
  - [go mod でプロジェクトを初期化する](#go-mod-でプロジェクトを初期化する)
  - [依存関係の整理](#依存関係の整理)

## Module と Package

以下に一般的な Go プロジェクトのディレクトリ構成例を示します。

```bash
project-root/      # プロジェクトのルートディレクトリ（モジュール）
├── go.mod         # モジュール定義ファイル
├── go.sum         # 依存関係のチェックサムファイル
├── pkg/           # パッケージを配置するディレクトリ
├── foo/           # fooパッケージ
│   └─ foo.go
├── bar/           # barパッケージ
│   └─ bar.go
└── main.go        # mainパッケージ
```

Go では関連する機能をまとめたものを「パッケージ」と呼びます。
上記の例では `pkg/foo` ディレクトリに `foo` パッケージがあり、`pkg/bar` ディレクトリに `bar` パッケージがあります。

一方、`go.mod` ファイルが存在するディレクトリ（この場合は project-root）から始まる一連のパッケージ群を「モジュール」と呼びます。

つまり、上記の例では project-root ディレクトリがモジュールのルートディレクトリとなり、その下にある `pkg/foo` と `pkg/bar` の両方のパッケージが同じモジュールに属しています。

## go mod でプロジェクトを初期化する

Go Modules を使用するには、まずプロジェクトのルートディレクトリで `go mod init` コマンドを実行して `go.mod` ファイルを作成します。これは uv の `pyproject.toml` や Node.js の `package.json` を作成してプロジェクトの初期化を行う操作に相当します。

```bash
go mod init <module-name> # github.com/username/project-name
```

`<module-name>` にはモジュールの名前を指定します。
モジュールを公開して配布する想定がある場合は、`go.mod` ファイルのモジュール名としてリポジトリの URL を指定することが一般的です。

## 依存関係の整理

Go Modules では、`go.mod` ファイルと `go.sum` ファイルを使用して依存関係を管理します。プロジェクト内で使用されていないパッケージを削除したり、依存関係を最新の状態に保つためには、以下のコマンドを使用します。

```bash
go mod tidy
```

Go では先にコードにインポート文を書き、その後で `go mod tidy` を実行することで、必要な依存関係が自動的に `go.mod` と `go.sum` に追加されます。
Python や Javascript のように、先に依存関係を宣言してからコードを書くという流れとは対照的です。

当ディレクトリでは UUID をパッケージ [main.go](./main.go) を用意しています。
このコードには外部パッケージ `github.com/google/uuid` をインポートしています。

```go
import "github.com/google/uuid"
```

このように標準のライブラリ以外のパッケージをインポートした場合、`go mod tidy` を実行すると自動的に `go.mod` と `go.sum` に依存関係が追加されます。もしパッケージが標準のライブラリのみであれば `go.sum` は作られません。

```bash
go mod tidy
# go.mod と go.sum に依存関係が追加される
```
