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

wsl2 がインストールされていない場合は [wsl.md](../../windows/wsl.md) を参考にインストールする。

codex を利用して作業する場合は Windows のファイルシステム /mnt/c/ ではなく wsl 上にリポジトリをクローンして作業する方が動作が早いのでおすすめ。（らしい）

## wsl 上で codex を利用する

既に volta が利用可能になっているが、これは [claude_with_wsl.md](../claude/claude_with_wsl.md) を参考にして wsl 上に volta をインストールしたため。

```bash
$ wsl # wsl を起動する

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
