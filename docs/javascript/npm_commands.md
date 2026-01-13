# npm command

<!-- markdownlint-disable MD024 -->

- [npm command](#npm-command)
  - [npm install](#npm-install)
    - [コマンドの省略形の注意点](#コマンドの省略形の注意点)
    - [参考](#参考)
    - [Volta を使用していない場合](#volta-を使用していない場合)
      - [1. `npm install` (引数なし)](#1-npm-install-引数なし)
      - [2. `npm install -g <package>`](#2-npm-install--g-package)
      - [3. `npm install <package>`](#3-npm-install-package)
      - [4. `npm install -D <package>`](#4-npm-install--d-package)
    - [Volta を使用している場合](#volta-を使用している場合)
      - [1. `npm install` (引数なし)](#1-npm-install-引数なし-1)
      - [2. `npm install -g <package>`](#2-npm-install--g-package-1)
      - [3. `npm install <package>`](#3-npm-install-package-1)
      - [4. `npm install -D <package>`](#4-npm-install--d-package-1)
    - [Volta 使用時の重要なポイント](#volta-使用時の重要なポイント)
    - [`volta pin` コマンド](#volta-pin-コマンド)
      - [`volta pin` の主な機能と効果](#volta-pin-の主な機能と効果)
      - [`volta pin` の基本的な使い方](#volta-pin-の基本的な使い方)
      - [`volta pin` を使用するタイミング](#volta-pin-を使用するタイミング)
      - [まとめ](#まとめ)
  - [npm ci](#npm-ci)
  - [npm list](#npm-list)
  - [Check `package.json`](#check-packagejson)
  - [npm uninstall](#npm-uninstall)
    - [Uninstall local package](#uninstall-local-package)
    - [Uninstall global package](#uninstall-global-package)

## npm install

npm で Node.js のパッケージを管理する際に、 `install` コマンドによってパッケージをインストールするが、その際にどこにパッケージがインストールされ、どうパッケージを使用するかを整理した。

### コマンドの省略形の注意点

- `npm install` は省略系として `npm i` も使用できる。
- `npm install -D` は `npm install --save-dev` の省略系で、`npm install -d` は `npm install --loglevel=debug` の省略系。似ているが意味は異なるので注意が必要。

### 参考

- Gemini
- [そろそろ適当に npm install するのを卒業する](https://zenn.dev/ikuraikura/articles/71b917ab11ae690e3cd7)

### Volta を使用していない場合

#### 1. `npm install` (引数なし)

- 現在の作業ディレクトリにある `package.json` に基づいて、必要なパッケージをインストールします。プロジェクトを始める際は `npm init` コマンドで新しい `package.json` を作成します。
- **インストール先:** プロジェクトのルートディレクトリにある `node_modules` ディレクトリにインストールされます。これらのパッケージは、そのプロジェクトのローカルな依存関係として扱われます。
- **`PATH`:** グローバルにインストールされないため、これらのパッケージの実行可能ファイル（コマンドラインツールなど）は、直接 `PATH` に追加されません。通常は、プロジェクトの `package.json` の `scripts` で定義して実行したり、`npx <コマンド>` のように `npx` 経由で使用したりします。
- **使用時の注意点:**
  - プロジェクトごとに依存関係が分離されるため、異なるプロジェクトで同じパッケージの異なるバージョンを使用できます。
  - プロジェクトを共有する際には、`package.json` と `package-lock.json` を含めることで、依存関係のバージョンを一致させることができます。
  - グローバルにインストールするよりも、プロジェクトの依存関係として管理する方が一般的で推奨されます。
- `--save` オプションはデフォルトで有効になっており、インストールされたパッケージは自動的に `package.json` の `dependencies` セクションに追加されます。つまり `--save` を明示的に指定する必要はありません。

#### 2. `npm install -g <package>`

- **インストール先:** グローバルな npm のパッケージディレクトリにインストールされます。この場所はシステムによって異なりますが、一般的には以下のいずれかの場所にあります。
  - macOS/Linux: `/usr/local/lib/node_modules` または `~/.nvm/versions/node/<バージョン>/lib/node_modules` (nvm を使用している場合)
  - Windows: `C:\Users\<ユーザー名>\AppData\Roaming\npm\node_modules`
- **`PATH`:** グローバルにインストールされたパッケージの実行可能ファイルは、通常、システムの `PATH` 環境変数に追加されます。これにより、ターミナルから直接コマンドを実行できるようになります。
- **使用時の注意点:**
  - システム全体で共通して使用するコマンドラインツール（例: `create-react-app`, `vue-cli`, `nodemon` など）をインストールする際に使用します。
  - グローバルインストールは、異なるプロジェクト間で依存関係を共有する反面、バージョン管理が難しくなる可能性があります。プロジェクトごとに必要なバージョンが異なる場合に問題が生じることがあります。
  - 権限の問題でインストールに失敗することがあります（その場合は `sudo` を使用したり、npm のプレフィックス設定を変更したりする必要があります）。

#### 3. `npm install <package>`

- これは `npm install <パッケージ名>` の省略形で、`-g` オプションがない場合は、現在のプロジェクトのローカルな依存関係として `node_modules` にインストールされます。
- `PATH` と使用時の注意点は、上記の「1. `npm install`」と同様です。

#### 4. `npm install -D <package>`

- **インストール先:** プロジェクトのルートディレクトリにある `node_modules` ディレクトリにインストールされます。
- **`package.json` への記録:** このオプションを使用すると、インストールされたパッケージは `package.json` の `devDependencies` セクションに記録されます。これは、開発時にのみ必要なパッケージ（例: テストフレームワーク、リンター、トランスパイラーなど）を示すために使用されます。
- **`PATH`:** ローカルインストールと同様、実行可能ファイルは直接 `PATH` に追加されません。`package.json` の `scripts` や `npx` 経由で使用します。
- **使用時の注意点:**
  - 開発環境でのみ必要な依存関係を明確に分離できます。
  - 本番環境にデプロイする際には、`devDependencies` に含まれるパッケージは通常インストールされません（`npm install --production` など）。
- `-D` は `--save-dev` の省略形であり、同じ効果を持ちます。

### Volta を使用している場合

Volta を使用している場合、Node.js と npm のバージョン管理が Volta によって行われます。

#### 1. `npm install` (引数なし)

- **インストール先:** Volta が管理する Node.js 環境の `node_modules` ディレクトリ（通常はプロジェクトのルート）にインストールされます。Volta はプロジェクトごとに適切な Node.js バージョンとそれに紐づく npm を提供するため、インストール先は通常と変わりませんが、どの Node.js 環境にインストールされるかは Volta によって制御されます。
- **`PATH`:** Volta はアクティブな Node.js 環境に合わせて `PATH` を自動的に設定するため、ローカルにインストールされたパッケージの実行可能ファイルは、`package.json` の `scripts` や `npx` 経由で使用できます。
- **使用時の注意点:** Volta を使用している場合でも、ローカルインストールに関する基本的な注意点は変わりません。プロジェクトごとに依存関係が分離され、`package.json` と `package-lock.json` でバージョン管理を行います。

#### 2. `npm install -g <package>`

- **インストール先:** Volta が管理するグローバルな npm パッケージディレクトリにインストールされます。この場所は Volta の設定によって管理され、通常は Volta の管理下にある Node.js のバージョンごとに分離されています。例えば、Node.js 18.x でグローバルインストールしたパッケージと Node.js 20.x でグローバルインストールしたパッケージは、異なる場所に格納される可能性があります。
- **`PATH`:** Volta はアクティブな Node.js 環境に合わせてグローバルパッケージの `PATH` も管理します。npm のバージョンを切り替えると、利用できるグローバルコマンドもその npm バージョンでインストールされたものに変わります。
- **使用時の注意点:**
  - Volta を使用している場合でも、グローバルインストールは慎重に行うべきです。依存する Node.js や npm のバージョンが変わると、グローバルツールの動作に影響が出る可能性があります。
  - 異なる Node.js バージョンでグローバルツールを使用する場合は、それぞれのバージョンでインストールし直すことが推奨されます。Volta はこの分離を容易にします。

#### 3. `npm install <package>`

- Volta 環境下では、`-g` オプションがないため、ローカルなプロジェクトの `node_modules` にインストールされます。
- `PATH` と使用時の注意点は、Volta を使用していない場合の「1. `npm install`」と同様です。

#### 4. `npm install -D <package>`

- **インストール先:** Volta が管理する Node.js 環境の `node_modules` ディレクトリにインストールされ、`package.json` の `devDependencies` に記録されます。
- **`PATH`:** ローカルインストールと同様に扱われます。
- **使用時の注意点:** 開発時の依存関係の管理という点で、Volta の有無に関わらず基本的な考え方は同じです。

### Volta 使用時の重要なポイント

- **Node.js と npm のバージョン管理:** Volta はプロジェクトごとに使用する Node.js と npm のバージョンを自動的に切り替えます。これにより、グローバルに特定のバージョンをインストールする必要性が減り、プロジェクト間の互換性の問題を軽減できます。
- **グローバルインストールの分離:** Volta はグローバルにインストールされたパッケージも Node.js のバージョンごとに分離して管理するため、異なる Node.js バージョンを使用するプロジェクト間でグローバルツールの競合を避けることができます。
- **`volta pin` の活用:** プロジェクトで使用する Node.js と npm のバージョンを `volta pin` コマンドで固定化し、チームで共有することで、開発環境の一貫性を保つことができます。

Volta を使用することで、Node.js と npm のバージョン管理がより柔軟かつ安全に行えるようになります。グローバルインストールは必要最小限に留め、可能な限りプロジェクトローカルに依存関係を管理する原則は、Volta を使用している場合でも推奨されます。

### `volta pin` コマンド

`volta pin` は、Volta を使用してプロジェクトで使用する Node.js、npm、yarn などのツールのバージョンを**明示的に固定（ピン留め）する**ためのコマンドです。このコマンドを実行すると、プロジェクトのルートにある `package.json` ファイルに、使用するツールのバージョン情報が記録されます。

#### `volta pin` の主な機能と効果

1. **バージョン情報の記録:** `volta pin` コマンドを実行すると、指定したツールのバージョンが `package.json` の `engines` フィールドに追記または更新されます。

   ```json
   {
     "name": "your-project",
     "version": "1.0.0",
     "dependencies": {
       // ...
     },
     "devDependencies": {
       // ...
     },
     "engines": {
       "node": "18.16.0",
       "npm": "9.5.1"
     }
   }
   ```

2. **プロジェクト固有のバージョン管理:** これにより、プロジェクトごとに特定のバージョンのツールを使用することが保証されます。異なるプロジェクトで異なるバージョンの Node.js や npm を使用する必要がある場合に非常に便利です。

3. **チーム開発の連携:** プロジェクトのリポジトリを共有する際に、`package.json` にピン留めされたバージョン情報も共有されます。Volta を使用している他の開発者がこのプロジェクトをチェックアウトすると、Volta は自動的に `package.json` に記述されたバージョンを検出し、そのバージョンを使用するように環境を設定します。これにより、チーム全体で一貫した開発環境を維持できます。

4. **自動的なツールインストール:** もし `package.json` にピン留めされたバージョンのツールがローカルにインストールされていない場合、Volta はプロジェクトのディレクトリに入った際に自動的にそのバージョンをダウンロードして使用します。

#### `volta pin` の基本的な使い方

プロジェクトのルートディレクトリに移動し、以下の形式でコマンドを実行します。

- **Node.js のバージョンをピン留め:**

  ```bash
  volta pin node@<使用したいバージョン>
  ```

  例: `volta pin node@20.11.1`

- **npm のバージョンをピン留め:**

  ```bash
  volta pin npm@<使用したいバージョン>
  ```

  例: `volta pin npm@10.2.4`

- **yarn のバージョンをピン留め:**

  ```bash
  volta pin yarn@<使用したいバージョン>
  ```

  例: `volta pin yarn@4.0.0`

複数のツールを同時にピン留めすることも可能です。

```bash
volta pin node@18.16.0 npm@9.5.1
```

#### `volta pin` を使用するタイミング

- **新しいプロジェクトを開始する時:** 使用する Node.js とパッケージマネージャーのバージョンを最初に決定し、ピン留めしておくことで、後々のバージョン不整合を防ぎます。
- **既存のプロジェクトで Volta を導入する時:** プロジェクトで使用している、または推奨する Node.js とパッケージマネージャーのバージョンをピン留めすることで、チーム全体で同じ環境を共有しやすくします。
- **プロジェクトの依存関係を更新する時:** 必要に応じて Node.js やパッケージマネージャーのバージョンを更新し、ピン留めすることで、新しい環境での動作を保証します。

#### まとめ

`volta pin` コマンドは、Volta の最も重要な機能の 1 つであり、プロジェクトで使用するツールのバージョンを `package.json` に記録し、チーム全体で一貫した開発環境を維持するために不可欠です。このコマンドを活用することで、バージョン不整合による問題を減らし、よりスムーズな開発体験を実現できます。

## npm ci

`npm install` では `package.json` に基づいて依存関係をインストールするが、`npm ci` は `package-lock.json` の内容を基にして、正確なバージョンのパッケージをインストールする。
`node_modules` ディレクトリがある場合は一旦削除される。
`package-lock.json` はより詳細な依存関係が記載されているので、インストールの所要時間が短縮されたり、環境によらず同じバージョンのパッケージがインストールされることが保証される。
そのため CI/CD 環境や自動化されたビルドプロセスでの使用が推奨される。
`npm ci` の ci は Continuous Integration の略ではなく、 Clean Install の略。

## npm list

プロジェクトのルートディレクトリで以下のコマンドを実行すると、インストールされているパッケージの一覧がツリー表示される。 `ls` は `list` のエイリアスで、同じ機能を持つ。

```bash
npm list
npm ls
```

グローバルにインストールされたパッケージを確認したい場合は、`-g` オプションを追加する。

```bash
npm list -g
```

特定のパッケージのバージョンを確認したい場合は、パッケージ名を指定する。

```bash
npm list <パッケージ名>
```

## Check `package.json`

プロジェクトのルートディレクトリにある `package.json` ファイルを開くと、`dependencies` および `devDependencies` の項目にインストールされているパッケージとそのバージョンが記載されている。

- **`dependencies`**: アプリケーションの実行に必要なパッケージ
- **`devDependencies`**: 開発時にのみ必要なパッケージ（テスト、ビルドツールなど）

## npm uninstall

### Uninstall local package

ローカルにインストールされたパッケージをアンインストールする場合はプロジェクトのルートディレクトリで以下のコマンドを実行する。

```bash
npm uninstall <パッケージ名>
```

`--save` オプションを指定すると、`package.json` ファイルの `dependencies` からも削除される。

```bash
npm uninstall --save <パッケージ名>
```

`--save-dev` オプションを指定すると、`package.json` ファイルの `devDependencies` から削除される。

```bash
npm uninstall --save-dev <パッケージ名>
```

### Uninstall global package

グローバルにインストールされたパッケージをアンインストールする場合は、`-g` オプションを追加する。

```bash
npm uninstall -g <パッケージ名>
```
