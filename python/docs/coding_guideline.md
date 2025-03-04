# Python Coding Guideline

> この引用部分はドキュメントにする際に削除する。
> Python を使用するプロジェクトにおいて、下記のようなガイドラインを共有し、チームのコード品質を向上させたいという意志で作成したドキュメント。

**目次**

- [Python Coding Guideline](#python-coding-guideline)
  - [概要](#概要)
    - [フォーマッタ](#フォーマッタ)
    - [リンター](#リンター)
      - [flake8](#flake8)
      - [mypy](#mypy)
      - [型ヒントと mypy](#型ヒントと-mypy)
  - [フォーマッタとリンターの使用方法](#フォーマッタとリンターの使用方法)
    - [CI ツール](#ci-ツール)
    - [Visual Studio Code の拡張機能](#visual-studio-code-の拡張機能)
    - [Python パッケージ](#python-パッケージ)

## 概要

プロジェクト内で使用される Python スクリプトについて、高品質なソースコードを書くために推奨することを記載したガイドライン。

以下で紹介する方法を導入するとことで [PEP8](https://peps.python.org/pep-0008/) と、
それをさらに拡張した [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md) に準拠したうえで、
さらに高品質なコーディングをサポートする。

### フォーマッタ

フォーマッタを使用すると、プログラマはコードスタイルの遵守に脳のリソースを割かず、ロジックの記述にフォーカスできるので、利用を推奨する。

| フォーマッタ | 概要                                   |
| :----------: | :------------------------------------- |
|   autopep8   | PEP8 に従うようにフォーマットする      |
|    isort     | import 文の順序をそろえる              |
|    black     | 一貫性と可読性の高いフォーマットをする |

autopep8 と black のフォーマット内容は競合するところがあるが、その場合は black のフォーマット結果を優先する。
black を利用していれば autopep8 で修正されるところはほとんどない。

### リンター

リンターとはソースコードを静的に（つまり実行する前に）解析してエラーなどをチェックするツールである。
フォーマッタで自動的に修正できない潜在的エラーの検出に利用する。

| リンター | 概要                               |
| :------: | :--------------------------------- |
|  flake8  | 論理エラーやスタイルをチェックする |
|   mypy   | 型ヒントに基づいた型チェックを行う |

設定ファイルとオプションを次のように設定する。

#### flake8

下記のコードをコピーしてプロジェクト内に `.flake8` というファイルを作成する。

```ini
[flake8]

# AVOID comments written in MULTI BYTE SEQUENCE, such as Japanese,
# which may cause error when executing autopep8 in Windows machine.

# E501: Limit the number of characters per line to 120.
# In cases where E501 is violated in patterns that cannot be automatically adjusted by black
# (e.g., strings or comment lines that fit better on a single line),
# do not enforce corrections even if a warning is issued.
# Note: Black formatter will break lines to fit within 88 characters,
# but flake8 is configured to issue warnings for lines exceeding 120 characters.
max-line-length = 120

# Ignore settings
# E402:
#   Allow imports outside the top level
#   for purposes such as conditional imports or avoiding circular dependencies
#
# E731:
#   No need to discourage the use of lambda expressions
#
# W503:
#   Recommend breaking lines before binary operators
#   and discourage W504 (breaking lines after binary operators)
ignore = E402,E731,W503
```

```bash
flake8 [解析するファイルパス]
```

flake8 で表示される警告のうち

```txt
E501 line too long (X > 120 characters)
```

についてはすべてを修正しなくてよい。
基本的に black フォーマッタによって１行あたりの文字数が 88 文字適切に改行がなされるはずであり、それでも 88 文字を超えた方がおさまりがよいと black が判断しているからである。
もちろん 88 文字を超えないように手動でコードを修正できればなおよい。

#### mypy

下記のコードをコピーしてプロジェクト内に `mypy.ini` というファイルを作成する。

```ini
[mypy]
ignore_missing_imports = True
explicit_package_bases = True
check_untyped_defs = True
cache_dir = .mypy_cache
```

```bash
mypy --install-types --non-interactive --show-traceback  --check-untyped-defs [解析するファイルパス]
mypy --install-types --non-interactive --show-traceback --strict [解析するファイルパス] # strict モードでチェックする場合
```

#### 型ヒントと mypy

mypy は Python 3.5 以降で使用できる型ヒントを利用して、コード内の型チェックを実施する。
型ヒントは静的解析に利用されるが、インタプリタの挙動には影響しない。
型ヒントはインタプリタバージョンによって記法が異なるため注意が必要である。

また、下記の理由で適切に型ヒントを書いていても警告されうる。

- ソースコードの import 元となる外部ライブラリが型ヒントに対応してない
- 新しい記法の型ヒントに対応していない

以上よりすべての警告を修正する必要はない。あくまで「ここは修正したほうがいい」という気付きを得るために使用する。

## フォーマッタとリンターの使用方法

1. CI ツール
2. VS Code の拡張機能
3. Python パッケージ

上記のいずれか（もしくは複数）を使用する。

### CI ツール

Jenkins や GitHub Actions などの CI ツールを利用して、プルリクエスト作成時にフォーマットやリントを実施する。

### Visual Studio Code の拡張機能

Visual Studio Code でコードを書く場合は次の拡張機能を使用すると、コマンドを実行せずとも保存時に自動的にフォーマットしてくれる。

| 拡張機能 | マーケットプレイス                                                              |
| :------: | :------------------------------------------------------------------------------ |
|  isort   | <https://marketplace.visualstudio.com/items?itemName=ms-python.isort>           |
|  black   | <https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter> |

上記の拡張機能を VS Code にインストールし、settings.json に下記の設定を追加する。

```json
{
     "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "isort.args": [
        "--profile",
        "black"
    ],
}
```

<details>
<summary><b>他にも Python を書く上で入れておくとよい拡張機能</b></summary>
<div>

|    拡張機能     | 概要                                                                                                             | マーケットプレイス                                                             |
| :-------------: | :--------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------- |
|     Python      | Microsoft が提供する Python 開発のための拡張機能。これを入れると Pylance と Python Debugger もインストールされる | <https://marketplace.visualstudio.com/items?itemName=ms-python.python>         |
|     Pylance     | コード補完、型チェック、リファクタリング、ドキュメントの表示などをしてくれる高性能な言語サーバー                 | <https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance> |
| Python Debugger | Python スクリプトにブレークポイントを設定してステップ実行できるリモートデバッグツール                            | <https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy>        |
| Python Debugger | パッケージの管理を容易にする                                                                                     | <https://marketplace.visualstudio.com/items?itemName=slightc.pip-manager>      |

</div>
</details>

リンターについては Pylance がその役割を果たしてくれる。

### Python パッケージ

**Windows**

Windows の Python ランチャーを利用してコードをフォーマットする。

```bash
py -m autopep8 -i --aggressive --aggressive [filepath]
py -m isort [filepath]
py -m black [filepath]
py -m flake8 [filepath]
py -m mypy --install-types --non-interactive --show-traceback --strict [filepath]
```

**mac / Linux**

```bash
autopep8 -i --aggressive --aggressive [filepath]
isort [filepath]
black [filepath]
flake8 [filepath]
mypy --install-types --non-interactive --show-traceback --strict [filepath]
```
