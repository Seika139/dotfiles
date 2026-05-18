# Claude Code 設定の双方向同期モデル

## 概要

CCWB (Claude Code with Bedrock 認証ヘルパー) を導入したマシンでは、`~/.claude/settings.json` を CCWB が物理書き換えするため、従来の symlink 一本運用は破綻する。
本ドキュメントは、これを回避しつつ「公開可能な設定は git 履歴で追跡 / 秘匿すべき内容は gitignored」の二層構造を維持する設計を定義する。

対象プロファイル: `cg-m2-mac` / `win-15034` / `wsl-ubuntu`。

## 背景

### 旧モデル（symlink 一本）

```text
~/.claude/settings.json       -> dotfiles/profiles/<host>/settings.json (symlink)
~/.claude/settings.local.json -> dotfiles/profiles/<host>/settings.local.json (symlink)
```

dotfiles で編集すれば直接 `~/.claude/` に反映され、明快だった。

### 衝突の発生

CCWB の認証ヘルパー (`credential-process --force-init` 等) は `~/.claude/settings.json` を **実ファイルとして上書き**する。symlink は破壊され、dotfiles 側との接続が切れる。

さらに調査の結果、Claude Code は **`~/.claude/settings.local.json` を読んでいない** ことが判明した。`--setting-sources` ヘルプに登場する `local` スコープは **プロジェクト下の `.claude/settings.local.json`** を指し、ユーザー全体の `~/.claude/settings.local.json` は対象外。

つまり認証必須項目 (`awsAuthRefresh`, `env.AWS_PROFILE` 等) を `~/.claude/settings.local.json` に書いても Claude Code は読まず、認証が通らない。

### dotfiles リポジトリは PUBLIC

本リポジトリは public 公開のため、クローズドな情報を git にコミットできない制約がある。

## 設計方針

### 双方向同期モデル

```text
                              [編集]
                                │
                                ▼
   dotfiles/profiles/<host>/settings.json (公開、git管理)
   dotfiles/profiles/<host>/settings.local.json (秘匿、gitignored)
                │                       ▲
                │ merge (link)          │ split (recover)
                ▼                       │
            ~/.claude/settings.json (Claude Code が読む唯一の原本)
                ▲
                │ [CCWB が物理書き換え]
                │
            CCWB credential-process / --force-init
```

- **`~/.claude/settings.json`** は実ファイル運用。symlink にしない。
- **`~/.claude/settings.local.json`** は使わない。Claude Code が読まないため。既存 symlink は撤去。
- **dotfiles 側 `settings.local.json`** は名前を維持するが役割は「dotfiles 内部の秘匿ストア」になる。

### キーの分類ルール

`recover` 時の split / `link` 時の merge は、以下の分類に従う。

