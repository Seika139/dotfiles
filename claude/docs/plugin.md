# Claude Code Plugin & Marketplace ナレッジ

## 概要

Plugin は Claude Code をスキル・エージェント・フック・MCP サーバー・LSP サーバーで拡張するパッケージ。
Marketplace は Plugin のカタログ（配布チャネル）。

## Plugin vs スタンドアロンスキル

| 項目     | スタンドアロン（`.claude/skills/`）      | Plugin                                          |
| -------- | ---------------------------------------- | ----------------------------------------------- |
| スキル名 | `/hello`                                 | `/plugin-name:hello`（名前空間付き）            |
| 用途     | 個人的なワークフロー、実験               | チーム共有、コミュニティ配布                    |
| 配置     | `.claude/skills/` or `~/.claude/skills/` | `.claude-plugin/plugin.json` を含むディレクトリ |
| 更新     | 手動                                     | Marketplace 経由で自動更新可能                  |
| スコープ | 配置場所に依存                           | user / project / local / managed                |

## Plugin のディレクトリ構造

```text
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # マニフェスト（必須ではないがほぼ必須）
├── skills/
│   └── skill-name/
│       └── SKILL.md          # スキル定義
├── commands/                  # コマンド（Markdown）
├── agents/                    # カスタムエージェント
├── hooks/
│   └── hooks.json             # イベントハンドラー
├── .mcp.json                  # MCP サーバー設定
├── .lsp.json                  # LSP サーバー設定
└── settings.json              # デフォルト設定
```

**注意**: `commands/`, `agents/`, `skills/`, `hooks/` は `.claude-plugin/` の外（プラグインルート）に配置する。

## plugin.json（マニフェスト）

```json
{
  "name": "my-plugin",           // 識別子（ケバブケース）。スキル名前空間になる
  "description": "説明",
  "author": { "name": "..." },
  "homepage": "...",
  "repository": "...",
  "license": "MIT",
  "keywords": ["..."],
  // コンポーネントのカスタムパス（省略時はデフォルト位置）
  "commands": ["./commands/"],
  "agents": ["./agents/security-reviewer.md"],
  "hooks": { ... },
  "mcpServers": { ... },
  "lspServers": { ... }
}
```

**注意**: 公式プラグインでは `version` フィールドは使用されていない。マーケットプレイスの `plugins` エントリ側でバージョンを管理する。

## SKILL.md のフォーマット

```markdown
---
description: スキルの説明（Claude が自動選択する際に使用）
user-invocable: true # true の場合、ユーザーが /plugin:skill で呼び出し可能
disable-model-invocation: true # true の場合、Claude の自動呼び出しを禁止
---

スキルの指示内容。
$ARGUMENTS でユーザー入力を受け取れる。
```

**注意**: `user-invocable: true` がないと `/plugin-name:skill-name` でのユーザー直接呼び出しができない。Claude が内部的に Skill ツールで呼び出すことは可能。

### フロントマター全フィールドリファレンス

すべてのフィールドはオプション。`description` のみ推奨。

| フィールド                 | 型          | デフォルト         | 説明                                                                           |
| -------------------------- | ----------- | ------------------ | ------------------------------------------------------------------------------ |
| `name`                     | string      | ディレクトリ名     | スキルの表示名・コマンド名（小文字・数字・ハイフンのみ、最大 64 文字）         |
| `description`              | string      | 本文の最初の段落   | スキルの説明。Claude が自動呼び出しの判断に使う（250 文字超は短縮される）      |
| `argument-hint`            | string      | なし               | オートコンプリートに表示されるヒント（例: `[issue-number]`）                   |
| `disable-model-invocation` | bool        | `false`            | `true` で Claude の自動呼び出しを禁止（`/name` の手動呼び出しのみ）            |
| `user-invocable`           | bool        | `true`             | `false` で `/` メニューから非表示（Claude のみが使うバックグラウンド知識向け） |
| `allowed-tools`            | string/list | なし               | スキル実行中に許可なしで使えるツール（例: `Read Grep Glob`）                   |
| `model`                    | string      | セッションのモデル | スキル実行時に使うモデルを指定                                                 |
| `effort`                   | string      | セッションから継承 | 努力レベル: `low`, `medium`, `high`, `max`（Opus 4.6 のみ）                    |
| `context`                  | string      | なし               | `fork` でサブエージェントとして隔離実行                                        |
| `agent`                    | string      | `general-purpose`  | `context: fork` 時のサブエージェント種類（`Explore`, `Plan` 等）               |
| `hooks`                    | object      | なし               | スキルのライフサイクルにスコープされたフック                                   |
| `paths`                    | string/list | なし               | スキルが有効化されるファイルパスの glob パターン                               |
| `shell`                    | string      | `bash`             | `` !`command` `` ブロックのシェル（`bash` or `powershell`）                    |

