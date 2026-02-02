# DevContainer 内に dotfiles を展開する

DevContainer 内で開発環境を構築する際に、ホストマシンの dotfiles を展開して利用する方法を説明する。

**vscode の settings.json に以下の設定を追加する。**

```json
{
  "dotfiles.repository": "https://github.com/Seika139/dotfiles.git", // dotfiles リポジトリの URL を指定
  "dotfiles.installCommand": "install.sh" // dotfiles リポジトリを起点としたインストールコマンドを指定
}
```

さらに、DevContainer内のシェルを立ち上げたとき、そのシェルがログインシェルとして起動されるように設定する。

```json
{
  "terminal.integrated.profiles.linux": {
    "bash": {
      "path": "bash",
      "icon": "terminal-bash",
      "args": ["-l"]
    }
  },
  "terminal.integrated.defaultProfile.linux": "bash"
}
```

## ローカルの git 設定を Dev Container に反映する

1. Git 管理されているプロジェクトの DevContainer を立ち上げたときに git のユーザー設定が反映されていないことがある。
2. dotfiles を Dev Container 内に展開する設定しても、この dotfiles ではユーザー設定を記載している `~/.gitconfig.local` を git 管理していないため GitHub 経由で dotfiles をインストールした際に git のユーザー設定が反映されない。

そこで、以下の設定をすることで、DevContainer内で git 設定を自動的に完了するようにした。

### 環境変数に git ユーザー情報を設定する

[04_git.bash](../../bash/public/04_git.bash) にて以下のように環境変数を設定するようにした。

```plain
git config user.name →  GIT_USER_NAME
git config user.email →  GIT_USER_EMAIL
git config user.signingkey →  GIT_USER_SIGNINGKEY
```

そのうえで、以下のどちらかを利用して、ローカルの環境変数を Dev Container 内に渡すようにする。
どちらか片方を実施すれば良い。

### A. vscode の settings.json にて `remote.containers.environment` を利用して環境変数を渡す

```json
{
  "remote.containers.environment": {
    "GIT_USER_NAME": "${localEnv:GIT_USER_NAME}",
    "GIT_USER_EMAIL": "${localEnv:GIT_USER_EMAIL}",
    "GIT_USER_SIGNINGKEY": "${localEnv:GIT_USER_SIGNINGKEY}"
  }
}
```

- 参考: [VSCodeのsetting.json](../../vscode-settings/profiles/win-15034/settings.json)

### B. devcontainer.json にて `containerEnv` を利用して環境変数を渡す

```json
{
  "containerEnv": {
    "GIT_USER_NAME": "${localEnv:GIT_USER_NAME}",
    "GIT_USER_EMAIL": "${localEnv:GIT_USER_EMAIL}",
    "GIT_USER_SIGNINGKEY": "${localEnv:GIT_USER_SIGNINGKEY}"
  }
}
```

- 参考: [devcontainer.json](../../devcontainer-example/.devcontainer/devcontainer.json)
