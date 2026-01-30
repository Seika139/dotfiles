# ln コマンドのフラグを `-sfv` から `-sfnv` に更新する計画

既存の `ln -sfv` コマンドを、より安全な `ln -sfnv` に変更します。これにより、リンク先がディレクトリ（またはディレクトリへのシンボリックリンク）である場合に、その中にリンクが作成されてしまう「二重リンク問題」を防ぎます。

## Proposed Changes

### Dotfiles Root

#### [MODIFY] [install.sh](file:///Users/suzukikenichi/dotfiles/install.sh)

- 複数の `ln -sfv` を `ln -sfnv` に置換します。

### Claude Profile Management

#### [MODIFY] [mise.toml](file:///Users/suzukikenichi/dotfiles/claude/mise.toml)

- `link` タスク内の `ln -sfv` を `ln -sfnv` に置換します。

### Codex Profile Management

#### [MODIFY] [mise.toml](file:///Users/suzukikenichi/dotfiles/codex/mise.toml)

- `link` タスク内の `ln -sfv` を `ln -sfnv` に置換します。

### Gemini Profile Management

#### [MODIFY] [mise.toml](file:///Users/suzukikenichi/dotfiles/gemini/mise.toml)

- `link` タスク内の `ln -sfv` を `ln -sfnv` に置換します。

### Shell Aliases

#### [MODIFY] [11_alias.bash](file:///Users/suzukikenichi/dotfiles/bash/public/11_alias.bash)

- `batcat` と `fdfind` のリンク作成箇所で `ln -s` を `ln -sfnv` に変更し、`-f` (force) と `-v` (verbose) も追加して動作を統一します。

## Verification Plan

### Automated Tests

- なし（フラグ変更のみのため、手動検証を優先）

### Manual Verification

1. `claude/mise.toml` の `link` タスクを実行し、`~/.claude/` 内のシンボリックリンクが正しく更新されるか確認する。
   - `mise -C claude run link`
   - `ls -l ~/.claude`
2. 他の `codex`, `gemini` についても同様に確認する。
3. `install.sh` の変更が文法的に正しいことを `shellcheck` で確認する。
   - `mise run shellcheck`
