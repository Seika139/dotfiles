# Mac で複数バージョンの Python を使用する

Mac で複数バージョンの Python インタプリタを利用する方法はいくつもあるが、2024年現在でスタンダードな方法のひとつである [asdf](https://asdf-vm.com/) を利用する。

## Homebrew

Homebrew は macOS 上で動作するパッケージ管理ツール。
git をはじめとしたさまざまなツールを管理できるので mac ユーザーには必須といってよい。
Python をインストールする話の前提として必要になるので先に解説する。

[【完全版】Homebrewとはなんぞや](https://zenn.dev/sawao/articles/e7e90d43f2c7f9)

### インストール方法

もし mac のターミナルなどで `brew` コマンドが実行できない場合は次のようにしてインストールする。

- <https://brew.sh/ja/> の分かりやすいところにインストール用のコマンドが載っているので、コピーしてターミナルに張り付けて実行する。
- ターミナルで `brew -v` を実行してインストールできたことを確認する。

### 基本的な使い方

```bash
$ brew install <パッケージ名> # パッケージをインストールする
$ brew list                   # インストールされたパッケージ一覧を表示する
$ brew remove <パッケージ名>  # パッケージをアンインストール
$ brew upgrade                # すべてのパッケージをアップグレード
$ brew upgrade <パッケージ名> # パッケージを個別にアップグレード
```

## asdf

Homebrew が使えることを確認したら、いよいよ [asdf](https://asdf-vm.com/) の導入に移る。

asdf 公式では git clone してインストールする方法を推奨しているが、ここでは手軽さを重視して Homebrew でインストールする。

<details>
<summary><b>asdf 以外の選択肢</b></summary>
<div>

## Homebrew に直接複数バージョンをインストールする

環境が汚れる

## pyenv

申請が必要

## conda

商用利用に向いてない

## docker

コンテナの知識が必要になる。便利だけど割愛

</div>
</details>

---

<!-- TODO -->

asdf でも pyenv でも社用利用はの申請が必要になるので一旦中止