### 呼び出し制御の組み合わせ

| フロントマター設定               | ユーザー呼び出し | Claude 自動呼び出し | コンテキストへの読み込み                                   |
| -------------------------------- | ---------------- | ------------------- | ---------------------------------------------------------- |
| （デフォルト）                   | ○                | ○                   | 説明は常に含まれ、呼び出し時にフル読み込み                 |
| `disable-model-invocation: true` | ○                | ✕                   | 説明はコンテキストに含まれない。手動呼び出し時のみ読み込み |
| `user-invocable: false`          | ✕                | ○                   | 説明は常に含まれ、呼び出し時にフル読み込み                 |

### スキルコンテンツ内の変数・置換

| 変数                   | 説明                                                            |
| ---------------------- | --------------------------------------------------------------- |
| `$ARGUMENTS`           | 引数全体。コンテンツに存在しない場合は末尾に自動追加            |
| `$ARGUMENTS[N]` / `$N` | N 番目の引数（0 始まり）                                        |
| `` !`command` ``       | シェルコマンドの実行結果を注入（前処理、Claude は結果のみ見る） |
| `${CLAUDE_SESSION_ID}` | 現在のセッション ID                                             |
| `${CLAUDE_SKILL_DIR}`  | SKILL.md のあるディレクトリパス                                 |

### スキルコンテンツのパターン

**リファレンス型**（Claude が自動で適用する知識）:

```yaml
---
name: api-conventions
description: API design patterns for this codebase
---
When writing API endpoints:
  - Use RESTful naming conventions
  - Return consistent error formats
```

**タスク型**（手動で呼び出すアクション）:

```yaml
---
name: deploy
description: Deploy the application to production
context: fork
disable-model-invocation: true
---
Deploy the application:
1. Run the test suite
2. Build the application
```

**サブエージェント実行**（隔離コンテキストで実行）:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---
Research $ARGUMENTS thoroughly...
```

### サポートファイル

SKILL.md 以外にファイルを同梱可能。テンプレート・例・スクリプト等を分離し、SKILL.md からリンクで参照する:

```text
my-skill/
├── SKILL.md           # メイン指示（必須）
├── template.md        # Claude が埋めるテンプレート
├── examples/
│   └── sample.md      # 出力例
└── scripts/
    └── validate.sh    # Claude が実行するスクリプト
```

SKILL.md は 500 行以下を推奨。詳細なリファレンスは別ファイルに移動する。

## Marketplace の仕組み

### 構造

```text
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json      # カタログ定義
└── plugins/
    └── plugin-name/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/...
```

### marketplace.json

```json
{
  "name": "company-tools", // 識別子（ケバブケース）
  "owner": {
    "name": "DevTools Team",
    "email": "devtools@example.com"
  },
  "metadata": {
    "description": "説明",
    "version": "1.0.0",
    "pluginRoot": "./plugins" // 相対パスの基本ディレクトリ
  },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter", // 相対パス or オブジェクト
      "description": "説明",
      "version": "2.1.0"
    }
  ]
}
```

### Plugin ソースの種類

| ソース               | 形式     | 例                                                                          |
| -------------------- | -------- | --------------------------------------------------------------------------- |
| 相対パス             | `string` | `"./plugins/my-plugin"`                                                     |
| GitHub               | `object` | `{ "source": "github", "repo": "owner/repo", "ref": "v2.0", "sha": "..." }` |
| Git URL              | `object` | `{ "source": "url", "url": "https://gitlab.com/...", "ref": "main" }`       |
| Git サブディレクトリ | `object` | `{ "source": "git-subdir", "url": "...", "path": "tools/plugin" }`          |
| npm                  | `object` | `{ "source": "npm", "package": "@acme/plugin", "version": "^2.0.0" }`       |

## Marketplace の管理コマンド

```bash
# マーケットプレイスの追加
/plugin marketplace add owner/repo              # GitHub
/plugin marketplace add https://gitlab.com/...  # Git URL
/plugin marketplace add ./my-marketplace         # ローカルパス

# マーケットプレイスの管理
/plugin marketplace list
/plugin marketplace update marketplace-name
/plugin marketplace remove marketplace-name     # rm も可

