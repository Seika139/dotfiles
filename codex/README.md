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
network_access = true
model = "gpt-5.6-terra"
model_reasoning_effort = "xhigh"
```

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
- `mise run link` を実行すると、`render_hooks.py` は `hooks.base.json` + `hooks.local.json` の内容に加えて、**その時点で `~/.codex/hooks.json` に入っているエントリを出自に関わらずすべてそのまま残し**た上で書き直します。つまり `~/.codex/hooks.json` は「自分で管理する分」と「前回までに外部が書き込んだ分」を毎回引き継ぎながら再生成される、蓄積型の生成ファイルです。

`hooks.base.json` は git 管理する共有設定、`hooks.local.json` は git 管理しないローカル設定です。

`../agents` にて `mise run update` が実行する `apm install -g --refresh --force` は `~/.codex/hooks.json` に**タグ無しで**直接エントリを書き込みます（例: `DietrichGebert/ponytail`）。`render_hooks.py` はタグを見るのではなく、再生成時点で既存の `~/.codex/hooks.json` に入っているエントリを（`hooks.base.json` / `hooks.local.json` の内容と合わせて）そのまま残すため、apm など外部が書き込んだ hook を消してしまうことはありません。そのため `hooks.base.json` / `hooks.local.json` に apm 由来のエントリを手動でコピーしてはいけません（次の `apm install -g` で二重に書き込まれ、`~/.codex/hooks.json` の中身が重複します）。

この「そのまま残す」動作には制約があります。`~/.codex/hooks.json` に既に入っているエントリは、その出自（apm か過去の `hooks.base.json` か）に関わらず無条件に残り続けるため、`hooks.base.json` / `hooks.local.json` からエントリを削除しても `mise run link` だけでは反映されません。完全に消したい場合は `~/.codex/hooks.json` を削除してから `mise run link` を実行してください。

旧構成では `~/.codex/hooks.json` が `profiles/<profile>/hooks.json` への symlink だったため、この変更を pull した直後は symlink がリンク切れ（リンク先のファイルが存在しない状態）になり、apm 由来のエントリは生成時に収穫できません。移行初回は `mise run link` の後に `../agents` で `mise run update` を実行して apm エントリを再生成してください。

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
