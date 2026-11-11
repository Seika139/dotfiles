# Codex profiles

このディレクトリは、PC ごとに Codex の profile を切り替えるための設定セットです。

Claude 側の `~/.claude` 切り替えに近い構成ですが、Codex の `config.toml` は Codex 本体に書き換えられることがあるため、symlink ではなく生成ファイルとして扱います。

## 構成

```text
codex/
  mise.toml
  mise/scripts/
    link.sh
    sync_agents.sh
    pull_config.sh
    render_config.py
    sync_prompt_skills.py
  profiles/
    <profile>/
      AGENTS.md
      config.base.toml
      config.local.toml
      hooks.base.json
      hooks.local.json
      prompts/
      skills/
      custom-config/
  agents/
    <native-agent>.toml
  docs/
    native-agents.md
```

主な profile:

```bash
cd /home/ken/dotfiles/codex
mise run list
```

## 反映先

`mise run link` を実行すると、現在の profile が `~/.codex` に反映されます。

```text
~/.codex/AGENTS.md       -> codex/profiles/<profile>/AGENTS.md
~/.codex/prompts         -> codex/profiles/<profile>/prompts
~/.codex/custom-config   -> codex/profiles/<profile>/custom-config
~/.codex/skills/<skill>  -> codex/profiles/<profile>/skills/<skill>
~/.codex/agents/<name>.toml  通常ファイルとして配備
~/.codex/config.toml     通常ファイルとして生成
~/.codex/hooks.json      通常ファイルとして生成
```

`skills` は `~/.codex/skills` ディレクトリごとの symlink にはしません。Codex の `.system` skill を残すため、profile skill だけを個別に symlink します。

`agents` は package 共通の native Codex TOML を個別の通常ファイルとして配備します。役割の使い分けと衝突時のバックアップ規則は [docs/native-agents.md](docs/native-agents.md) を参照してください。

`prompts/` は Claude command 由来の元ファイル置き場です。現在の Codex CLI 0.125.0 では、`~/.codex/prompts/*.md` は独自 slash command として読み込まれません。そのため `mise run link` 時に `prompts/*.md` から `skills/<command-name>/SKILL.md` を生成し、`$command-name` として使えるようにしています。

## config.toml の運用

Codex の実行時設定は `~/.codex/config.toml` です。

このファイルは symlink ではなく、次の 2 ファイルを合成して生成します。

```text
codex/profiles/<profile>/config.base.toml
+ codex/profiles/<profile>/config.local.toml
= ~/.codex/config.toml
```

`config.base.toml` は git 管理する共有設定です。

例:

```toml
model_reasoning_effort = "xhigh"

[features.multi_agent_v2]
enabled = true
max_concurrent_threads_per_session = 3

[sandbox_workspace_write]
network_access = true
```

全 profile は Multi-Agent V2 を有効にし、同時 thread 数を3に設定します。この上限にはメイン session が含まれるため、メイン session と子 agent 2つまでが同時に動きます。V1 用の `[agents].max_depth` と `[agents].max_concurrent_threads_per_session` は設定しません。設定を使う端末では対象 profile を選択して `mise run link` を実行してください。`config.local.toml` で同じキーを定義すると、その端末では local 側の値が優先されます。

`config.local.toml` は git 管理しないローカル設定です。

例:

```toml
[projects."/home/ken/dotfiles"]
trust_level = "trusted"

[mcp_servers.openaiDeveloperDocs]
command = "npx"
args = ["-y", "mcp-remote", "https://developers.openai.com/mcp"]
```

同じキーがある場合は `config.local.toml` が優先されます。

## hooks.json の運用

`~/.codex/hooks.json` も symlink ではなく、`config.toml` と同様に生成ファイルとして扱います。
これは apm (Agent Package Manager) を利用して ponytail などの外部パッケージをインストールする際に、apm 自身が `~/.codex/hooks.json` を直接書き換えるためです。

`config.toml` の 2 ファイル単純合成とは違い、hooks.json は「自分で管理する内容」と「外部 (apm など) が書き込む内容」を役割分担する設計です。

