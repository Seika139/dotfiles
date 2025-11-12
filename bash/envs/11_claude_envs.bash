#!/usr/bin/env bash

# Claude / Bedrock / OpenAI 関連のモデル指定は公開情報なのでここで定義する。
export ANTHROPIC_MODEL='us.anthropic.claude-3-7-sonnet-20250219-v1:0'
# export ANTHROPIC_MODEL='us.anthropic.claude-sonnet-4-20250514-v1:0'
# export ANTHROPIC_MODEL='us.anthropic.claude-opus-4-20250514-v1:0'
export ANTHROPIC_SMALL_FAST_MODEL='us.anthropic.claude-3-5-sonnet-20241022-v2:0'
# export ANTHROPIC_SMALL_FAST_MODEL='us.anthropic.claude-3-5-haiku-20241022-v1:0'
export AWS_REGION='us-east-1'
export CLAUDE_CODE_USE_BEDROCK=1