| 分類                | 行き先                         | キー                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PORTABLE (公開)** | dotfiles `settings.json`       | トップレベル: `attribution`, `defaultMode`, `enabledPlugins`, `extraKnownMarketplaces`, `hooks`, `outputStyle`, `permissions`, `skipDangerousModePermissionPrompt`, `statusLine`<br>env: `ANTHROPIC_*MODEL`, `ANTHROPIC_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, `API_TIMEOUT_MS`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_ENABLE_TELEMETRY`, `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `MAX_THINKING_TOKENS`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_LOGS_EXPORTER`, `OTEL_METRICS_EXPORTER`, `___CLAUDE_CODE_MAX_OUTPUT_TOKENS` |
| **LOCAL (秘匿)**    | dotfiles `settings.local.json` | トップレベル: `awsAuthRefresh`, `otelHeadersHelper`<br>env: `AWS_PROFILE`, `AWS_REGION`, `CREDENTIAL_PROCESS_PATH`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_RESOURCE_ATTRIBUTES`, `SLACK_WEBHOOK_URL`                                                                                                                                                                                                                                                                                                                  |

#### 分類の判定基準

- 公開リポジトリにコミットしたくない値は **LOCAL**
  - 非公開の URL (`telemetry.ccwb.cyg.ninja`)
  - 非公開の識別子 (`ccwb-prod-apne-1` AWS プロファイル名、リージョン)
  - 組織情報 (`OTEL_RESOURCE_ATTRIBUTES` の `department=...`)
  - Webhook シークレット
- それ以外は **PORTABLE**

#### 絶対パスを含むキーは LOCAL

`awsAuthRefresh` / `otelHeadersHelper` / `env.CREDENTIAL_PROCESS_PATH` は値に絶対パス (`/Users/<username>/...` 等) を含む。Claude Code の認証フェーズで必要なキーだが、`~/.claude/settings.json` (実ファイル) には `link` 時に LOCAL 側からマージされるため、認証は問題なく通る。

LOCAL に置く理由:

- ユーザー名がパスに含まれるため、別マシン (異なる username) に dotfiles を持ち越すと壊れる。git にコミットすると persona が露出するリスクもある。
- 認証ヘルパーのインストール先 (`~/claude-code-with-bedrock/...`) はマシンごとに変わりうる。

CCWB のドキュメント上「上書き禁止」のキーだが、`recover` で取り込んだ値をそのまま `link` で書き戻す本設計では値を改変しないため、CCWB の意図には反しない。

#### `extraKnownMarketplaces` / `enabledPlugins` は marketplace ホワイトリスト

`extraKnownMarketplaces` (Claude Code の plugin marketplace 一覧) と `enabledPlugins` (有効化中の plugin 一覧) は、**marketplace 単位のホワイトリスト**で分類する。

```bash
PORTABLE_MARKETPLACES=["claude-plugins-official", "openai-codex"]
```

- **PORTABLE 行き**: ホワイトリストにある marketplace に紐づくキー
  - `extraKnownMarketplaces.<name>` で `<name>` がホワイトリスト一致
  - `enabledPlugins.<plugin>@<name>` で `<name>` がホワイトリスト一致
- **LOCAL 行き**: それ以外 (社内専用 marketplace 等)

ホワイトリスト方式を採用する理由:

- plugin / marketplace は外部リポジトリから取得するもので、後から社内専用が追加されるリスクが構造的に高い。fail-safe な「明示しないと公開しない」挙動が望ましい。
- marketplace 名と plugin 名 (`<plugin>@<marketplace>`) で命名が連動しているため、marketplace 単位の判定で両方のキーを整合的に振り分けられる。

ホワイトリストに新しい公開 OK な marketplace を追加するときは、`recover-settings.sh` の `PORTABLE_MARKETPLACES` 変数を編集する。

#### CCWB 手順書の「上書き禁止」リストとの関係

CCWB の手順書は次を「上書きしないでください」と指定している:

- 環境変数: `CLAUDE_CODE_USE_BEDROCK`, `AWS_REGION`, `AWS_PROFILE`, `CLAUDE_CODE_ENABLE_TELEMETRY`, `OTEL_*`
- 設定: `awsAuthRefresh`, `otelHeadersHelper`

これらの値は **CCWB が中央配布する**ため、dotfiles 側で勝手に違う値を書くと組織方針に追従できなくなる。本設計では「**値は変えず、置き場所を分類する**」のみで、CCWB の意図に反しない。

`recover` で取り込んだ値を git にコミットすれば、CCWB の中央値変更が**履歴として追跡可能**になる副次的メリットも得られる。

## タスクの責任分界

### `mise run recover`

外部（CCWB 等）が書き換えた `~/.claude/settings.json` を dotfiles に取り込む。

```text
~/.claude/settings.json (実ファイル)
    │
    │ jq で split
    ▼
