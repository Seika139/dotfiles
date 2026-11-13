# Claude Code 設定の双方向同期モデル

## 概要

dotfiles リポジトリは public のため、秘匿すべき値を commit できず、従来の symlink 一本運用では秘匿値を置く場所がない。
本ドキュメントは、「公開可能な設定は git 履歴で追跡 / 秘匿すべき内容は gitignored」の二層構造を維持する設計を定義する。

対象プロファイル: `cg-m2-mac` / `win-15034` / `wsl-ubuntu`。

## 背景

### 旧モデル（symlink 一本）

```text
~/.claude/settings.json       -> dotfiles/profiles/<host>/settings.json (symlink)
~/.claude/settings.local.json -> dotfiles/profiles/<host>/settings.local.json (symlink)
```

dotfiles で編集すれば直接 `~/.claude/` に反映され、明快だった。

### symlink 一本運用をやめた理由

Claude Code は **`~/.claude/settings.local.json` を読まない**。`--setting-sources` ヘルプに登場する `local` スコープは **プロジェクト下の `.claude/settings.local.json`** を指し、ユーザー全体の `~/.claude/settings.local.json` は対象外。

つまり秘匿値を `~/.claude/settings.local.json` に分けて置いても Claude Code は読まず、設定が反映されない。

### dotfiles リポジトリは PUBLIC

本リポジトリは public 公開のため、クローズドな情報を git にコミットできない制約がある。
symlink 一本運用では `~/.claude/settings.json` の全内容が git 管理下に入るため、秘匿値を置けない。

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
             │ [手元で変更]
```

- **`~/.claude/settings.json`** は実ファイル運用。symlink にしない。
- **`~/.claude/settings.local.json`** は使わない。Claude Code が読まないため。既存 symlink は撤去。
- **dotfiles 側 `settings.local.json`** は名前を維持するが役割は「dotfiles 内部の秘匿ストア」になる。

### キーの分類ルール

`recover` 時の split / `link` 時の merge は、以下の分類に従う。

```text
local    = LOCAL_KEYS ∪ LOCAL_ENV_KEYS ∪ 非 portable な marketplace ∪ provenance ∪ 非 portable な hooks エントリ
portable = SOURCE (~/.claude/settings.json) から local を引いたもの
```

| 分類                | 行き先                         | キー                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **PORTABLE (公開)** | dotfiles `settings.json`       | トップレベル: `attribution`, `advisorModel`, `defaultMode`, `enabledPlugins`, `extraKnownMarketplaces`, `model`, `outputStyle`, `permissions`, `skipDangerousModePermissionPrompt`, `statusLine`<br>env: `ANTHROPIC_*MODEL`, `ANTHROPIC_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`, `API_TIMEOUT_MS`, `CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `MAX_THINKING_TOKENS`, `___CLAUDE_CODE_MAX_OUTPUT_TOKENS`<br>`hooks`: コミット済み `settings.json` の同一イベントに完全一致するエントリ |
| **LOCAL (秘匿)**    | dotfiles `settings.local.json` | env: `SLACK_WEBHOOK_URL`<br>`hooks`: 上記以外のすべてのエントリ (`~/.claude/` 側で追加・編集されたものを含む)                                                                                                                                                                                                                                                                                                                                                            |

#### 分類の判定基準

- 公開リポジトリにコミットしたくない値は **LOCAL**
  - Webhook シークレット
  - マシン固有の絶対パス (`hooks` の `command` に含まれる `C:\Users\<username>\...` 等)
- それ以外は **PORTABLE**

#### `hooks` はエントリ単位で分類する

`hooks` はトップレベルのキー名ホワイトリストだけでは分類できない。`~/.claude/settings.json` (マージ済みの SOURCE) には `hooks.PreToolUse` のようにイベント名単位で配列が並ぶだけで、各エントリが元々 `settings.json` 由来か `settings.local.json` 由来かの情報は残っていない。内容 (絶対パスの有無) で判定する方式も採用しない。

そこで `link` と `recover` の両方をエントリ単位でそろえる。

