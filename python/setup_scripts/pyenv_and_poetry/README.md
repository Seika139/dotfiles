# setup_scripts/pyenv_and_poetry

Python のパッケージ管理を pyenv + poetry で行う際に、環境構築を行う手順を一括で実行するスクリプトを管理するディレクトリ。

## ディレクトリ構成

```plaintext
python/setup_scripts/pyenv_and_poetry/
├── copy_into_project/
├── general/
├── pyenv/
|   ├── install_pyenv.bash
|   └── uninstall_pyenv.bash
└── README.md # このファイル
```

### copy_into_project

各Pythonプロジェクトにコピーして使用する想定のスクリプト群。
ディレクトリ内のすべてのスクリプトをプロジェクトにコピーする。
その際、`[project_root]/scripts/setup_XXX.bash` のように、プロジェクトルートに `scripts` のようなディレクトリを作成し、その中にコピーする。
スクリプト内でプロジェクトルートが自身の2つ上がプロジェクトルートであることを想定しているため、ディレクトリ構成が変わる場合はスクリプト内のパスを修正すること。

### general

プロジェクトにコピーせずに引数でパスを指定して実行するスクリプト群。
自分が使用するPC内でプロジェクトを作成する際に使用する。
`general/setup_project.bash` は作ったはいいものの、本番環境でこれを実行することはなさそうなので、実質的な用途はない。

### pyenv

pyenv のインストーラー pyenv は PC 共通でインストールするため general と copy_into_project に分ける必要はない。
各プロジェクトで pyenv を使用する場合はこれらもコピーする。
