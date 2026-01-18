# shellcheck

CLI の shellcheck と VSCode の拡張機能がある。

```bash
brew install shellcheck # CLI の場合
```

shellcheck を使うことで、シェルスクリプトの静的解析ができるようになる。

```bash
shellcheck your-script.sh
# 解析の結果が表示される
```

VSCode でも同様に、コード上に警告が表示されるようになる。

## 外部のファイルをソースにしている場合

外部のファイルを `source` コマンドで読み込んでいる場合にshellcheck はその内容を解析できないため、警告を出すことがある。

- SC1091: 追跡できないソースファイルをで読み込んでいる場合の警告
- SC2154: 未定義の変数を参照している場合の警告
- SC2034: 定義した変数が使われていない場合の警告

外部のファイルを追跡できないが故にこれらの警告が出る。

以下に対処法を示す。

## 1. CLI での対処法

```bash
shellcheck -x -P SCRIPTDIR your-script.sh
```

- `-x` オプションは外部ソースの解析を有効にする
- `-P <path>` オプションは外部ソースのパスを指定する
  - `<path>` に特別なキーワード `SCRIPTDIR` を指定すると、スクリプトが存在するディレクトリを指す

これで CLI での解析時に警告が出なくなる。

## 2. .shellcheckrc ファイルを作成する

プロジェクトのルートディレクトリに .shellcheckrc ファイルを作成し、以下を追加する。

```bash
source-path=SCRIPTDIR
external-sources=true
```

## 3. VSCode の設定

VSCode の設定ファイル settings.json に以下を追加する。

```json
"shellcheck.customArgs": ["-x"],
```
