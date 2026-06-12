#!/usr/bin/env bash

# 00_secrets.bash の例
export SOME_SECRET_KEY="your_secret_key_here"
# Claude / Codex の hook 通知 (claude/notify_discord.sh, codex/notify.sh) 用。
# 注意: ここはマシン全体に export されるので、汎用名 (DISCORD_WEBHOOK_URL 等) を
# 使わないこと。プロジェクト側の dotenv 読み込みが setdefault 型だと、この値が
# プロジェクト固有の .env を覆い隠して別チャンネルへ通知される事故が起きる。
export AGENT_NOTIFY_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/XXXXXXXXXX/YYYYYYYYYY"
export OPENCLAW_BACKUP_PASSPHRASE="your_passphrase_here"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/triggers/XXXXXXXXXX/YYYYYYYYYY/ZZZZZZZZZZ"
