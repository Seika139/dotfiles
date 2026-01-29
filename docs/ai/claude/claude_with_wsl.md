# Ubuntu on Windows などの WSL2 上で Claude を動かす

> ※ 注意 claude code のインストール方法は 2026.01.28 ごろに変わったので注意
> See: <https://code.claude.com/docs/ja/setup>
>
> native: `curl -fsSL https://claude.ai/install.sh | bash`
> brew: `brew install --cask claude-code`

Windows 上に Claude がインストールされていると Ubuntu 上で claude コマンドを実行したときに以下のようなエラーになる。
これは Windows 側（Volta の shim）を WSL(Ubuntu) から直接実行していて、先頭行が cmd ... になっているため WSL では cmd が見つからずエラーになっているから。

```plain
ken@CG15034:~/programs/cyg-sercuit/framework$ claude
/mnt/c/Users/S13316/AppData/Local/Volta/bin/claude: line 1: cmd: command not found
```

修正の方針は以下のどちらか

- WSL から cmd.exe を実行するように修正する（簡単）
- WSL 側に Claude をインストールする（面倒だが根本的な対応）

今回は後者を選択した。

```bash
# ubuntu 上に volta, node をインストールする
$ curl https://get.volta.sh | bash
$ exec $SHELL -l
$ volta -v
2.0.2
$ volta install node
$ node -v
v22.19.0
# claude をインストールする
$ npm install -g @anthropic-ai/claude-code
```

## 環境の設定

Slack の `ai活用_coding` チャンネルなどを参考に、Amazon Bedrock で Claude を使うための環境変数を設定する。
Opus4.1 の調子が悪いので Opus4 を使うようにした。

`~/.bashrc` に以下を追加した。

```bash
# Claude の環境変数を設定する
source "$HOME/bash/claude_envs.sh"
```

`~/bash/claude_envs.sh` に Windows 側で使っているのと同じ環境変数を設定する。

```bash
export AWS_REGION="us-east-1"
export CLAUDE_CODE_USE_BEDROCK="1"
# export ANTHROPIC_MODEL="us.anthropic.claude-opus-4-1-20250805-v1:0"
export ANTHROPIC_MODEL="us.anthropic.claude-opus-4-20250514-v1:0"
export ANTHROPIC_SMALL_FAST_MODEL="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
export AWS_ACCESS_KEY_ID="******"
export AWS_SECRET_ACCESS_KEY="******"
```

動作確認成功

```bash
$ claude -p hello
Hello! How can I help you with your project today?
```
