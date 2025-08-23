# mise

- GitHub: <https://github.com/jdx/mise>
- 公式ドキュメント: <https://mise.jdx.dev/>

## 概要

以下の機能を併せ持つ万能ツール

- asdf, (nvm, pyenv) などのようにプログラミング言語やツールのバージョンを管理する
- direnv のようにプロジェクトやディレクトリごとに環境変数を設定できる
- make のように、プロジェクトごとにコマンド（タスク）を定義できる

## インストール

インストールしてシェルにフックします。

### Mac

```bash
brew install mise
# bash の場合
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
# zsh の場合
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc

# 新しくターミナルを開くか、以下のコマンドで設定を再読み込み
source ~/.bashrc  # または ~/.zshrc
```

### Linux

```bash
curl https://mise.run | sh
# bash の場合
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
# zsh の場合
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc

# 新しくターミナルを開くか、以下のコマンドで設定を再読み込み
source ~/.bashrc  # または ~/.zshrc
```

## 基本的な使用方法

### ツールのインストール

```bash
# Python の特定バージョンをインストール
mise install python@3.11.0

# Node.js の最新LTS版をインストール
mise install node@lts

# 複数のツールを同時にインストール
mise install python@3.11.0 node@lts
```

### プロジェクト固有の設定

プロジェクトディレクトリに`.mise.toml`ファイルを作成して、プロジェクト固有のツールバージョンを指定できます：

```toml
[tools]
python = "3.11.0"
node = "18.17.0"
```

### ツールの使用

```bash
# インストールされているツールの一覧
mise list

# 特定のツールのバージョン切り替え
mise use python@3.11.0

# 現在のディレクトリで使用するツールのバージョンを設定
mise local python 3.11.0

# グローバルでデフォルトのツールバージョンを設定
mise global python 3.11.0
```

### ツールの削除

```bash
# 特定のバージョンを削除
mise uninstall python@3.11.0

# ツール全体を削除
mise uninstall python
```

## 便利な機能

### プラグインの管理

```bash
# 利用可能なプラグインの一覧
mise plugins list

# プラグインのインストール
mise plugin install python

# プラグインの更新
mise plugin update python
```

### 環境変数の管理

```bash
# 環境変数の設定
mise env set NODE_ENV production

# 環境変数の削除
mise env unset NODE_ENV
```

### シェルの統合

```bash
# 現在のシェルでmiseを有効化
mise activate bash  # または zsh

# シェルの統合を無効化
mise deactivate
```

## トラブルシューティング

### パスの問題

mise が正しく動作しない場合、以下を確認してください：

1. シェルの初期化設定が正しく行われているか
2. `PATH`環境変数に mise のパスが含まれているか
3. 新しいターミナルセッションを開始しているか

### 権限の問題

Devcontainer で権限エラーが発生する場合：

```bash
chmod +x ~/.local/bin/mise
```

## 参考リンク

- [公式ドキュメント](https://mise.jdx.dev/)
- [GitHub リポジトリ](https://github.com/jdx/mise)
- [プラグイン一覧](https://mise.jdx.dev/plugins)
- [ターミナルを使う人は、とりあえず「mise」を入れておく時代。・・・を夢見て。](https://zenn.dev/dress_code/articles/a99ff13634bbe6)
