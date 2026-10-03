# Windows で Codex を利用する場合

Windows では Codex CLI の実行環境として WSL2 を使う方法を案内します。Codex CLI は dotfiles の選択済み mise profile により Node.js とともに導入されます。

Windows 上で直接 `codex` を実行すると、WSL のセットアップを促される場合があります。

```text
For best performance, run Codex in Windows Subsystem for Linux (WSL2)
```

Windows 上で直接実行する場合は [OpenAI のドキュメント](https://developers.openai.com/codex/windows) を参照してください。WSL2 が未導入なら [wsl.md](../../windows/wsl.md) の手順で導入します。この警告を無視して Windows 上で直接実行する場合は `~/.codex/config.toml` に以下の設定を追加することで回避できます。

```toml
windows_wsl_setup_acknowledged = true
```

## WSL 上で Codex を利用する

WSL 内に dotfiles をセットアップし、`bash/daily/.env` で `DAILY_PROFILE=wsl-ubuntu` を選択して `install.sh` を実行します。Ubuntu では mise が未導入なら install.sh が apt 経由で導入を試み、その後、選択profileから Node.js と Codex CLI をインストールします。

なお、codex を利用して作業する場合は Windows のファイルシステム（`/mnt/c/` 配下）ではなく WSL 上にリポジトリをクローンして作業する方が動作が速いとされている。

```bash
codex --version
codex
```

`node` または `codex` が意図しない実行ファイルを指す場合は、WSL で `command -v node` と `command -v codex` を実行して PATH 上の場所を確認してください。mise 管理の実行ファイルが選ばれない場合は、mise の Bash 初期化と Windows PATH から混入した旧 shim の順序を確認してください。

## Serena を利用するには

WSL 上で pipx を経由して uv をインストールします。

```bash
sudo apt update
sudo apt install -y pipx python3-venv
/usr/bin/pipx ensurepath
source ~/.bashrc
pipx install uv
uv --version
uvx --version
```
