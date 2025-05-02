# GitHub の認証

<!-- markdownlint-disable MD024-->

## Public リポジトリ

Public リポジトリは誰でも閲覧可能であり、特別な認証なしにクローンやプルが可能です。プッシュに関しては、書き込み権限を持つユーザーのみが設定を行う必要があります。

### HTTPS

- **Push:** 通常、初回プッシュ時に GitHub のユーザー名とパスワード（またはアクセストークン）の入力を求められます。資格情報をキャッシュする設定を行うことで、その後の入力を省略できます。
- **Pull:** 特に設定は不要です。リポジトリの URL を指定して `git clone` または `git pull` を実行できます。

### SSH

- **Push/Pull:** 事前に SSH 鍵を生成し、GitHub アカウントに登録する必要があります。登録後、リポジトリの SSH URL を使用することで、パスワードなしにプッシュとプルが可能です。

### GitHub CLI

- **Push/Pull:** `gh auth login` コマンドで GitHub アカウントと連携することで、HTTPS または SSH の認証情報を GitHub CLI が自動的に管理します。連携後は、特に設定なしに `gh repo clone`, `git push`, `git pull` などのコマンドを実行できます。

## Private リポジトリ

Private リポジトリへのアクセスは、明示的に権限を与えられたユーザーのみに制限されます。そのため、プッシュとプルの両方で認証が必要です。

### HTTPS

- **Push/Pull:** リポジトリへのアクセス権を持つ GitHub アカウントのユーザー名とパスワード（またはアクセストークン）が必要です。通常、初回アクセス時に認証情報の入力を求められます。資格情報ヘルパーを設定することで、認証情報をキャッシュし、その後の入力を省略できます。

### SSH

- **Push/Pull:** Public リポジトリと同様に、事前に SSH 鍵を生成し、アクセス権のある GitHub アカウントに登録する必要があります。登録後、リポジトリの SSH URL を使用することで、パスワードなしにプッシュとプルが可能です。

### GitHub CLI

- **Push/Pull:** Public リポジトリと同様に、`gh auth login` コマンドでアクセス権のある GitHub アカウントと連携することで、HTTPS または SSH の認証情報を GitHub CLI が自動的に管理します。連携後は、特に設定なしに `gh repo clone`, `git push`, `git pull` などのコマンドを実行できます。

## GitHub Enterprise (SSO 設定時)

GitHub Enterprise で SSO (Single Sign-On) が設定されている場合、認証の仕組みが通常と異なります。

### HTTPS

- **Push/Pull:**
  - **初回認証:** 通常のユーザー名とパスワードではなく、GitHub Enterprise の認証システムを通じて発行されたアクセストークンを使用します。Web ブラウザを通じて GitHub Enterprise にログインし、個人用アクセストークンを生成する必要があります。
  - **トークンの管理:** 生成したアクセストークンを資格情報ヘルパーに登録することで、その後の入力を省略できます。

### SSH

- **Push/Pull:**
  - **SSH 鍵の登録:** 通常の GitHub.com と同様に SSH 鍵を生成し、GitHub Enterprise のアカウントに登録します。
  - **SSO 連携:** SSO 環境によっては、SSH 鍵の利用に追加の承認が必要となる場合があります。GitHub Enterprise の管理者にお問い合わせください。

### GitHub CLI

- **Push/Pull:**
  - **`gh auth login`:** GitHub CLI で認証を行う際に、GitHub Enterprise Server の URL を指定する必要があります。コマンド実行後、Web ブラウザが開き、SSO による認証フローが開始されます。
  - **アクセストークンの自動管理:** 認証が成功すると、GitHub CLI が必要なアクセストークンを自動的に管理するため、その後の操作で特別な設定は不要です。

**補足:**

- **アクセストークン:** パスワードよりも安全性が高く、有効期限やスコープ（権限範囲）を設定できます。特に SSO 環境下では、アクセストークンの利用が推奨されます。
- **資格情報ヘルパー:** Git の設定で利用できるツールで、HTTPS 認証情報を安全に保存し、以後の入力を省略できます。`git config --global credential.helper store` などで設定できます。
- **SSH 鍵の生成:** `ssh-keygen` コマンドで生成できます。公開鍵 (`.pub` ファイル) を GitHub アカウントに登録します。
- **GitHub CLI のインストール:** GitHub の公式サイトからインストールできます。
