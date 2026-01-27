#!/usr/bin/env bash

# Claude Code / OpenAI 関連のモデル指定は公開情報なのでここで定義する。
export AWS_REGION='us-east-1'
export CLAUDE_CODE_USE_BEDROCK=1
export _DISABLE_ANTHROPIC_MODEL="global.anthropic.claude-opus-4-5-20251101-v1:0"
export ANTHROPIC_MODEL="us.anthropic.claude-opus-4-5-20251101-v1:0"
export ANTHROPIC_SMALL_FAST_MODEL="global.anthropic.claude-sonnet-4-5-20250929-v1:0"
