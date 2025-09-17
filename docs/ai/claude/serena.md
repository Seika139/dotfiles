# Serena MCP

## 2行要約

AIアシスタントに「コードの文脈を失わせずに理解させる」ためのツール。
uv と claude が使える環境なら、簡単に導入できる

- [AIコーディングの常識が変わる！Claudeを"覚醒"させる知性、「Serena」徹底解説｜Kyutaro](https://note.com/kyutaro15/n/n61a8825fe303)
- [LLMが理解できるコードの地図 ─ Serena MCPでAIが賢くなる仕組み](https://zenn.dev/contrea/articles/d18ee9447a9366)

プロジェクトごとに最初の1回だけ必要

```bash
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena-mcp-server --context ide-assistant --project $(pwd)
```

```bash
# claude のプロンプトに入力
/mcp__serena__initial_instructions
```

事前に `.claude/settings.local.json` に以下の設定を追加しておくと、インデックス更新時に権限の確認をスキップできるので楽。

```json
{
  "permissions": {
    "allow": [
      "mcp__serena__find_file",
      "mcp__serena__check_onboarding_performed",
      "mcp__serena__onboarding",
      "mcp__serena__list_dir",
      "mcp__serena__get_symbols_overview",
      "mcp__serena__find_symbol",
      "mcp__serena__write_memory",
      "mcp__serena__think_about_collected_information"
    ],
    "deny": [],
    "ask": []
  }
}
```
