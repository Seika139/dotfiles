# 日次スクリプトのプロファイル管理化 完了報告

## 変更内容

シェル起動時に1日に1度だけ実行されるスクリプトを、PCや環境ごとにプロファイルとして管理できるように刷新しました。

### [Component Name] bash

#### [NEW] [daily/.env](file:///Users/suzukikenichi/dotfiles/bash/daily/.env)

使用するプロファイル名を定義します。`.gitignore` によりGit管理から除外されています。

```bash
DAILY_PROFILE=default
```

#### [NEW] プロファイルディレクトリ

`bash/daily/profile/default/` を作成し、既存の `daily_init.sh` をこちらに移動しました。
今後、新しいプロファイルを作成する場合は `bash/daily/profile/<profile_name>/` を作成し、その中に `.sh` または `.bash` ファイルを配置してください。

#### [MODIFY] [07_daily_runner.bash](file:///Users/suzukikenichi/dotfiles/bash/public/07_daily_runner.bash)

- `bash/daily/.env` から `DAILY_PROFILE` を読み込むように変更。
- 指定されたプロファイルディレクトリ内のスクリプトをすべて一括で「1日1回」実行するようリファクタリング。
- 相対パスの解決ロジックを簡素化・安定化。

## 検証結果

### 手動確認内容

1. `DAILY_PROFILE=test_prof` を設定し、テストスクリプトを作成。
2. 初回起動時のみスクリプトが実行されることを確認。
3. 二回目以降は実行がスキップされることを確認。
4. キャッシュファイル（`~/.cache/bdotdir/daily/*.stamp`）が正しく作成されていることを確認。

## 使い方

1. `bash/daily/profile/` 下にディレクトリを作成します（例: `work`, `home`）。
2. その中に、1日1回実行したい処理を記述した `.sh` ファイルを置きます。
3. `bash/daily/.env` で `DAILY_PROFILE=work` のように指定して切り替えます。