- **merge (`link` / `status`)**: `mise/scripts/merge-settings.jq` で、hooks 以外は `.[0] * .[1]` (local 優先) で deep merge し、`hooks` だけはイベントごとに `settings.json` の配列、`settings.local.json` の配列の順に連結する。local 側のエントリのうち portable 側と完全一致するものは重複として除去する。`hooks` がオブジェクトでない、またはイベントの値が配列でない場合はエラーで中断する。
- **split (`recover`)**: `SOURCE.hooks[E]` の各エントリについて、コミット済み `settings.json` の `hooks[E]` に完全一致するエントリがあれば portable、それ以外はすべて local に振り分ける。空になったイベントや空の `hooks` は出力しない。

同じイベント名 (例: `Stop`) を `settings.json` と `settings.local.json` の両方に置いてよい。どちらの配列も `~/.claude/settings.json` に届き、`recover` でもエントリ単位で元のファイルに戻る。ただし `recover` 後の `link` で、イベント内のエントリ順が「portable、local」の順に並び替わることがある。

この方式では、コミット済み `settings.json` に無い hook エントリはすべて local 行きになる (旧方式の「既存 `settings.local.json` に無いイベントは portable」とは既定が逆)。`/hooks` や `~/.claude/settings.json` の手編集で追加した hook は `settings.local.json` に取り込まれるため、公開したい hook は profile の `settings.json` を直接編集してから `mise run link` を実行する。

#### `env` 等は provenance (由来ベース) で分類する

hooks 以外で、マージ済みの SOURCE からはどちらのファイル由来かを判別できないキーは、「既存の `settings.local.json` に既にあるキーは local に留める」を判定ソースとして使う。トップレベルキー `K` について、`recover` 実行前の `settings.local.json` (`existing_local`) と `SOURCE` を比較する。

- `existing_local[K]` と `SOURCE[K]` が**両方オブジェクト**なら、`existing_local[K]` のサブキーのうち `SOURCE[K]` にも存在するものだけを local に振り分ける。`env` の変数名単位の分類はこの仕組みの上に成り立っており、`LOCAL_ENV_KEYS` ホワイトリストと provenance の union で決まる。
- それ以外 (配列・スカラー、または型が食い違う場合) は `K` を丸ごと local に振り分ける。

provenance は**「行き先」を決めるだけで「存在」を作らない**: `SOURCE` に存在しないキーは `existing_local` にあっても出力に復活させない。素朴に「既存 local を丸ごと union する」実装だと、`~/.claude/` から意図的に削除した設定が復活し、続く `link` で押し戻されてしまうため、`SOURCE` にあるキーだけを対象にする。

`LOCAL_KEYS` (現在は空配列)・marketplace 系 (`extraKnownMarketplaces` / `enabledPlugins`)・`hooks` は既に専用ロジックがあるため provenance の対象外 (二重判定を避ける)。

provenance は**一方向ラチェット**である。あるキーが一度 `settings.local.json` に入ると、`SOURCE` に存在し続ける限り永久に local のままになる。local から portable に戻す仕組みは無く、誤分類は `settings.local.json` を手編集して該当キーを取り除く以外に修正手段が無い。

**同一の `env` 変数名を `settings.json` と `settings.local.json` の両方に置いてはならない**。hooks 以外は `.[0] * .[1]` で local が上書きするため、同じ変数名が両ファイルにあると `link` 実行時に git 管理側の値は `~/.claude/settings.json` に届かず、続く `recover` では provenance によりそのまま local 判定され続ける。結果として `settings.json` 側のコミット済み値が警告もエラーもなく消える (データロス)。

#### 書き込み前の安全ガード

provenance は既存 `settings.local.json` を参照する自己参照的な仕組みのため、参照先が無い/不足している状態 (`settings.local.json` は `.gitignore` の対象で、git clone 直後は必ず不在) では保護が働かない。また hooks の分類はコミット済み `settings.json` を基準にするため、`link` 前の古い `~/.claude/settings.json` から `recover` すると portable なエントリが失われ得る。分類ルール自体は変えず、書き込み直前の最後の防波堤として `recover-settings.sh` に 3 つのガードを置いている。いずれも確認プロンプトより前に評価するため、非対話モードでも効く。

