# ShellCheck GitHub Action 実装計画

## 概要

`.github/workflows/shellcheck.yml` を実装し、プルリクエストやメインブランチへのプッシュ時に自動的にシェルスクリプトの静的解析（ShellCheck）が行われるようにします。

## 実装内容

### [Component Name] Actions

#### [NEW] [shellcheck.yml](file:///Users/suzukikenichi/dotfiles/.github/workflows/shellcheck.yml)

- `ubuntu-latest` ランナーを使用。
- `bash/mise.toml` で定義されているチェック対象およびオプション (`-x`, `-P SCRIPTDIR`) を踏襲します。
- 特定のディレクトリ (`bash/`) 以下のスクリプトと、リポジトリルートにある主要なスクリプト (`install.sh`, `unlink.sh`) を対象にします。

## 検証計画

### 自動テスト

- 実際に GitHub にプッシュした際に Action が正常にパスすることを確認（ここではシンタックスチェックと、ローカルでの `mise run shellcheck` との整合性確認）。
