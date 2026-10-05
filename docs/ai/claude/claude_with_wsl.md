# Ubuntu on Windows などの WSL2 上で Claude を動かす

> ※ 注意 claude code のインストール方法は 2026.01.28 ごろに変わったので注意
> See: <https://code.claude.com/docs/ja/setup>
>
> native: `curl -fsSL https://claude.ai/install.sh | bash`
> brew: `brew install --cask claude-code`

Windows 上に Claude がインストールされていると Ubuntu 上で claude コマンドを実行したときに以下のようなエラーになる。
これは Windows 側の CLI shim を WSL(Ubuntu) から直接実行していて、先頭行が cmd ... になっているため WSL では cmd が見つからずエラーになっているから。Windows 側の shim が Windows PATH 経由で WSL に混ざる場合も同様です。

```plain
user-name@xxxx:~/programs/framework$ claude
/mnt/c/Users/user-name/AppData/Local/.../claude: line 1: cmd: command not found
```

修正の方針は以下のどちらか

- WSL から cmd.exe を実行するように修正する（簡単）
- WSL 側に Claude をインストールする（面倒だが根本的な対応）

今回は後者を選択した。

```bash
# dotfiles を WSL のホームディレクトリに配置し、mise 設定を適用する
cd "$HOME/dotfiles"
# install 前に bash/daily/.env で DAILY_PROFILE=wsl-ubuntu を設定する
bash install.sh
# mise profile から導入された Node.js を確認する
node --version
# claude をインストールする
npm install -g @anthropic-ai/claude-code
```

## 環境の設定

WSL 側で `claude` を起動し、画面の案内に従ってログインする。環境変数の設定は不要。

動作確認成功

```bash
$ claude -p hello
Hello! How can I help you with your project today?
```
