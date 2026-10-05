# Claude Code

<!-- markdownlint-disable MD057 -->

社内の PoC で Claude Code が利用できるので、Claude Code を使って得た知見をまとめる。

## API キーの設定

[Claudeを始める - Anthropic](https://docs.anthropic.com/ja/docs/get-started) にあるように `ANTHROPIC_API_KEY` を環境変数として設定するのが基本的な Claude の API を呼び出す方法。

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

ログインして使う場合は、`claude` を起動して画面の案内に従うだけでよく、`ANTHROPIC_API_KEY` は不要。

## settings.json

- [Claude Code設定 - Anthropic](https://docs.anthropic.com/ja/docs/claude-code/settings)

ユーザー設定は `~/.claude/settings.json` に、プロジェクトの設定は `./claude/settings.json` に保存する。

対話中に `/config` コマンドでも変更できますが、ファイルで管理することで再現性や共有性が高まります。

先述の API 実行用の環境変数も `setting.json` の `env` で設定できます。

```json
{
  "permissions": {
    "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Read(~/.zshrc)"],
    "deny": [
      "Bash(curl *)",
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
