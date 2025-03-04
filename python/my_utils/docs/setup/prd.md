# 本番環境での環境構築

> これは locust のプロジェクトの例です。

踏み台サーバーから runner と呼ばれる負荷をかけるためのサーバーに接続します。

```bash
# 24.11.14 時点では 01 から 06 までの runner が存在します
ssh runner-str01-0[1-6]
```

runner の各自のホームディレクトリにこのリポジトリをクローンします。

※ 現時点では ssh でのクローンができないみたいなので、 https でクローンしてください。ssh でクローンできたら教えてください。

```bash
git clone XXXXX
cd loadtest
```

## pyenv

Python のバージョン管理は pyenv を使用します。
pyenv をインストールするスクリプトを実行します。
既にインストール済みの場合でも適切なエラーハンドリングをするので複数回実行しても問題ありません。

```bash
bash scripts/install_pyenv.bash
```

上記のスクリプトで pyenv をインストールしたら、pyenv を環境変数として読み込むために shell を再読み込みしてください。

```bash
source $HOME/.bashrc
```

### パッケージ不足による警告が出る場合

install_pyenv.bash 実行中に下記のような警告が出る場合があります。
その場合は runner を管理するシス管さんに OS へのパッケージ追加をお願いしてください。

```plaintext
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/user_name/.pyenv/versions/3.12.6/lib/python3.12/bz2.py", line 17, in <module>
    from _bz2 import BZ2Compressor, BZ2Decompressor
ModuleNotFoundError: No module named '_bz2'
WARNING: The Python bz2 extension was not compiled. Missing the bzip2 lib?
```

システム管理者の対応後に下記のスクリプトを実行して、警告なしで python を pyenv でインストールできることを確認してください。

```bash
pyenv unisntall 3.12.6
bash scripts/install_pyenv.bash
```

## プロジェクトのセットアップ

- pyenv を使用して所定の python バージョンのインストール
- poetry を使用してパッケージのインストール

を行います。
こちらもスクリプトを用意しているので、実行してください。

```bash
bash scripts/setup_prd.bash
```
