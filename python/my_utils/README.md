# my_utils

dotfiles 内で Python を利用した便利なスクリプト群を管理するディレクトリ。
シェルスクリプトでは実装しづらい処理を Python で実装すると同時に、他のプロジェクトで Python を導入する際の参考になるようなプロジェクト管理を実施する。
つまり、新規でプロジェクトを立ち上げる際はこのプロジェクト自体を模倣すればよい状態を目指す。

## docs 内のファイルについて

[./docs](./docs/) 内のファイルは他プロジェクトにコピーしやすいような状態にしておくため、他プロジェクトへのコピー用ではないドキュメントは [../docs/poetry.md](../docs/poetry.md) に配置する。

## パッケージ管理

パッケージ管理の方針については [こっち](../docs/package_management.md) に情報を集約する。

> ここから下がコピーして使用されることを想定した README です。

---

## パッケージ管理の方針

Python のバージョン管理は Windows では自前の Python ランチャーを使用し、それ以外の OS では pyenv を使用します。
プロジェクトのパッケージ管理は共通して poetry を使用します。

※ Windows の Python ランチャーとは何ぞやという方は、[こちら](../docs/start_python/windows.md)を参照してください。

## 導入

環境に応じてドキュメントを分けているので、適切なドキュメントを参照してください。

- [本番環境 (Rocky Linux9)](./docs/setup/prd.md)
- [開発環境 (Windows)](./docs/setup/dev_windows.md)
- [開発環境 (Linux 系)](./docs/setup/dev_linux.md)

## 設定ファイルの解説

| ファイル名                         | 内容                                                                                                                                                                      |
| :--------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [.python-version](.python-version) | pyenv で使用する Python のバージョンを指定します。プロジェクトで使用する Python のバージョンを変更しない限り変更不要です。                                                |
| [pyproject.toml](pyproject.toml)   | poetry の設定ファイルです。プロジェクトで使用するパッケージのバージョンや依存関係を記述します。                                                                           |
| [poetry.lock](poetry.lock)         | poetry で使用するパッケージのバージョンを固定したファイルです。プロジェクトで使用するパッケージを変更した場合はこちらが自動的に更新されるので、コミットに含めてください。 |
| [.editorconfig](.editorconfig)     | メジャーなエディタで使用可能な設定ファイルです。windows でもデフォルトで改行コードを LF で読み込むなどの設定をしています。                                                |

## パッケージの管理

pip コマンドでパッケージなどの管理をする代わりに poetry を使用します。

ここでは例として requests パッケージをインストールする手順を示します。

```bash
poetry add requests # pip install requests に相当します
```

この際、`poetry.lock` が更新され、`pyproject.toml` にも追記されます。
適宜コミットに含めてください。

パッケージを消す場合は `poetry remove requests` を実行してください。

## locust の実行（各種ライブラリを使用する際の注意）

通常の環境ではライブラリ名でコマンドを実行しますが、このプロジェクトでは以下のように実行して下さい。（locust 以外の Python ライブラリも同様です）

```bash
poetry run locust -f [ファイル名] [各種オプション]
```

あるいは仮想環境に入ってから locust を実行しても構いません。

```bash
poetry shell
poetry --version

# poetry が v2.0.0 以上の場合
poetry env activate # 仮想環境を起動する
locust -f [ファイル名] [各種オプション]
poetry env deactivate # 仮想環境を終了する

# poetry が v2.0.0 未満の場合
poetry shell # 仮想環境を起動する
locust -f [ファイル名] [各種オプション]
exit # 仮想環境を終了する
```
