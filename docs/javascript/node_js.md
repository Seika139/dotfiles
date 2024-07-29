# Node.js と関連ツール

## Node.js

もともとブラウザ上で動作する JavaScript をサーバー（PC）上で動作させるもの。

## パッケージ管理ツール

Node.js のパッケージ・ライブラリを管理するツール。

### npm

- Node.js 公式のパッケージマネージャー
- `package.json` ファイルでプロジェクトの依存関係を管理する

### yarn

- Facebook (Meta) が開発した npm の代替パッケージマネージャー
- npm より高速だとされていたが、最近は npm も高速になった
- `yarn.lock` ファイルで依存関係を管理する

## バージョン管理ツール

Node.js 自体のバージョンを管理するツール。
たくさんあるうちのいくつかを記載する。

- nvm
- n
- volta: Node.js に関しては 2024 時点で一番おすすめ
- asdf: Node.js に限らずいろんな言語のバージョン管理ができる

## Volta の使用方法

インストール方法は適宜調べる。
このあたりを見てインストールする。

- [Windows で Node.js のバージョン管理 - VOLTA v1.1.1 ｜るらい](https://note.com/rurai/n/n47a3fb9c4508#6fc517db-ac60-4916-aa13-de7d3e8359a9)
- [Node.js バージョン管理 Volta を Windows にインストールする](https://zenn.dev/longbridge/articles/30c70144c97d32)

以下コマンドの参考: [Node.js バージョン管理ツール『Volta』を使ってみる #npm - Qiita](https://qiita.com/nakashun1129/items/47c09ccbbba73c4ef8c4)

### Volta で Node.js をインストールする

```bash
volta install node@[バージョン]
```

`[バージョン]` には latest や特定のバージョンを入れる。

### インストール済みのバージョン一覧の確認

```bash
volta list node
```

現在インストールされている全ての Node.js のバージョンと、現在アクティブなバージョンが表示される。

### バージョンの切り替え

特定のプロジェクトで使用する Node.js のバージョンを指定したい場合、プロジェクトのルートディレクトリで次のコマンドを実行する。

```bash
volta pin node@14.15.0
```

これにより、そのプロジェクトでのみ指定されたバージョンの Node.js が使用されるようになる。

> volta pin は package.json にバージョンを記載するので、そもそも npm init してないと使えません。必要に応じて npm init して package.json を作成してください。

グローバルに使用するバージョンを変更する場合は、以下のようにコマンドを実行します。

```bash
volta default node@14.15.0
```