# プラグインの操作
/plugin install plugin-name@marketplace-name
/plugin uninstall plugin-name@marketplace-name
/plugin enable plugin-name@marketplace-name
/plugin disable plugin-name@marketplace-name

# 検証
claude plugin validate .                # CLI から
/plugin validate .                      # Claude Code 内から

# 変更の反映
/reload-plugins
```

## インストールスコープ

| スコープ | 説明                           | 設定場所                      |
| -------- | ------------------------------ | ----------------------------- |
| User     | 全プロジェクトで自分用         | `~/.claude/settings.json`     |
| Project  | リポジトリの全コラボレーター用 | `.claude/settings.json`       |
| Local    | リポジトリ内で自分のみ         | `.claude/settings.local.json` |
| Managed  | 管理者が強制                   | 管理設定                      |

## チーム向け設定（`.claude/settings.json`）

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "your-org/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "code-formatter@company-tools": true,
    "deployment-tools@company-tools": true
  }
}
```

リポジトリを trust すると自動的にマーケットプレイス追加とプラグインインストールが促される。

## 管理者によるマーケットプレイス制限（managed-settings.json）

```json
{
  "strictKnownMarketplaces": [
    { "source": "github", "repo": "acme-corp/approved-plugins" },
    { "source": "hostPattern", "hostPattern": "^github\\.example\\.com$" }
  ]
}
```

- 空配列 `[]` = 完全ロックダウン
- 未定義 = 制限なし

## 開発・テスト

```bash
# ローカルテスト（インストール不要）— プラグインルートを直接指定
claude --plugin-dir ./my-plugin

# 複数プラグイン同時読み込み
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

- `--plugin-dir` は同名のインストール済みプラグインをオーバーライドする
- 変更後は `/reload-plugins` で反映
- **ローカル開発では `--plugin-dir` を推奨**: ローカルディレクトリ型マーケットプレイス（`/plugin` で登録）はマーケットプレイスルート全体をキャッシュにコピーするため、`source` フィールドでサブディレクトリを指定しても `skills/` がプラグインルート直下に配置されず、スキルが検出されない場合がある。`--plugin-dir` ならプラグインディレクトリを直接参照するのでこの問題を回避できる

## 特殊変数

| 変数                    | 用途                                                               |
| ----------------------- | ------------------------------------------------------------------ |
| `${CLAUDE_PLUGIN_ROOT}` | プラグインのインストールディレクトリ（キャッシュにコピー後のパス） |
| `${CLAUDE_PLUGIN_DATA}` | 永続データディレクトリ（更新後も保持）                             |
| `$ARGUMENTS`            | SKILL.md 内でユーザー入力をキャプチャ                              |

## 注意事項

- **マーケットプレイスルートとプラグインルートは分離する**: `source: "./"` でマーケットプレイスとプラグインを同一ディレクトリにすると、`marketplace.json` がプラグインキャッシュにもコピーされ、スキル検出が失敗する。必ず `plugins/` サブディレクトリに分離すること
- プラグインはキャッシュ（`~/.claude/plugins/cache/`）にコピーされるため、外部ファイル参照（`../`）は不可。シンボリックリンクで対応可能
- プライベートリポジトリは `GITHUB_TOKEN` / `GH_TOKEN` 等の環境変数でバックグラウンド自動更新に対応
- Marketplace の名前に予約語（`claude-plugins-official`, `anthropic-marketplace` 等）は使用不可
- `strict: true`（デフォルト）では `plugin.json` が権限。`strict: false` ではマーケットプレイスエントリが完全な定義

## スタンドアロンスキルから Plugin への移行

1. プラグインディレクトリ + `.claude-plugin/plugin.json` を作成
2. `.claude/commands/` -> `plugin/commands/`、`.claude/skills/` -> `plugin/skills/` にコピー
3. `settings.json` の hooks -> `hooks/hooks.json` に移動
4. `claude --plugin-dir ./my-plugin` でテスト
5. 動作確認後、元の `.claude/` から重複ファイルを削除

## 公式マーケットプレイスへの送信

- Claude.ai: <https://claude.ai/settings/plugins/submit>
- Console: <https://platform.claude.com/plugins/submit>

## 参考ドキュメント

- プラグイン作成: <https://code.claude.com/docs/ja/plugins>
- マーケットプレイス作成: <https://code.claude.com/docs/ja/plugin-marketplaces>
- プラグイン検出・インストール: <https://code.claude.com/docs/ja/discover-plugins>
- プラグインリファレンス: <https://code.claude.com/docs/ja/plugins-reference>
- 設定: <https://code.claude.com/docs/ja/settings#plugin-settings>
