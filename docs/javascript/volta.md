# Volta とランタイム／パッケージマネージャーの関係

Volta は JavaScript/TypeScript 開発向けに、Node.js ランタイムと npm・Yarn・pnpm といったパッケージマネージャーのバージョンをユーザー単位・プロジェクト単位で管理するツールです。
ここでは、それぞれのツールとの関係と運用フローを整理します。

## 基本の考え方

- **グローバルツールチェーン**: `volta install ...` を実行すると、インストールされたバージョンがユーザー全体の既定値になります。どのディレクトリでもそのバージョンが使われます。
- **プロジェクト固定 (pin)**: プロジェクトルートで `volta pin node@...` や `volta pin yarn@...` を実行すると、直下の `package.json` に `volta` セクションが追加され、そのディレクトリ配下では固定された Node.js / Yarn が優先されます。pnpm は Volta 上ではツールチェーンに追加できる CLI という扱いなので、pin の対象外です。
- **ツール解決の優先順位**: プロジェクトの `volta` セクション > グローバルツールチェーン > システムに配置されたバイナリの順で解決されます。

## ツールごとの管理

### Node.js

- `volta install node@<version>` で Node.js をインストールすると、同梱の npm も自動的にセットアップされます。
- `volta install node@latest` を実行すると、最新安定版へ更新できます。
- プロジェクト単位で固定したい場合は、対象ディレクトリで `volta pin node@20.16.0` のように指定します。

### npm

- Node.js をインストールしたタイミングで付属の npm がセットアップされるため、基本的には Node.js のバージョンに追従します。
- `volta install npm@<version>` を使うと、ユーザー全体で利用する npm のバージョンを個別に上書きできます。Node.js のバージョンを変えずに npm だけ試したい場合や、`node@latest` に含まれる npm を上書きしたい場合に有効です。
- `volta pin npm@<version>` をプロジェクトルートで実行すると、固定された npm が優先されます。

### Yarn

- `volta install yarn@<version>` でグローバル既定値を設定できます。
- Volta は Yarn 1 系と Yarn 2+ (Berry) のどちらもサポートしており、`latest` や特定バージョンを指定して切り替え可能です。
- プロジェクト固有で利用したい場合は、プロジェクトルートで `volta pin yarn@<version>` を実行します。

### pnpm

- `volta install pnpm@<version>` で pnpm をユーザー全体にインストールできます。
- pnpm は `volta pin` に対応していないです

    ```bash
    $ volta pin pnpm@10.17
    error: Only node and yarn can be pinned in a project

    Use `npm install` or `yarn add` to select a version of pnpm for this project.
    ```

- そのため、プロジェクトで pnpm のバージョンを固定したい場合は、次のいずれかを利用します。
  - `volta install pnpm@<version>` を全員が実行してグローバルツールチェーンを揃える。
  - `npm install pnpm@<version> --save-dev` や `yarn add pnpm@<version> --dev` でプロジェクト依存に追加し、`npx pnpm ...` や npm script 経由で呼び出す。
  - Node.js 16 以降を使っている場合は `corepack enable pnpm` → `corepack prepare pnpm@<version> --activate` で Corepack に管理させる。

## 代表的なコマンド

```bash
# グローバルに最新版を導入
volta install node@latest
volta install npm@latest
volta install yarn@latest
volta install pnpm@latest

# 現在のツールチェーンを確認
volta list

# プロジェクトルートで固定する
volta pin node@20.16.0
volta pin yarn@4.5.0

# 固定されたバージョンの確認 (プロジェクトルートで実行)
cat package.json | jq '.volta'
```

## 運用のポイント

- **package.json の管理**: `volta pin` を実行すると `package.json` に `volta` セクション (node / yarn) が追記されます。リポジトリで共有したい場合は忘れずにコミットしてください。
  - package.json が存在しない場合は `npm init` で Node.js プロジェクトを初期化してから `volta pin` を実行しましょう。
- **CI/CD での再現性**: CI で `volta install` を実行するだけで、必要なツールが自動的にダウンロードされます。`volta fetch` を使えば事前ダウンロードのみを行うことも可能です。
- **バージョン確認**: `node -v`, `npm -v`, `yarn -v`, `pnpm -v` を実行して、想定したバージョンが利用されているか確認しましょう。
- **バージョン切り替えの柔軟性**: 新バージョンを試す際は `volta install ...` を再実行するだけで切り替えられます。問題があれば以前のバージョンを再インストールして戻せます。
- **pnpm の共有**: pnpm をチームで共有する場合は、グローバルインストールや devDependencies 化、Corepack のいずれかを統一ルールとして決めておくと混乱を防げます。
