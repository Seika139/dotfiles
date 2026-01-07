# Gemini 関連ファイルの管理対象追加 計画書

`~/.gemini/GEMINI.md` と `~/.gemini/antigravity/global_workflows/` を `dotfiles` リポジトリで管理できるようにし、`mise` 経由でシンボリックリンクを管理できるようにします。

## 提案される変更

### [gemini]

#### [MODIFY] [mise.toml](file:///Users/suzukikenichi/dotfiles/gemini/mise.toml)
- リンク対象を定義しているループ (`for file in commands; do`) に `GEMINI.md` と `antigravity/global_workflows` を追加します。
- ネストしたディレクトリのリンクを作成する際、親ディレクトリ（`~/.gemini/antigravity`）が自動で作成されるように `mkdir -p` のロジックを確認/強化します。

#### [NEW] [GEMINI.md](file:///Users/suzukikenichi/dotfiles/gemini/profiles/hm-m1-mac/GEMINI.md)
- 現在 `~/.gemini/GEMINI.md` にあるファイルをこちらに移動（またはコピー）します。

#### [NEW] [global_workflows](file:///Users/suzukikenichi/dotfiles/gemini/profiles/hm-m1-mac/antigravity/global_workflows/)
- 現在 `~/.gemini/antigravity/global_workflows/` にあるディレクトリをこちらに移動（またはコピー）します。

## 検証計画

### 自動テスト / コマンド
- `mise -C gemini run status` を実行し、現状の「未存在」または「リンク切れ」を確認。
- `mise -C gemini run link` を実行して、シンボリックリンクを生成。
- 再度 `mise -C gemini run status` で正常にリンクされていることを確認。

### 手動確認
- `ls -la ~/.gemini/GEMINI.md` でリンク先が `dotfiles` を指しているか確認。
- `ls -la ~/.gemini/antigravity/global_workflows` で同様に確認。
