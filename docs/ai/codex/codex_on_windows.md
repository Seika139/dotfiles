# Windows で Codex を利用する場合

codex コマンドを実行すると、WSL のセットアップを促される。

```bash
$ codex

 For best performance, run Codex in Windows Subsystem for Linux (WSL2)

> 1. Exit and install WSL2
  2. Continue anyway
```

最初は Windows 上で直接 codex を使っていたが、mcp の起動や notify の実行が wsl から実行されていて、設定ファイルに記載したものが Windows 上で実行されなくて困った。
したがって WSL2 をインストールして利用することを推奨する。

詳細は [OpenAI のドキュメント](https://developers.openai.com/codex/windows) を参照すべし。

> ※ これを無視して Windows 上で直接実行する場合は `~/.codex/config.toml` に以下の設定を追加する。
>
> ```toml
> windows_wsl_setup_acknowledged = true
> ```

wsl2 がインストールされていない場合は、[WSL のインストール](https://learn.microsoft.com/ja-jp/windows/wsl/install)などを参考にインストールする。

wsl2 かどうかは以下のコマンドで確認できる。

```bash
$ wsl -l -v
  NAME              STATE           VERSION
* Ubuntu-24.04      Running         2
  docker-desktop    Running         2
```

## wsl 上で codex を利用する

```bash
$ wsl # wsl を起動する

# volta をインストールする（2025-09 参照）
volta install node@22

# Codex CLI をグローバルにインストール
volta install @openai/codex

# Codex を実行
codex
```

これで wsl 上で codex コマンドが実行できるようになる。

## serena を利用するには

wsl 上で pipx を経由して uv をインストールする

```bash
sudo apt update
sudo apt install -y pipx python3-venv

# PATH を通す（初回のみ）
/usr/bin/pipx ensurepath

# シェル再読み込み
source ~/.bashrc  # もしくは source ~/.zshrc

# 動作確認
pipx --version
pipx install uv
uv --version
uvx --version
```

<!-- TODO 2025-09 も参考にする -->

<!--
TODO

- 設定ファイルが Windows 側と WSL 側で分かれるので、 wsl 側で ~/.codex/config.toml を作成する必要がある。
- とにかく wsl と Windows の両方で codex  & serena & notify が動くようにする。
- wsl 上で codex を利用する場合は Windows にマウントされたパスでの作業が遅い（https://developers.openai.com/codex/windows) そのため、wsl 上にリポジトリをクローンして作業することを推奨する。
 -->