dotfiles/.../settings.json     (PORTABLE 側のキーを抽出)
dotfiles/.../settings.local.json (LOCAL 側のキーを抽出)
```

旧設計と異なる点:

- symlink 復元処理は **削除**。実ファイル運用に切り替えたため。
- 最後に `link` を呼んで `~/.claude/settings.json` を再生成し、整合状態に戻す。

### `mise run link`

dotfiles の編集を `~/.claude/settings.json` に反映する。

```text
dotfiles/.../settings.json
dotfiles/.../settings.local.json
    │
    │ jq -s '.[0] * .[1]' で deep merge
    ▼
~/.claude/settings.json (実ファイル、書き出し)
```

- `settings.json` 系は **マージ書き出し方式**（symlink ではない）。
- `CLAUDE.md` / `commands` / `skills` / `rules` / `custom-config` は引き続き **symlink**。
- `~/.claude/settings.local.json` の symlink は **削除**（Claude Code が読まない）。

### `mise run status`

`~/.claude/settings.json` が dotfiles の最新マージ結果と一致しているかを判定する。

- **一致**: 整合状態。問題なし。
- **不一致**: 外部書き換え or dotfiles 編集後 `link` 未実行。`recover` か `link` を促すメッセージを出す。
- `CLAUDE.md` 等の symlink は従来通り存在確認。

### `mise run check` / `mise run check_env`

変更なし。内部ヘルパーとして `recover` / `link` / `switch` から呼ばれる。

### `mise run create_profile`

新規プロファイル作成時のテンプレ:

- `settings.json`: 個人カスタマイズの最小例（permissions, hooks 等）。
- `settings.local.json`: 空の `{}` または LOCAL キーのスケルトンのみ。

### `mise run switch` / `mise run list`

変更なし。`switch` は内部で `link` を呼ぶため、`link` の挙動変更に自動追従。

## ワークフロー

### シナリオ A: 個人カスタマイズを変更したい

```bash
vim ~/dotfiles/claude/profiles/cg-m2-mac/settings.json
mise run link
git add claude/profiles/cg-m2-mac/settings.json
git commit
```

### シナリオ B: CCWB が `~/.claude/settings.json` を書き換えた

`credential-process --force-init` 実行後や、CCWB の中央配布値が更新された後:

```bash
mise run status   # ドリフト検出
mise run recover  # split して dotfiles に取り込み + link で再生成
git diff
git commit        # 必要なら中央値変更を履歴に残す
```

### シナリオ C: 新マシンセットアップ

```bash
git clone <dotfiles>
~/claude-code-with-bedrock/bin/credential-process --force-init  # CCWB 初期化
mise run recover   # CCWB が書いた settings.json を dotfiles に取り込み
mise run link      # 必要に応じて
```

## 制約と注意

### 他マシンへ profile を持ち越せない

`awsAuthRefresh` / `otelHeadersHelper` / `env.CREDENTIAL_PROCESS_PATH` に**ユーザー名を含む絶対パス**が入る。`hm-m1-mac` (個人 Mac) や `wsl-ubuntu` でユーザー名が違うと壊れる。プロファイル単位で分離する現設計を維持する限り問題ないが、profile 共有は不可。

### CCWB 再インストール時の挙動

CCWB のインストーラは `~/.claude/settings.json` を `settings.json.bak.<timestamp>` に退避してから書き換える。新方針では実ファイル運用なので symlink 破壊は発生しない。`recover` で再取り込みすれば整合状態に戻る。

### `~/.claude/ccwb-overrides.yaml`

モデル選択や token 上限のユーザー上書きは CCWB の overrides yaml で行う仕様。dotfiles 側で symlink 化するかは未決定。秘匿性は低いので公開可能な範囲で symlink 化が望ましいが、本設計のスコープ外。

## 関連ファイル

- `claude/mise/scripts/link.sh` — マージ書き出しと symlink 配置
- `claude/mise/scripts/recover-settings.sh` — split と取り込み
- `claude/mise.toml` — タスク定義
- `claude/profiles/<host>/settings.json` — PORTABLE 設定（git 管理）
- `claude/profiles/<host>/settings.local.json` — LOCAL 設定（gitignored）
- `claude/.gitignore` — `**/settings.local.json` の除外定義
