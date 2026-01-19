# プロファイルベースの日次スクリプト実行への刷新

## 概要

`bash/public/07_daily_runner.bash` を拡張し、`bash/daily/profile/` 下のプロファイルごとに日次スクリプトを管理・実行できるようにします。
また、使用するプロファイルは `bash/daily/.env` (gitignore対象) で変更可能にします。

## ユーザー確認事項

> [!IMPORTANT]
> `bash/daily/.env` はGit管理対象外です。新規環境では手動で作成するか、デフォルト設定が使用されます。

## 変更内容

### [Component Name] bash

#### [NEW] [daily/.env](file:///Users/suzukikenichi/dotfiles/bash/daily/.env)

プロファイル名を指定する環境変数 `DAILY_PROFILE` を定義します（例: `DAILY_PROFILE=personal`）。

#### [NEW] [daily/profile/default/](file:///Users/suzukikenichi/dotfiles/bash/daily/profile/default/)

デフォルトのプロファイルディレクトリを作成します。

#### [MODIFY] [07_daily_runner.bash](file:///Users/suzukikenichi/dotfiles/bash/public/07_daily_runner.bash)

1. `bash/daily/.env` を読み込むロジックを追加。
2. `DAILY_PROFILE` が未設定の場合は `default` を使用。
3. `bash/daily/profile/${DAILY_PROFILE}/` 内の `*.sh` および `*.bash` を一括で日次実行対象とする。
   - 各ファイルごとに `bdotdir_run_once_per_day` を呼び出すように変更。

#### [DELETE] [daily_init.sh](file:///Users/suzukikenichi/dotfiles/bash/public/daily_init.sh)

不要になった古い初期化スクリプトを削除し、必要に応じて新しいプロファイル下へ移動します。

## 検証計画

### 自動テスト

なし。

### 手動確認

1. `bash/daily/profile/test_profile/` を作成し、テスト用の `test.sh` を配置。
2. `bash/daily/.env` に `DAILY_PROFILE=test_profile` を設定。
3. シェルを起動し、初回のみ `test.sh` が実行されることを確認。
4. プロファイルを切り替えた場合に、新しいプロファイルのスクリプトが正しく実行されることを確認。
