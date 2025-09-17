# Claude Code

社内の PoC で Claude Code が利用できるので、Claude Code を使って得た知見をまとめる。

## API キーの設定

[Claudeを始める - Anthropic](https://docs.anthropic.com/ja/docs/get-started) にあるように `ANTHROPIC_API_KEY` を環境変数として設定するのが基本的な Claude の API を呼び出す方法。

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

ただし、社内のPoCでは [エンタープライズデプロイメント概要 - Anthropic](https://docs.anthropic.com/ja/docs/claude-code/third-party-integrations) の Amazon Bedrock を利用するため、`ANTHROPIC_API_KEY` の代わりに `ANTHROPIC_ENTERPRISE_API_KEY` を設定する必要がある。
具体的には Slack の ai活用_coding チャンネルのCanvasに記載されているが、そこに書かれている環境変数を読み込む必要がある。
自分の場合は [10_claude_envs.bash](../../../bash/private/10_claude_envs.bash) が bash 起動時に読み込まれるようになっている。

## settings.json

- [Claude Code設定 - Anthropic](https://docs.anthropic.com/ja/docs/claude-code/settings)

ユーザー設定は `~/.claude/settings.json` に、プロジェクトの設定は `./claude/settings.json` に保存する。

対話中に `/config` コマンドでも変更できますが、ファイルで管理することで再現性や共有性が高まります。

先述の API 実行用の環境変数も `setting.json` の `env` で設定できます。

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  }
}
```

## TODO

settings.local.json にある env は自動で読み込まれないので、手動で読み込む必要がある。この方法をメモしておく。