- **ガード A (中断)**: 書き込み予定の `settings.json` (PORTABLE_JSON) の文字列値に、このマシンの実際のホームディレクトリ (POSIX 形式、`C:\Users\X` 形式、`C:/Users/X` 形式のいずれか) が含まれていたら、エラーメッセージを出して非ゼロで終了する。書き込み・バックアップ・`link` 呼び出しには到達しない。パスの「形」(`/Users/` や `/home/` のような汎用パターン) では判定しない。移植可能な絶対パス (`/usr/bin/...` 等) を誤検知するため、必ず「このマシンの実際の `$HOME`」で照合する。
- **ガード B (警告)**: provenance が local に振り分けたサブキー (`env` の変数名等) が、コミット済み `settings.json` の同名キーと衝突していたら警告を出す。中断はしない。上記の「同一の `env` 変数名を両方に置いてはならない」制約への違反を検知するためのもの。
- **ガード C (中断)**: コミット済み `settings.json` の hooks エントリのうち、`~/.claude/settings.json` の同一イベントに完全一致で存在しないものがあれば、該当イベント名を表示して非ゼロで終了する。`settings.json` を編集した後に `link` していない、または `~/.claude/` 側で portable な hook を編集・削除した場合に発生する。先に `mise run link` を実行するか、両ファイルを手動で揃えてから再実行する。

#### 移行時の注意 (hooks のエントリ単位マージ導入)

旧方式では、同じイベント名が両ファイルにあると `settings.local.json` の配列が `settings.json` の配列を丸ごと置換していた。新方式では両方の配列が連結されて実行されるため、そのような環境では `link` 後に `settings.json` 側の hook も動き始める。更新後は `mise run status` で `~/.claude/settings.json` との差分を確認し、意図しない hook が増えていないかを確かめる。

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

## タスクの責任分界

### `mise run recover`

`~/.claude/settings.json` を手元で変更した後に、その内容を dotfiles に取り込む。

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
    │ jq -s -f merge-settings.jq で deep merge (hooks はイベント単位で連結)
    ▼
~/.claude/settings.json (実ファイル、書き出し)
```

- `settings.json` 系は **マージ書き出し方式**（symlink ではない）。
- `CLAUDE.md` / `commands` / `skills` / `rules` / `custom-config` は引き続き **symlink**。
- `~/.claude/settings.local.json` の symlink は **削除**（Claude Code が読まない）。
- APM が user settings に配備する Ponytail hook は plugin runtime 外で実行されるため、hook command 内でだけ APM package root を設定する。全 hook 共通の `env.CLAUDE_PLUGIN_ROOT` には設定しない。

### `mise run status`

`~/.claude/settings.json` が dotfiles の最新マージ結果と一致しているかを判定する。

- **一致**: 整合状態。問題なし。
- **不一致**: 手元での変更 or dotfiles 編集後 `link` 未実行。`recover` か `link` を促すメッセージを出す。
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

### シナリオ B: `~/.claude/settings.json` を手元で変更した

`/config` や手動編集などで `~/.claude/settings.json` を直接変更した後:

```bash
mise run status   # ドリフト検出
mise run recover  # split して dotfiles に取り込み + link で再生成
git diff
git commit
```

### シナリオ C: 新マシンセットアップ

```bash
git clone <dotfiles>
mise run link      # settings.json と settings.local.json を merge して ~/.claude/settings.json を生成
```

`settings.local.json` は gitignored のため clone 直後は存在しない。秘匿値が必要なら別途 `claude/profiles/<host>/settings.local.json` を用意してから `link` を実行する。

## 関連ファイル

- `claude/mise/scripts/link.sh` — マージ書き出しと symlink 配置
- `claude/mise/scripts/merge-settings.jq` — `link` / `status` 共通のマージロジック
- `claude/mise/scripts/recover-settings.sh` — split と取り込み
- `claude/mise.toml` — タスク定義
- `claude/profiles/<host>/settings.json` — PORTABLE 設定（git 管理）
- `claude/profiles/<host>/settings.local.json` — LOCAL 設定（gitignored）
- `claude/.gitignore` — `**/settings.local.json` の除外定義