- `hooks.base.json` / `hooks.local.json` には、**自分で管理したい hook だけ**を書きます。apm など外部由来の内容はここに書きません。
- `mise run link` を実行すると、`render_hooks.py` は `hooks.base.json` + `hooks.local.json` の内容に加えて、**その時点で `~/.codex/hooks.json` に入っている外部エントリを引き継いで**書き直します。profile が同じイベントの Ponytail hook を管理している場合は、古い APM 登録が二重起動しないよう、その Ponytail hook だけ引き継ぎ対象から除きます。

`hooks.base.json` は git 管理する共有設定、`hooks.local.json` は git 管理しないローカル設定です。

`../agents` にて `mise run update` が実行する `apm install -g --refresh --force` は `~/.codex/hooks.json` に**タグ無しで**直接エントリを書き込みます（例: `DietrichGebert/ponytail`）。通常の外部 hook は生成時に保持されますが、profile が同じイベントで管理する Ponytail hook は旧 APM 登録を除いて profile 側の設定を使います。外部 hook を `hooks.base.json` / `hooks.local.json` に手動でコピーしないでください。Ponytail の Windows 登録はこの例外として `hooks.local.json` に置き、`CLAUDE_PLUGIN_ROOT` を hook プロセス内で設定します。

通常の外部 hook は、`~/.codex/hooks.json` に既に入っている限り出自を問わず残ります。そのため `hooks.base.json` / `hooks.local.json` から通常 hook を削除しても `mise run link` だけでは消えません。完全に消したい場合は `~/.codex/hooks.json` を削除してから `mise run link` を実行してください。

旧構成では `~/.codex/hooks.json` が `profiles/<profile>/hooks.json` への symlink だったため、この変更を pull した直後は symlink がリンク切れ（リンク先のファイルが存在しない状態）になり、apm 由来のエントリは生成時に収穫できません。移行初回は `mise run link` の後に `../agents` で `mise run update` を実行して apm エントリを再生成してください。

### Downloads からのプロンプトをブロックする

全 profile の UserPromptSubmit hook は、セッションの作業ディレクトリがOSで解決したDownloadsまたはその配下なら、モデルへ送る前にプロンプトを拒否します。Windows Known Folder、Linux の user-dirs.dirs、macOS の ~/Downloads を参照し、WSL では Linux 側と Windows 側の保存先を確認します。WSL で Windows 側の保存先を確認できない場合や、Linux の `XDG_DOWNLOAD_DIR` がホーム自体を指す場合も、判定不能として拒否します。

Unix系 profile は `PATH` から `python3`、次に `python` を探して Python 3.11 以上で実行します。Windows profile は PowerShell から同じ順で解決します。Codexの起動環境からPythonを見つけられない場合もプロンプトを拒否するため、GUIからCodexを使う場合はその起動環境の `PATH` にPythonを含めてください。

`win-15034` profile のhook commandはPowerShell構文です。CodexのWindows hook実行シェルにPowerShellが設定されていることを前提とします。

このhookは、Downloadsを作業ディレクトリにしたセッションからのプロンプトをブロックします。起動時に `AGENTS.md` が読み込まれていても、そのプロンプトはモデルへ送られません。Downloads以外の場所から起動して別の場所にあるファイルを読ませるケースや、OS設定上のDownloads以外にブラウザの保存先を変更したケースは対象外です。拒否された場合は、信頼できるプロジェクトディレクトリから新しいCodexセッションを開始してください。

profile を `mise run link` で反映したあと、Codex の `/hooks` で追加された hook を確認して信頼してください。以前の試作版hookをすでに反映していた場合は、生成済みの `~/.codex/hooks.json` から `block_downloads.py` を直接実行する旧 `UserPromptSubmit` entry を削除してから `mise run link` を実行してください。rendererは生成済みファイルの既存entryを保持します。

## よく使うコマンド

profile の状態確認:

```bash
cd /home/ken/dotfiles/codex
mise run status --prof wsl-ubuntu
```

profile を `~/.codex` に反映:

```bash
mise run link --prof wsl-ubuntu
```

`prompts/` から command skill だけを再生成:

```bash
mise run sync_prompt_skills --prof wsl-ubuntu
```

profile を切り替え:

```bash
mise run switch --prof wsl-ubuntu
```

