# git config

- [git config](#git-config)
  - [Git の設定レベル](#git-の設定レベル)
  - [`git config` の設定方法](#git-config-の設定方法)
    - [1. ユーザー名とメールアドレスの設定（必須）](#1-ユーザー名とメールアドレスの設定必須)
    - [2. その他のよく使われる設定](#2-その他のよく使われる設定)
  - [`git config` の確認方法](#git-config-の確認方法)
    - [1. すべての設定を表示する](#1-すべての設定を表示する)
    - [2. 特定のレベルの設定を表示する](#2-特定のレベルの設定を表示する)
    - [3. 特定の設定項目の値を確認する](#3-特定の設定項目の値を確認する)
    - [4. 設定ファイルの場所と設定値の出所を確認する](#4-設定ファイルの場所と設定値の出所を確認する)
  - [設定ファイルを直接編集する](#設定ファイルを直接編集する)

`git config` コマンドは、Git の設定を管理するために使用されます。設定には 3 つのレベルがあり、それぞれ適用範囲が異なります。

## Git の設定レベル

1. **システムレベル (`--system`)**:

   - **適用範囲**: そのコンピューター上のすべてのユーザー、すべてのリポジトリに適用されます。
   - **設定ファイル**: `/etc/gitconfig` (Windows では `C:\Program Files\Git\mingw64\etc\gitconfig` など)
   - **優先順位**: 最も低い。他のレベルで同じ設定があれば上書きされます。

2. **グローバルレベル (`--global`)**:

   - **適用範囲**: 現在ログインしているユーザーのすべてのリポジトリに適用されます。
   - **設定ファイル**: `~/.gitconfig` または `~/.config/git/config` (Windows では `C:\Users\<ユーザー名>\.gitconfig` など)
   - **優先順位**: システムレベルより高い。ローカルレベルで同じ設定がなければ適用されます。

3. **ローカルレベル (`--local` またはオプションなし)**:
   - **適用範囲**: 特定の Git リポジトリのみに適用されます。
   - **設定ファイル**: 該当リポジトリ内の `.git/config`
   - **優先順位**: 最も高い。他のレベルの設定を上書きします。

**優先順位**:「ローカル > グローバル > システム」の順に設定が読み込まれ、より狭いスコープの設定が優先されます。

## `git config` の設定方法

`git config [種別] [設定項目] [値]` の形式で設定します。

### 1. ユーザー名とメールアドレスの設定（必須）

Git を使い始める際に、コミット時のユーザー名とメールアドレスを設定します。これらは通常、グローバルレベルで設定します。

```bash
# ユーザー名の設定 (グローバル)
git config --global user.name "Your Name"

# メールアドレスの設定 (グローバル)
git config --global user.email "your.email@example.com"
```

特定のプロジェクトで別のユーザー名やメールアドレスを使用したい場合は、そのリポジトリ内でローカルレベルで設定します。

```bash
# ユーザー名の設定 (ローカル - 該当リポジトリ内でのみ有効)
git config user.name "Project Specific User"

# メールアドレスの設定 (ローカル - 該当リポジトリ内でのみ有効)
git config user.email "project.email@example.com"
```

### 2. その他のよく使われる設定

- **エディタの設定**: コミットメッセージなどを編集する際に使用するエディタを設定します。

  ```bash
  # Visual Studio Code をエディタとして設定 (グローバル)
  git config --global core.editor "code --wait"

  # Vim をエディタとして設定 (グローバル)
  git config --global core.editor "vim"
  ```

  `--wait` オプションは、VS Code が閉じられるまで Git の処理を待機させます。

- **色付けの設定**: ターミナルでの Git コマンドの出力に色を付けます。

  ```bash
  # すべての Git コマンドの出力に色付け (グローバル)
  git config --global color.ui true
  ```

  `true` の他に、`false` (色付けしない) や `auto` (ターミナルが対応していれば色付け) などがあります。

- **エイリアスの設定**: よく使う Git コマンドに短いエイリアスを設定します。

  ```bash
  # `git st` で `git status` が実行されるように設定 (グローバル)
  git config --global alias.st status

  # `git co` で `git checkout` が実行されるように設定 (グローバル)
  git config --global alias.co checkout

  # `git br` で `git branch` が実行されるように設定 (グローバル)
  git config --global alias.br branch

  # `git cm` で `git commit -m` が実行されるように設定 (グローバル)
  git config --global alias.cm "commit -m"
  ```

- **改行コードの自動変換 (`core.autocrlf`)**:
  OS 間の改行コードの違いによる問題を避けるために設定します。

  - **Windows の場合**: Git が LF を CRLF に自動変換するように設定します。

    ```bash
    git config --global core.autocrlf true
    ```

  - **macOS / Linux の場合**: Git が LF を CRLF に変換しないように設定します。

    ```bash
    git config --global core.autocrlf input
    ```

- **初期ブランチ名の変更 (`init.defaultBranch`)**:
  新しいリポジトリを作成した際のデフォルトのブランチ名を `master` から `main` などに変更できます。

  ```bash
  git config --global init.defaultBranch main
  ```

## `git config` の確認方法

設定内容を確認するには、主に以下のコマンドを使用します。

### 1. すべての設定を表示する

すべての設定レベル (システム、グローバル、ローカル) の設定をまとめて表示します。

```bash
git config --list
```

このコマンドは、優先順位に基づいて最終的に有効になる設定を表示します。ローカルリポジトリのルートディレクトリで実行しないと、ローカル設定は含まれません。

### 2. 特定のレベルの設定を表示する

- **グローバル設定のみ表示**:

  ```bash
  git config --list --global
  ```

- **システム設定のみ表示**:

  ```bash
  git config --list --system
  ```

- **ローカル設定のみ表示**:

  ```bash
  # リポジトリ内で実行
  git config --list --local
  ```

### 3. 特定の設定項目の値を確認する

特定の設定項目の値だけを確認したい場合に便利です。

```bash
# グローバルユーザー名を確認
git config --global user.name

# ローカルユーザー名を確認
git config user.name

# グローバルメールアドレスを確認
git config --global user.email

# エディタ設定を確認
git config --global core.editor
```

オプション (`--global`, `--system`, `--local`) を付けない場合は、現在のリポジトリのローカル設定、グローバル設定、システム設定の順に探して最初に見つかった値を表示します。

### 4. 設定ファイルの場所と設定値の出所を確認する

各設定がどのファイルから読み込まれているかを確認できます。

```bash
git config --list --show-origin
```

これにより、設定値の横にその設定が定義されているファイルパスが表示されます。

## 設定ファイルを直接編集する

`git config` コマンドを使用する代わりに、直接設定ファイルを編集することも可能です。

- **ローカル設定ファイル**: `.git/config` (各リポジトリ内)
- **グローバル設定ファイル**: `~/.gitconfig` または `~/.config/git/config`
- **システム設定ファイル**: `/etc/gitconfig`

これらのファイルはプレーンテキストなので、好きなテキストエディタで開いて編集できます。
ただし、構文を誤ると問題が発生する可能性があるため、通常は `git config` コマンドの使用が推奨されます。

特定のレベルの設定ファイルをエディタで開くコマンドもあります。

```bash
# ローカル設定ファイルを開く
git config -e

# グローバル設定ファイルを開く
git config --global -e

# システム設定ファイルを開く
git config --system -e
```

これらのコマンドは、`core.editor` で設定されたエディタでファイルを開きます。設定されていない場合はシステムのデフォルトエディタが使われます。
