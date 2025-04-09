# Poetry

poetry で Python プロジェクトを開始・運用する際の手順をまとめる。
poetry 自体の運用に Python3.9 以上が必要なことに注意する。

- [Poetry](#poetry)
  - [poetry 自体のインストール](#poetry-自体のインストール)
  - [プロジェクトを始める](#プロジェクトを始める)
    - [1. 作成済みのプロジェクトをクローンして始める場合](#1-作成済みのプロジェクトをクローンして始める場合)
    - [2. ドキュメント内にあるインストーラを活用する](#2-ドキュメント内にあるインストーラを活用する)
    - [3. ドキュメント内にあるインストーラを活用する(インストーラをプロジェクトに配置しない場合)](#3-ドキュメント内にあるインストーラを活用するインストーラをプロジェクトに配置しない場合)
    - [4. インストーラを利用せずにプロジェクトを始める](#4-インストーラを利用せずにプロジェクトを始める)
  - [パッケージ管理](#パッケージ管理)
  - [仮想環境](#仮想環境)
    - [poetry が v2.0.0 以上の場合](#poetry-が-v200-以上の場合)
    - [poetry が v2.0.0 未満の場合](#poetry-が-v200-未満の場合)
    - [IDE のインタープリタに仮想環境を設定する](#ide-のインタープリタに仮想環境を設定する)
  - [各種ライブラリおよび python の実行方法](#各種ライブラリおよび-python-の実行方法)
  - [poetry プロジェクトのディレクトリ構成](#poetry-プロジェクトのディレクトリ構成)
    - [`__init__.py`](#__init__py)
      - [1. 空のままにする](#1-空のままにする)
      - [2. パッケージ内のモジュールやクラスをインポートする](#2-パッケージ内のモジュールやクラスをインポートする)
      - [3. 初期化コードを追加する](#3-初期化コードを追加する)
    - [ユニットテスト](#ユニットテスト)
      - [テストコードの例](#テストコードの例)
      - [pytest の機能](#pytest-の機能)
      - [パラメータ化テスト](#パラメータ化テスト)
      - [フィクスチャ](#フィクスチャ)
  - [設定ファイルの解説](#設定ファイルの解説)
    - [.python-version](#python-version)
    - [pyproject.toml](#pyprojecttoml)
    - [poetry.lock](#poetrylock)
    - [.editorconfig](#editorconfig)

## poetry 自体のインストール

> ※ 後述の「[1. 作成済みのプロジェクトをクローンして始める場合](#1-作成済みのプロジェクトをクローンして始める場合)」または「[2. ドキュメント内にあるインストーラを活用する](#2-ドキュメント内にあるインストーラを活用する)」に該当する場合は、その手順に poetry のインストールが含まれているので、ここではスキップして良い。

<https://python-poetry.org/docs/> を参照して、poetry をインストールするのが確実。

[../setup_scripts/pyenv_and_poetry/copy_into_project/setup_dev_windows.bash](../setup_scripts/pyenv_and_poetry/copy_into_project/setup_dev_windows.bash) に書かれているように

```bash
curl -sSL https://install.python-poetry.org | python3 -
# Windows の Python ランチャーを使用している場合は下記のコマンドを実行する
curl -sSL https://install.python-poetry.org | py -3 -
```

を実行してインストールしても良い。

## プロジェクトを始める

場合に応じて下記のいずれかの手順でプロジェクトを始める。

### 1. 作成済みのプロジェクトをクローンして始める場合

このドキュメント群に準拠してプロジェクトが作られいている場合はプロジェクト開始用のスクリプトがあるはずなのでそれを実行する。
詳細はクローンしたプロジェクト内のドキュメントを参照する。

```bash
cd [project_dir]
bash ./scripts/setup_XXX.sh # OS によってスクリプト名が異なる
```

### 2. ドキュメント内にあるインストーラを活用する

このドキュメント群内にあるインストーラを利用してプロジェクトを作成する。

```bash
# 任意のディレクトリにプロジェクト用のディレクトリを作成する
cd [somewhere]
mkdir [project_name]
```

[../my_utils/scripts/](../my_utils/scripts/) 内のファイルを `project_name/scripts` ディレクトリにコピーする。

```bash
# プロジェクト用のディレクトリに移動する
$ cd [project_name]

# scripts フォルダがあることを確認する
$ ls
scripts/

# 現在のディレクトリをプロジェクトにする（直下に pyproject.toml などが作られる）
# -n オプションで対話的なプロンプトをスキップする
$ poetry init -n

$ ls
pyproject.toml  scripts/
```

[../my_utils/pyproject.toml](../my_utils/pyproject.toml) の内容をコピーして `pyproject.toml` に貼り付け、適宜編集する。

同時に下記のファイルもコピーしてプロジェクトに配置する。

- [../my_utils/.python-version](../my_utils/.python-version) (必須)
- [../my_utils/.editorconfig](../my_utils/.editorconfig) (任意)

プロジェクトで使用する python インタプリタバージョンを変更する場合は `.python-version` の内容を変更すること。

```bash
# インストーラを利用して依存関係をインストールする
$ bash scripts/setup_XXX.sh # OS によってスクリプト名が異なる
```

### 3. ドキュメント内にあるインストーラを活用する(インストーラをプロジェクトに配置しない場合)

このドキュメント群内にあるインストーラを利用してプロジェクトを作成するが、インストーラのスクリプトをプロジェクトに配置しない場合はこちらの手順に従う。

```bash
# 任意のディレクトリにプロジェクト用のディレクトリを作成する
cd [somewhere]
mkdir [project_name]
$ cd [project_name]

# 現在のディレクトリをプロジェクトにする（直下に pyproject.toml などが作られる）
# -n オプションで対話的なプロンプトをスキップする
$ poetry init -n

# pyproject.toml が作成されていることを確認する
$ ls
pyproject.toml
```

[../my_utils/pyproject.toml](../my_utils/pyproject.toml) の内容をコピーして `pyproject.toml` に貼り付け、適宜編集する。

同時に下記のファイルもコピーしてプロジェクトに配置する。

- [../my_utils/.python-version](../my_utils/.python-version) (必須)
- [../my_utils/.editorconfig](../my_utils/.editorconfig) (任意)

プロジェクトで使用する python インタプリタバージョンを変更する場合は `.python-version` の内容を変更すること。

```bash
# インストーラを利用して依存関係をインストールする
# OS によってスクリプト名が異なる
# 引数にプロジェクトのパスを指定すること
$ bash ~/dotfiles/setup_scripts/pyenv_and_poetry/general/setup_dev_XXX.bash [project_path]
```

### 4. インストーラを利用せずにプロジェクトを始める

ここまでに使用した自作のインストーラを使用しない場合はこの手順に従う。

```bash
# 現在のディレクトリ下に my-project を作る
poetry new my-project

# 現在のディレクトリをプロジェクトにする（直下に pyproject.toml などが作られる）
# -n オプションで対話的なプロンプトをスキップする
poetry init -n
```

## パッケージ管理

pip コマンドでパッケージをインストールするのと同じ感覚で poetry コマンドを使用してパッケージを管理する。

```bash
# プロジェクトに新しい依存関係を追加する
poetry add numpy pandas

# プロジェクトから依存関係を削除する
poetry remove numpy pandas

# すべての依存関係を最新バージョンに更新する
poetry update

# pyproject.toml に基づいて依存関係をインストールする
poetry install
```

依存関係を更新すると、`pyproject.toml` と `poetry.lock` が更新される。
`poetry.lock` はプロジェクトの依存関係を固定するためのファイルで、他の開発者が同じ環境を再現できるようにするために使用されるので、 git 管理している場合はコミットに含めること。

## 仮想環境

poetry のバージョンでコマンドが異なるので初めにバージョンを確認しておく。

```bash
poetry --version
```

### poetry が v2.0.0 以上の場合

公式ページの情報をもとに書いています

- [Commands | Documentation | Poetry](https://python-poetry.org/docs/cli)
- [Managing environments | Documentation | Poetry](https://python-poetry.org/docs/managing-environments/)

```bash
# 現在のシェルで仮想環境をアクティブにするコマンドを出力する
# このコマンド自体が仮想環境をアクティブにするわけではない
poetry env activate

# 現在のプロジェクトに対して新しい仮想環境をアクティブ化、または作成する
poetry env use


poetry env info # 現在アクティブになっている仮想環境の情報を表示する
poetry env info --path # 現在アクティブになっている仮想環境のパスを表示する
poetry env list # 現在のプロジェクトに関連付けられた仮想環境を一覧表示する

# 仮想環境の削除
# 現在アクティブになっている仮想環境を削除すると、自動的に非アクティブになる。
poetry env remove [env_name] # 指定した仮想環境を削除する
poetry env remove --all # すべての仮想環境を削除する
```

### poetry が v2.0.0 未満の場合

```bash
poetry shell # 仮想環境を起動する
python [file] # 仮想環境内で python を実行
exit # 仮想環境を終了する
```

### IDE のインタープリタに仮想環境を設定する

IDE のインタープリタに仮想環境を設定することで、IDE 内で仮想環境を使用することができる。

- [PyCharm](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html)
- [VSCode](https://code.visualstudio.com/docs/python/environments#_creating-a-virtual-environment)

VS Code の場合は、コマンドパレットを開いて `Python: Select Interpreter` を選択し、仮想環境のパスを選択することで設定できる。
VS Code の機能で仮想環境を作ることもできるが、poetry で作成した仮想環境を使用する場合は、この機能は使用しないこと。

## 各種ライブラリおよび python の実行方法

仮想環境を明示的にアクティベートしなくても、`poetry run` をつけてコマンドを実行することで仮想環境内のライブラリを使用することができる。

```bash
# Example
poetry run python [script_name].py
poetry run locust -f [script_name].py
poetry run black [script_name].py
poetry run pytest [script_name].py
```

## poetry プロジェクトのディレクトリ構成

poetry プロジェクトのディレクトリ構成は下記のようになる。

```plaintext
my_project/
├── pyproject.toml
├── README.rst
├── my_project/
│ └── __init__.py
| └── module1.py
└── tests/
  ├── __init__.py
  └── test_module1.py
```

### `__init__.py`

`__init__.py` の扱い方については、プロジェクトの設計やパッケージの使い方に応じて異なります。一般的には、以下のようなシナリオに応じて `__init__.py` を変更することが考えられます。

#### 1. 空のままにする

単にディレクトリがパッケージとして認識される目的だけであれば、`__init__.py` は空のままでも問題ありません。
最初は空のままで開始し、必要に応じて変更を加えるのが良いでしょう。

#### 2. パッケージ内のモジュールやクラスをインポートする

よく使用するモジュールやクラスをパッケージレベルでインポートしておくと、利用者がパッケージを使いやすくなります。

```py
# module1.py
python
def greeting(name):
    return f"Hello, {name}!"
```

```py
# module2.py

def farewell(name):
    return f"Goodbye, {name}!"
```

このとき、`my_project/__init__.py` を以下のように編集できます

```py
from .module1 import greeting
from .module2 import farewell

__all__ = ['greeting', 'farewell']
```

#### 3. 初期化コードを追加する

パッケージの初期化に必要な設定や構成を行いたい場合、この `__init__.py` に初期化コードを含めることができます。

```py
import logging
logging.basicConfig(level=logging.INFO)

__all__ = []  # 公開したいモジュールやクラスがある場合に追加
```

### ユニットテスト

pytest を使用する。

```bash
# 依存関係をインストールする
poetry add --dev pytest

# テストを実行する
poetry run pytest
poetry run pytest -v # 詳細な出力を得たい場合
```

#### テストコードの例

```py
# tests/test_module1.py
from my_project.module1 import greeting

def test_greeting():
    assert greeting("Alice") == "Hello, Alice!"
    assert greeting("Bob") == "Hello, Bob!"
```

```py
# tests/test_module2.py
from my_project.module2 import farewell

def test_farewell():
    assert farewell("Alice") == "Goodbye, Alice!"
    assert farewell("Bob") == "Goodbye, Bob!"
```

#### pytest の機能

#### パラメータ化テスト

複数の入力で同じテストを繰り返したい場合に有効です。

```py
@pytest.mark.parametrize("input,expected", [("Alice", "Hello, Alice!"), ("Bob", "Hello, Bob!")])
def test_greeting(input, expected):
    assert greeting(input) == expected
```

#### フィクスチャ

テストの準備や後始末を簡単に行うことができます。

```py
import pytest

@pytest.fixture
def sample_data():
    return "Alice"

def test_greeting(sample_data):
    assert greeting(sample_data) == "Hello, Alice!"
```

## 設定ファイルの解説

### .python-version

pyenv で使用する Python のバージョンを指定する。
プロジェクトで使用する Python のバージョンを変更しない限り変更不要。

### pyproject.toml

poetry の設定ファイル。プロジェクトで使用するパッケージのバージョンや依存関係を記述する。

### poetry.lock

poetry で使用するパッケージのバージョンを固定したファイル。
プロジェクトで使用するパッケージを変更した場合はこちらが自動的に更新されるので、コミットに含めること。

### .editorconfig

メジャーなエディタで使用可能な設定ファイル。
windows でもデフォルトで改行コードを LF で読み込むなどの設定ができる。
