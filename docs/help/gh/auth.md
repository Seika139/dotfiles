# GitHub CLI の認証

※ GitHub で扱うトークン全般については [GitHub で扱うトークンについて](../github/token.md) を参照してください。

※ 2026年5月現在の内容です。今後変更される可能性があるため、最新の情報は公式ドキュメントを参照してください。

GitHub CLI (`gh`) を利用して GitHub 上のリポジトリや Issue、Pull Request などを操作するためには、事前に GitHub アカウントとの認証が必要です。
以下では、GitHub CLI を使用した認証方法について説明します。

## ログイン

```bash
gh auth login

# -c / --clipboard オプションを付けるとあとでブラウザ認証時に使う
# 8桁の one-time OAuth device code をクリップボードにコピーできます
gh auth login -c
gh auth login --clipboard
```

上記を実行するとインタラクティブに質問がされ、いくつか答えるだけでログインが完了します。
最初にGitHubエンタープライズかどうかを選択します。通常はGitHub.comを選択すればよいです。

```text
? What account do you want to log into?  [Use arrows to move, type to filter]
> GitHub.com
  GitHub Enterprise Server
```

次にGitに使うプロトコルを選択します。わからなければHTTPSを使えばよいでしょう。

```text
? What is your preferred protocol for Git operations?  [Use arrows to move, type to filter]
> HTTPS
  SSH
```

SSHを選択した場合は、端末上のSSH keyをGitHubにアップロードするか聞いてくれます。
すでに GitHub に key を登録している場合は Skip で OK です。

```text
? Upload your SSH public key to your GitHub account?  [Use arrows to move, type to filter]
> /home/XXXXX/.ssh/id_ed25519.pub
  /home/XXXXX/.ssh/id_rsa.pub
  Skip
```

最後に認証

- ブラウザ経由で行う
- トークンをペーストする
  を選択します

```text
? How would you like to authenticate GitHub CLI?  [Use arrows to move, type to filter]
> Login with a web browser
  Paste an authentication token
```

wsl などブラウザが開けなくてもホストPCのブラウザで <https://github.com/login/device> にアクセスしてコードを入力すればブラウザでの認証は可能です。

Paste an authentication token を選択した場合は、以下のような推移となります。

```text
? How would you like to authenticate GitHub CLI? Paste an authentication token
Tip: you can generate a Personal Access Token here https://github.com/settings/tokens
The minimum required scopes are 'repo', 'read:org'.
? Paste your authentication token:
```

書いてある通りに、<https://github.com/settings/tokens> に行き、repo と read:org の権限を付与したアクセストークンを作成します。

貼り付けると以下のように認証が完了します。

```text
? Paste your authentication token: ****************************************
- gh config set -h github.com git_protocol ssh
✓ Configured git protocol
✓ Logged in as XXXXXX
```

最後の認証が完了した後、GitHub CLI が認証情報を保存し、以降は `gh` コマンドを使用して GitHub の操作が可能になります。
Login with a web browser と Paste an authentication token では、トークンの種類が異なります。

※ Organization 側で Personal Access Token (PAT) による認証を許可していない場合がある。その場合は Login with a web browser を選択する必要があります。

## 認証状態の確認

```bash
gh auth status
```

このコマンドを実行すると、現在の認証状態が表示されます。以下の情報が確認できます。

- 認証されているユーザー名
- 認証方法（HTTPS または SSH）
- 認証トークンの有効期限（もしあれば）

## 認証情報の管理

GitHub CLI で認証が完了すると、認証情報は GitHub CLI の設定ファイルに保存されます。
通常、ユーザーのホームディレクトリの `.config/gh/hosts.yml` にあります。
このファイルには、認証されたアカウントの情報やアクセストークンが保存されます。
このファイルを直接編集することもできますが、通常は `gh auth` コマンドを使用して管理することが推奨されます。

```bash
cat ~/.config/gh/hosts.yml
```

このファイルに直接 Token が記載されている場合もあるので注意。
Mac の場合は、Keychain Access アプリで GitHub CLI のトークンを管理していて、 `hosts.yml` にトークンがない場合もあります。

トークンを表示するには以下のコマンドを使用します。

```bash
gh auth token
```

## ログアウト

```bash
gh auth logout
```

このコマンドを実行すると、GitHub CLI で保存されている認証情報が削除されます。
ログアウト後は、再度 `gh auth login` を実行して認証を行う必要があります。

## GitHub CLI からの認証をまとめて revoke する

`gh auth login` で発行されたトークンは、認証した PC ごとに異なる。（Windows の wsl からログインした場合も同様で wsl 上にホストマシンとは異なるトークンが発行・保存される）
つまりログアウトは基本的にその PC での認証情報を削除するだけで、他の PC での認証情報は削除されません。

もし、GitHub CLI からの認証をまとめて revoke したい場合は、GitHub の [Settings → Applications](https://github.com/settings/applications) → Authorized OAuth Apps から「GitHub CLI」を選択し、「Revoke access」をクリックすることで GitHub CLI からの認証をまとめて revoke できます。

## スコープの追加

`gh auth login` で認証した後に、スコープを追加したい場合は以下のコマンドを使用します。
たとえば、workflow と project のスコープを追加したい場合は以下のようにします。

```bash
gh auth refresh -h github.com -s workflow,project

# login の時点で workflow と project のスコープを付与する場合は
gh auth login -h github.com -s workflow,project
```

`-s` オプションではスコープの追加しかできないので、もしスコープを減らしたい場合は、一度ログアウトしてから再度ログインします。

`-c / --clipboard` オプションを付けると、あとでブラウザ認証時に使う 8桁の one-time OAuth device code をクリップボードにコピーできます。

## 参考ページ

- [GitHub CLIのインストールとログイン - APC 技術ブログ](https://techblog.ap-com.co.jp/entry/2021/08/23/091131)