新しい profile を作成:

```bash
mise run create_profile --prof new-profile-name
```

Codex が `~/.codex/config.toml` に書き込んだ変更を profile 側へ取り込む:

```bash
mise run pull_config --prof wsl-ubuntu
```

`pull_config` は `~/.codex/config.toml` を `codex/profiles/<profile>/config.local.toml` にコピーします。既存の `config.local.toml` がある場合は backup を作ります。

## Codex が config を書き換えたとき

Codex の操作によって `~/.codex/config.toml` が変わった場合、profile 側は自動では更新されません。

まず差分状態を確認します。

```bash
mise run status --prof wsl-ubuntu
```

`~/.codex/config.toml differs from rendered profile config` と表示された場合、どちらを正にするかで操作が変わります。

Codex が書いた変更を残す場合:

```bash
mise run pull_config --prof wsl-ubuntu
```

profile 側の設定で上書きする場合:

```bash
mise run link --prof wsl-ubuntu
```

共有したい設定は `config.local.toml` から `config.base.toml` に移してください。秘密情報、PC 固有パス、trusted projects などは `config.local.toml` に残します。

## Command Skills

Claude の `commands/*.md` に相当するものは、Codex CLI では slash command ではなく command skill として使います。

```text
codex/profiles/<profile>/prompts/review-pr.md
codex/profiles/<profile>/skills/review-pr/SKILL.md
```

`prompts/review-pr.md` は元ファイルです。`mise run sync_prompt_skills` または `mise run link` によって `skills/review-pr/SKILL.md` が生成されます。

Codex TUI では `/review-pr` ではなく、次のように `$` で呼び出します。

```text
$review-pr
```

引数が必要な command は、skill 名の後ろにそのまま書きます。

```text
$review-pr 123
$create-issue 認証エラーを調査して修正する
$solve-issue 456
$worktree fix-login
```

サブディレクトリに置いた prompt は `-` 区切りの skill 名になります。

```text
codex/profiles/<profile>/prompts/release/prepare.md
```

```text
$release-prepare
```

例:

```text
prompts/release/execute.md           -> $release-execute
```

`$` を入力すると skill / plugin / app の候補が表示されます。`/skills` から skill 一覧を開くこともできます。

`/` は Codex CLI 本体の組み込みコマンド用です。profile の command skill は `/` の候補には表示されません。

profile を切り替えた後は、Codex を再起動すると `$` の候補が確実に更新されます。

## Skills

Codex の skill は profile の `skills/<skill-name>/SKILL.md` に置きます。

```text
codex/profiles/<profile>/skills/codex-review/SKILL.md
```

skill は slash command ではありません。Codex が説明文に合う作業だと判断したときに自動で使います。

明示的に使わせたい場合は、`$` で skill 名を指定します。

```text
$codex-review を使ってこの diff をレビューして
```

または通常の文章でも指定できます。

```text
codex-review skill を使って確認して
```

`~/.codex/skills/.system` は Codex 本体の system skill なので、この profile 管理では触りません。

## git 管理するものとしないもの

git 管理するもの:

```text
config.base.toml
hooks.base.json
AGENTS.md
prompts/
skills/
custom-config/ の共有可能なファイル
```

git 管理しないもの:

```text
config.local.toml
config.local.toml.backup.*
hooks.local.json
mise.local.toml
秘密情報や PC 固有の設定
```

`.gitignore` で `config.local.toml` は無視されます。

## トラブルシュート

現在どの profile が反映されているか確認:

```bash
mise run status --prof wsl-ubuntu
```

`~/.codex/config.toml` が symlink になっている場合:

```bash
mise run link --prof wsl-ubuntu
```

この task が symlink を通常ファイルに置き換えます。

Codex が書いた設定をなくしたくない場合は、上書き前に取り込みます。

```bash
mise run pull_config --prof wsl-ubuntu
```

`/` に `$create-issue` などが出ない場合:

```text
正常です。Codex CLI の独自 workflow は `$` または `/skills` から呼び出します。
```

`$` に command skill が出ない場合:

```bash
cd /home/ken/dotfiles/codex
mise run link --prof wsl-ubuntu
```
