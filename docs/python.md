# python の管理

dotfiles を利用して Windows でも Mac でもスムーズに Python が使える状態にする。

[Python のパッケージ管理ベストプラクティス](https://qiita.com/c60evaporator/items/b6a7394231d1e768ce64) がすごいいい記事なので参考にする。

この記事では conda 系の利用を推奨しているが、 conda 系は自分があまり好きじゃないのと、商用利用では面倒くさそうなので pyenv + poetry 方式を採用する。
それ以外の方式はリンクの記事を参照。

## パッケージ管理について

> まず、一般的に「パッケージ管理」と呼ばれている要素を、以下の 4 つの機能に分割して考える必要があります。
>
> A. インタプリタ切替 (Python のバージョンを切り替える)
> B. パッケージ切替 (パッケージのバージョンを切り替える)
> C. パッケージインストール (パッケージをインストールする)
> D. リポジトリ (パッケージのインストール元)
>
> 一般的に「パッケージ管理ツール」と呼ばれているものは、上記機能の一部のみをカバーしているため、全ての機能を実現するためには複数のツールを組み合わせる必要があります。

## 基本的な流れ

プロジェクトごとに仮想環境を作成してパッケージを使い分け、不要になったら仮想環境を削除してベースの Python 環境は綺麗な状態を保つ事が望ましい。

上記のコンセプトに従い、以下の流れで開発環境 (パッケージ管理環境)を構築する。

1. 必要ツールのインストール (最初の 1 回のみ)
1. 仮想環境作成
1. 仮想環境にパッケージをインストール
1. エディタに仮想環境を紐付ける

## ① 必要ツールのインストール

### Mac

brew で poetry をインストール。

### Windows

Windows では python コマンドより「Python ランチャー」`py` を使用するのがよい。

```bash
$ py      # デフォルトバージョンの Python を実行
$ py -3.6 # バージョンを指定して実行

$ py --list # インストール済みのバージョンを確認
$ py -0p    # インストール済みのバージョンを確認
```

poetry のインストールは [ここ](https://qiita.com/c60evaporator/items/b6a7394231d1e768ce64#poetry%E3%81%AE%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB) を参照。

## ② 仮想環境作成

### プロジェクト用フォルダの作成

```bash
# プロジェクト用フォルダを作成する
$ cd [プロジェクト用フォルダの上位フォルダのパス]
$ poetry new [プロジェクト用フォルダ名]

# 既存のフォルダをプロジェクト用フォルダとして初期化する場合は
$ poetry init
```

## MEMO

Windows の py で直接パッケージを追加する

```bash
py -m pip install [package]
```