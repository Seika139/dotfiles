# ShellCheck GitHub Action 実装 完了報告

## 変更内容

GitHub Actions でシェルスクリプトを自動チェックするためのワークフローを実装しました。

### [Component Name] Actions

#### [NEW] [shellcheck.yml](file:///Users/suzukikenichi/dotfiles/.github/workflows/shellcheck.yml)

- **実行条件**: `main` ブランチへのプッシュ、プルリクエスト、およびシェルスクリプト (`.sh`, `.bash`) の変更時に起動します。
- **チェック内容**: `bash/mise.toml` で定義されているローカルでのチェック内容を完全に踏襲しました。
  - リポジトリ直下の `install.sh`, `unlink.sh` をチェック。
  - `bash/` ディレクトリ配下のすべての `.sh`, `.bash` ファイルを再帰的にチェック。
  - `-x` (外部ファイル読み込み許可) および `-P SCRIPTDIR` (相対パス解決) オプションを適用。

## 検証結果

### 整合性確認

- 実装したワークフローの `run` ステップの内容が、現在の `bash/mise.toml` の `shellcheck` タスクと一致していることを確認しました。これにより、ローカルでパスすれば CI でもパスする状態が保証されます。
