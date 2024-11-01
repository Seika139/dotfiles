# Brewfile

Mac OS 上で動作するパッケージ管理システム Homebrew にて`brew bundle` コマンドを利用して、

- Homebrew で管理しているパッケージをファイル（Brewfile）にエクスポートする
- ファイル（Brewfile）をもとにパッケージをインポートする

を容易に実現する。

## Homebrew でインストールできるアプリケーション

Slack や Clipy といったアプリケーションなども Homebrew で管理できる！

- [brave-browser — Homebrew Formulae](https://formulae.brew.sh/cask/brave-browser#default)
- [clipy — Homebrew Formulae](https://formulae.brew.sh/cask/clipy)
- [slack — Homebrew Formulae](https://formulae.brew.sh/cask/slack#default)
- [visual-studio-code — Homebrew Formulae](https://formulae.brew.sh/cask/visual-studio-code#default)

## 参考

- [Brew Bundle の使い方 · GitHub](https://gist.github.com/yoshimana/43b9205ddedad0ad65f2dee00c6f4261)
- [macOS と Homebrew で一瞬で環境をお引っ越し](https://zenn.dev/usagiga/articles/migrate-using-brew-bundle)
- [【完全版】Homebrew とはなんぞや](https://zenn.dev/sawao/articles/e7e90d43f2c7f9)

## ユースケース別実行コマンド

### 現在の設定をエクスポートする

```bash
# カレントディレクトリに ./Brewfile が作られて、現在の設定がリストアップされる。
brew bundle dump

# --file [filename]
# エクスポートするファイル名を指定する

# --force
# 既にファイルがある場合、強制的に上書きする（--force オプションをつけない場合エラーになる）
```

### ファイルからパッケージをインポートする

```bash
# カレントディレクトリの ./Brewfile をもとにパッケージをインストールする
brew bundle

# --file [filename]
# エクスポートするファイル名を指定する
```

## Brewfile.lock.json について

`brew bundle` 実行時に生成される `Brewfile.lock.json` は、Brewfile の依存関係を固定するためのファイル。
このファイルは、特定のバージョンのパッケージをインストールする際に役立つ。
以下のポイントに基づいて `Brewfile.lock.json` を扱うと良い。

1. **バージョン管理に含めるかどうか**:

   - **含める場合**: `Brewfile.lock.json` をバージョン管理に含めることで、他の開発者や新しい環境で同じバージョンのパッケージをインストールできます。これにより、開発環境の一貫性が保たれます。以下のコマンドで追加できます。

     ```bash
     git add Brewfile.lock.json
     git commit -m "Add Brewfile.lock.json for consistent package versions"
     git push origin main
     ```

   - **含めない場合**: パッケージの最新バージョンを常に使用したい場合や、ロックファイルの管理が煩雑になるのを避けたい場合は、バージョン管理に含めない選択肢もあります。この場合、`.gitignore` に追加して無視できます。

     ```bash
     echo "Brewfile.lock.json" >> .gitignore
     ```

2. **更新のタイミング**:

   - `Brewfile` を更新した際には、`Brewfile.lock.json` も更新する必要があります。以下のコマンドで更新できます。

     ```bash
     brew bundle lock --file=Brewfile
     ```

3. **新しい環境での使用**:

   - 新しい環境で `Brewfile.lock.json` を使用する場合、以下のコマンドでパッケージをインストールします。

     ```bash
     brew bundle --file=Brewfile
     ```

4. **依存関係の確認**:
   - `Brewfile.lock.json` を確認することで、現在インストールされているパッケージのバージョンを把握できます。これにより、特定のバージョンに依存するプロジェクトのトラブルシューティングが容易になります。

---

## インストール

```bash
brew tap Homebrew/bundle
```

## コマンドオプション

### `brew bundle` :リストファイルから一括インストール

```bash
touch Brewfile
brew bundle # brew bundle install も同じコマンド
```

- `--global` ホームディレクトリのリストファイル`~/.Brewfile`を使用

- `--file 'path/filename'` リストファイルを指定

### `dump` :インストールリストファイル作成

```bash
brew bundle dump
```

- 現在のディレクトリに `Brewfile` を作成しインストールリストを出力

  ```Brewfile
  tap "homebrew/cask"
  tap "user/tap-repo", "https://user@bitbucket.org/user/homebrew-tap-repo.git"
  cask_args appdir: "/Applications"

  brew "imagemagick"
  brew "denji/nginx/nginx-full", args: ["with-rmtp-module"]
  brew "mysql@5.6", restart_service: true, link: true, conflicts_with: ["mysql"]

  cask "firefox", args: { appdir: "~/my-apps/Applications" }
  cask "google-chrome"
  cask "java" unless system "/usr/libexec/java_home --failfast"
  cask "homebrew/cask-fonts/font-charter"

  mas "1Password", id: 443987910
  ```

- オプション
  - `--force` リストファイルを強制上書き
  - `--global` ホームディレクトリにリストファイル`.Brewfile`を作成
  - `--file 'path/filename'` リストファイルを指定
  - `--describe 'comment'` コメント行に comment を出力

### `cleanup` :アプリ・パッケージ一括削除

- Brewfile に記載のないアプリケーションをリスト表示する
- オプション
  - `--force` リストせずにアンインストール
  - `--global` ホームディレクトリのリストファイル`~/.Brewfile`を使用
  - `--file 'path/filename'` リストファイルを指定

### `check` :Brewfile 記載の内、インストール・アップグレードが必要なものを表示

- オプション
  - `--force` リストせずにアンインストール
  - `--global` ホームディレクトリのリストファイル`~/.Brewfile`を使用
  - `--file 'path/filename'` リストファイルを指定

### `list` :Brewfile 記載のリストを表示する

- オプション
  - `—cask`,`—taps`,`—mas`,`--brews` で表示形式指定、default が`--brews`、`--all`ですべて表示
  - `--global` ホームディレクトリのリストファイル`~/.Brewfile`を使用
  - `--file 'path/filename'` リストファイルを指定
