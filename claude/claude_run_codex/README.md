# with-codex-skills

Claude CodeとOpenAI Codex CLIを連携させるスキルです。

## 概要

このリポジトリには、Claude CodeからOpenAI Codex CLIを操作して協調作業を行うためのスキルが含まれています。

### 主な機能

- **セカンドオピニオン**: Codexに同じ質問を投げ、Claudeの回答と比較・検証
- **協調作業**: ClaudeとCodexが役割分担して1つのタスクを解決
- **対話モード**: tmuxでペインを分割し、両AIを視覚的に並行稼働

## 動作環境

以下のいずれかの環境で動作します:

- **macOS** - tmuxとCodex CLIがインストールされていること
- **Linux** - tmuxとCodex CLIがインストールされていること
- **Windows + WSL (Ubuntu)** - WSL内にtmuxとCodex CLIがインストールされていること

### 必要なツール

- [tmux](https://github.com/tmux/tmux) - ターミナルマルチプレクサ
- [OpenAI Codex CLI](https://github.com/openai/codex) - `npm install -g @openai/codex`
- [Claude Code](https://claude.ai/code) - `npm install -g @anthropic-ai/claude-code`

## インストール

ターミナルで以下のコマンドを実行:

```bash
# 1. Claude Codeのスキルディレクトリを作成
mkdir -p ~/.claude/skills

# 2. スキルを移動（パスは環境に合わせて変更）
cd -r SKILL_DOWNLOADED_PATH/with-codex-skills/with-codex ~/.claude/skills/

# 3. スクリプトに実行権限を付与
chmod +x ~/.claude/skills/with-codex/scripts/*.sh

# 4. 動作確認
~/.claude/skills/with-codex/scripts/codex-manager.sh

# 5. Codex CLIの確認
codex --version
```

## 使い方

### 重要: tmuxセッション内でClaude Codeを起動する

このスキルを利用するときは、Claude Codeを**tmuxセッション内で実行する必要があります**。

```bash
# 1. tmuxセッションを開始
tmux new-session -s claude

# 2. Claude Codeを起動
claude

# 3. スキルを使用（例）
# > /with-codex このコードをレビューして
```

スキルが実行されると、画面が左右に分割され:

- **左ペイン**: Claude Code
- **右ペイン**: OpenAI Codex CLI

両方のAIが同時に動作する様子を視覚的に確認できます。

### 手動でスクリプトを使う場合

```bash
# セットアップ（現在のペインを分割してCodexを起動）
~/.claude/skills/with-codex/scripts/codex-manager.sh setup

# プロンプト送信
~/.claude/skills/with-codex/scripts/codex-manager.sh send "your prompt"

# レスポンス待機
~/.claude/skills/with-codex/scripts/codex-manager.sh wait 30

# 出力キャプチャ
~/.claude/skills/with-codex/scripts/codex-manager.sh capture

# クリーンアップ（Codexペインを閉じる）
~/.claude/skills/with-codex/scripts/codex-manager.sh cleanup
```

## codex-manager.sh コマンド一覧

| コマンド | 説明 |
| --------- | ------ |
| `setup` | 現在のペインを分割し、右側でCodexを起動 |
| `send "prompt"` | Codexペインにプロンプト送信 |
| `capture [lines]` | Codexペインの出力をキャプチャ（デフォルト: 100行） |
| `wait [timeout]` | レスポンス安定まで待機（デフォルト: 60秒） |
| `cleanup` | Codexペインを閉じる |
| `status` | ペイン状態確認 |
| `focus` | Codexペインにフォーカス移動 |

## ファイル構成

```text
with-codex/
├── SKILL.md                    # スキル定義
├── scripts/
│   ├── codex-manager.sh        # tmux/Codex管理スクリプト
│   └── codex-exec.sh           # 非対話モードラッパー
└── references/
    └── workflows.md            # ワークフロー詳細
```

## 参考

- [GOROman](https://github.com/GOROman)氏がXでつぶやいていたのを参考にしてつくりました
  - 参考にした投稿: <https://x.com/GOROman/status/2011085523650298253?s=20>
