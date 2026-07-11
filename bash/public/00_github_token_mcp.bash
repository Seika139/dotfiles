#!/usr/bin/env bash
# GitHub リモート MCP (api.githubcopilot.com/mcp) 用の Bearer トークンを env に供給する。
# Claude Code の MCP ヘッダは `Authorization: Bearer ${GITHUB_MCP_PAT}` を参照し、
# claude 起動時のプロセス環境からこの変数を解決する (~/.claude.json には平文を焼かない)。
#
# 値は gh CLI の認証トークンを流用する (疎通確認用途)。トークン値そのものは書かないので
# このファイルは commit しても安全。将来 read 権限を絞った fine-grained PAT に差し替える場合はここの右辺だけを差し替える (MCP 登録側は変更不要)。
GITHUB_MCP_PAT="$(gh auth token 2>/dev/null)"
export GITHUB_MCP_PAT

# ~/.claude.json に MCP の登録が済んでない場合は以下のコマンドを実行して登録する。
#  claude mcp add --transport http --scope user github https://api.githubcopilot.com/mcp/ --header 'Authorization: Bearer ${GITHUB_MCP_PAT}'
