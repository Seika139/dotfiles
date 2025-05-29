# GitHub アカウントを使い分けつつ Dev Container を使う方法

1 つの PC で複数の GitHub アカウントを使い分けながら、Dev Container 内でも適切に GitHub との push/pull を行う方法を紹介します。

- [GitHub アカウントを使い分けつつ Dev Container を使う方法](#github-アカウントを使い分けつつ-dev-container-を使う方法)
  - [ssh と GitHub の設定](#ssh-と-github-の設定)
    - [ssh キーペア](#ssh-キーペア)
    - [GitHub への公開鍵の登録](#github-への公開鍵の登録)
    - [~/.ssh/config の設定](#sshconfig-の設定)
    - [SSH 接続のテスト](#ssh-接続のテスト)
  - [gitconfig](#gitconfig)
    - [アプローチ A（推奨） リポジトリごとに設定](#アプローチ-a推奨-リポジトリごとに設定)
    - [アプローチ B includeIf を使ってディレクトリごとに自動で切り替える](#アプローチ-b-includeif-を使ってディレクトリごとに自動で切り替える)
      - [1. メインの `~/.gitconfig` を編集](#1-メインの-gitconfig-を編集)
      - [2. 個人用と会社用の gitconfig ファイルを作成](#2-個人用と会社用の-gitconfig-ファイルを作成)
  - [リモート URL のクローン時の注意点](#リモート-url-のクローン時の注意点)
  - [Dev Containers 内で GitHub に push/pull する](#dev-containers-内で-github-に-pushpull-する)
    - [アプローチ A: SSH Agent Forwarding （推奨）](#アプローチ-a-ssh-agent-forwarding-推奨)
      - [仕組み](#仕組み)
      - [メリット](#メリット)
      - [設定と確認](#設定と確認)
        - [1. ホストマシンで SSH エージェントを起動し、鍵を読み込む](#1-ホストマシンで-ssh-エージェントを起動し鍵を読み込む)
        - [2. devcontainer.json の設定](#2-devcontainerjson-の設定)
        - [コンテナ内で確認](#コンテナ内で確認)
    - [アプローチ B: `~/.ssh` ディレクトリをマウントする（非推奨）](#アプローチ-b-ssh-ディレクトリをマウントする非推奨)
      - [仕組み](#仕組み-1)
      - [メリット](#メリット-1)
      - [デメリット](#デメリット)
    - [gitconfig の扱い](#gitconfig-の扱い)
      - [推奨される運用](#推奨される運用)

## ssh と GitHub の設定

### ssh キーペア

まず、会社用と個人用それぞれで SSH 鍵ペアを作成します。異なるファイル名で作成し、既存の鍵を上書きしないように注意しましょう。

各コマンド実行時にパスフレーズを設定するか聞かれますが、これは任意です。設定する場合は忘れないようにメモしておきましょう。

```bash
# 個人用（例: id_rsa_personal）
ssh-keygen -t rsa -f ~/.ssh/id_rsa_personal -C "your_personal_email@example.com"

# 会社用（例: id_rsa_company）
ssh-keygen -t rsa -f ~/.ssh/id_rsa_company -C "your_company_email@example.com"
```

### GitHub への公開鍵の登録

作成した公開鍵（`.pub` が付くファイル）をそれぞれの GitHub アカウントに登録します。

- 個人用 GitHub アカウント：`~/.ssh/id_rsa_personal.pub` の内容を登録
- 会社用 GitHub アカウント：`~/.ssh/id_rsa_company.pub` の内容を登録

GitHub の「Settings」→「SSH and GPG keys」から「New SSH key」をクリックし、タイトルを付けて鍵の内容を貼り付けます。

### ~/.ssh/config の設定

`~/.ssh/config` ファイルを作成または編集し、それぞれの GitHub アカウントへの接続設定を記述します。

```config
# 個人用GitHubアカウント
Host github.com-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_personal
    IdentitiesOnly yes # 重要！このホストでは指定された鍵のみ使用する

# 会社用GitHubアカウント
Host github.com-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_company
    IdentitiesOnly yes # 重要！このホストでは指定された鍵のみ使用する
```

- `Host`: Git の URL で指定するホスト名です。任意に設定できますが、`github.com-personal` や `github.com-company` のようにわかりやすい名前にすると良いでしょう。
- `HostName`: 実際の GitHub のホスト名（`github.com`）を指定します。
- `User`: git を指定します。
- `IdentityFile`: 使用する秘密鍵のパスを指定します。
- `IdentitiesOnly yes`: これを設定すると、このホストへの接続時に指定した `IdentityFile` のみを使用するようになります。複数の鍵を持っている場合に誤って他の鍵が使われるのを防ぎます。

### SSH 接続のテスト

設定が正しく行われたか、SSH 接続をテストします。

```bash
ssh -T github.com-personal
# Hi <個人用GitHubのユーザー名>! You've successfully authenticated, but GitHub does not provide shell access. と表示されれば成功

ssh -T github.com-company
# Hi <会社用GitHubのユーザー名>! You've successfully authenticated, but GitHub does not provide shell access. と表示されれば成功
```

## gitconfig

### アプローチ A（推奨） リポジトリごとに設定

これが最も推奨される方法です。各リポジトリのディレクトリで、そのリポジトリに合った Git ユーザー名とメールアドレスを設定します。

グローバルな設定は汎用的なものにしておく（または設定しない）。
もしすでにグローバルで設定している場合は、一旦削除するか、あまり使わない方（例えば個人用）を設定しておいても良いでしょう。

```bash
# グローバル設定（なくてもOK）
git config --global user.name "Your Name"
git config --global user.email "your_default_email@example.com"
```

各リポジトリをクローンした後、そのリポジトリのディレクトリ内でローカル設定を行う。

```bash
# 個人用リポジトリの場合
cd ~/projects/personal/your-repo-personal
git config user.name "Your Personal Name"
git config user.email "your_personal_email@example.com"

# 会社用リポジトリの場合
cd ~/projects/company/your-repo-company
git config user.name "Your Company Name"
git config user.email "your_company_email@example.com"
```

この設定は、そのリポジトリの `.git/config` ファイルに書き込まれます。

### アプローチ B includeIf を使ってディレクトリごとに自動で切り替える

特定のディレクトリ以下でのみ、特定の `gitconfig` を読み込むように設定できます。

#### 1. メインの `~/.gitconfig` を編集

```config
[user]
    # グローバルなユーザー名とメールアドレス（どちらでもない場合のデフォルト）
    # name = Your Default Name
    # email = your_default_email@example.com

[includeIf "gitdir:~/projects/personal/"]
    path = ~/.gitconfig_personal

[includeIf "gitdir:~/projects/company/"]
    path = ~/.gitconfig_company
```

`gitdir:` のパスは、Git リポジトリのルートディレクトリを指します。最後の`/`を忘れないように注意してください。

#### 2. 個人用と会社用の gitconfig ファイルを作成

`~/.gitconfig_personal` を作成:

```config
[user]
    name = Your Personal Name
    email = your_personal_email@example.com
```

`~/.gitconfig_company` を作成:

```config
[user]
    name = Your Company Name
    email = your_company_email@example.com
```

この設定により、`~/projects/personal/` 以下のリポジトリでは自動的に個人用の設定が、`~/projects/company/` 以下のリポジトリでは自動的に会社用の設定が適用されます。

## リモート URL のクローン時の注意点

リポジトリをクローンする際に、`~/.ssh/config` で設定した Host 名を使用します。

個人用リポジトリをクローンする場合:

- `git@github.com-personal:YourPersonalUser/your-repo-personal.git`

会社用リポジトリをクローンする場合:

- `git@github.com-company:YourCompanyOrg/your-repo-company.git`

このように、`github.com` の代わりに`~/.ssh/config` で設定した Host 名を使うことで、Git が自動的に適切な SSH 鍵を選択して接続してくれます。

## Dev Containers 内で GitHub に push/pull する

### アプローチ A: SSH Agent Forwarding （推奨）

Dev Containers の最も一般的な SSH 鍵の共有方法は、ホストマシンの SSH エージェントをコンテナにフォワードすることです。

#### 仕組み

ホストマシンで SSH エージェント（ssh-agent）が起動しており、鍵（ssh-add で追加したもの）が読み込まれている場合、Dev Containers はそのエージェントへのソケットをコンテナ内部に転送します。
コンテナ内部では、Git や SSH コマンドがこの転送されたソケットを通じてホストのエージェントと通信し、認証を行います。これにより、秘密鍵自体がコンテナ内部にコピーされることなく、安全に認証が可能です。

#### メリット

- セキュリティ: 秘密鍵をコンテナ内部にコピーする必要がないため、より安全です。コンテナが侵害されても、秘密鍵が漏洩するリスクが低減されます。
- 利便性: ホスト側で一度 ssh-add で鍵を読み込めば、コンテナを再構築しても鍵を再度追加する必要がありません。
- `.ssh/config` の利用: `~/.ssh/config` ファイル自体は通常コピーされませんが、SSH エージェントが鍵を管理しているため、Host エイリアスで指定した鍵が適切に選択されることが期待できます。

#### 設定と確認

##### 1. ホストマシンで SSH エージェントを起動し、鍵を読み込む

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa_personal
ssh-add ~/.ssh/id_rsa_company
# id_rsa_personalやid_rsa_companyがパスフレーズ付きの場合は、ここでパスフレーズの入力が求められます。
```

##### 2. devcontainer.json の設定

通常は不要ですが、明示的に設定することも可能です。
多くの場合、SSH エージェントフォワーディングはデフォルトで有効になっています。もし明示的に制御したい場合は、`devcontainer.json` に以下の設定を追加することが考えられます。

```json
{
  "name": "My Dev Container",
  // ...
  "runArgs": ["--mount", "type=ssh-agent,source=$SSH_AUTH_SOCK"]
}
```

ただし、VS Code の Dev Containers 拡張機能は、通常この設定なしでも自動的にエージェントフォワーディングを行います。

##### コンテナ内で確認

コンテナのターミナルで以下のコマンドを実行し、ホストの鍵が認識されているか確認します。

```bash
ssh-add -l
# ホストで追加した鍵が表示されれば成功
```

もし表示されない場合は、ホストで ssh-add が正しく実行されているか、sshd_config で AllowAgentForwarding yes が設定されているかなどを確認してください。

### アプローチ B: `~/.ssh` ディレクトリをマウントする（非推奨）

もう 1 つの方法は、ホストの `~/.ssh` ディレクトリ全体をコンテナにマウントすることです。

#### 仕組み

ホストの `~/.ssh` ディレクトリをコンテナの `/home/vscode/.ssh`（または適切なユーザーのホームディレクトリ）にボリュームマウントします。

#### メリット

`~/.ssh/config` ファイルを含め、すべての SSH 関連ファイルがコンテナ内部から直接利用可能になります。

#### デメリット

- セキュリティ: 秘密鍵がコンテナ内部に直接存在することになるため、コンテナが侵害された場合のリスクが高まります。
- パーミッションの問題: マウントしたディレクトリやファイルのパーミッションがコンテナ内で正しく設定されていないと、SSH がエラーを出すことがあります（`"Bad owner or permissions on ~/.ssh/config"` など）。これは手動で修正する必要がある場合があります。

```json
# devcontainer.json の例
{
    "name": "My Dev Container",
    // ...
    "mounts": [
        "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind"
    ]
    // または、ユーザー名が'root'など、イメージによって異なる場合は適宜変更
    // "mounts": [
    //     "source=${localEnv:HOME}/.ssh,target=/root/.ssh,type=bind"
    // ]
}
```

- `${localEnv:HOME}` は、ホストマシンのホームディレクトリのパスに展開されます。
- `target` は、コンテナ内のユーザーのホームディレクトリ内の `.ssh` ディレクトリを指定します。Dev Containers のデフォルトユーザーは `vscode` であることが多いです。

### gitconfig の扱い

gitconfig についても、Dev Containers はローカルのグローバル設定を自動的にコピーしようとします。

- グローバルな `~/.gitconfig`: デフォルトで、ホストの `~/.gitconfig` はコンテナ内のユーザーのホームディレクトリにコピーされます。これにより、`user.name` や `user.email` のグローバル設定、および `includeIf` の設定も引き継がれます。
- リポジトリごとの `.git/config`: 各リポジトリのローカル設定は、そのリポジトリ自体の一部であるため、コンテナにクローンまたはマウントされた時点でそのまま利用できます。

もしホストで `includeIf` を使って `~/.gitconfig_personal` と `~/.gitconfig_company` を設定している場合、その `~/.gitconfig` がコンテナにコピーされます。しかし、`~/.gitconfig_personal` や `~/.gitconfig_company` 自体は自動的にはコピーされません。

この場合、これらの個別設定ファイルもコンテナにマウントする必要があります。

```json
{
  "name": "My Dev Container",
  // ...
  "mounts": [
    // SSH関連ファイルをマウントする場合（推奨はSSHエージェントフォワーディング）
    // "source=${localEnv:HOME}/.ssh,target=/home/vscode/.ssh,type=bind",

    // gitconfigの個別設定ファイルをマウントする場合
    "source=${localEnv:HOME}/.gitconfig_personal,target=/home/vscode/.gitconfig_personal,type=bind",
    "source=${localEnv:HOME}/.gitconfig_company,target=/home/vscode/.gitconfig_company,type=bind"
  ]
}
```

#### 推奨される運用

- **SSH 認証**: SSH エージェントフォワーディングを使用することを強くお勧めします。これにより、鍵の管理がホストに一元化され、セキュリティも向上します。
- **Git 設定 (user.name/user.email)**:
  - 最もシンプルで確実なのは、リポジトリごとに `git config user.name "..."` と `git config user.email "..."` を設定する方法です。Dev Containers でリポジトリを開いたら、初回に一度だけそのリポジトリ用の設定を行えば、コンテナを再構築してもその設定は保持されます。
  - もし `includeIf` を使用する場合は、`~/.gitconfig` だけでなく、`~/.gitconfig_personal` や `~/.gitconfig_company` も mounts オプションでコンテナ内にマウントすることを忘れないでください。
