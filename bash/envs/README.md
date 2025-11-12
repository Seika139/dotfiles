# bash/envs ディレクトリの役割

このディレクトリは、Bash 起動時に読み込む「環境プロファイル」を管理します。`bash/.bashrc` から `bash/public/19_load_env.bash` が呼び出され、そこでこのディレクトリ配下のファイルを参照する仕組みになっています。

## 読み込みフロー

1. `bash/.bash_profile` → `bash/.bashrc` が読み込まれる。
2. `bash/.bashrc` 内のループで `bash/public/19_load_env.bash` が `source` される。
3. `19_load_env.bash` はこのディレクトリの `01_select_env.bash`（無い場合は sample 版）を読み込み、配列 `BDOT_ENV_PROFILE_FILES` に指定されたファイルを順番に `source` する。
4. 指定された各プロファイルファイル（例: `02_prof_a.bash`）で環境変数やエイリアスを設定すると、新しいシェルで自動的に反映される。

## 主要ファイル

- `01_select_env.sample.bash`
  - プロファイル選択用のサンプル。必要なプロファイル名を `BDOT_ENV_PROFILE_FILES` に列挙する。
- `01_select_env.bash`
  - 実際に利用する設定ファイル。`BDOT_ENV_PROFILE_FILES` に読み込みたいファイル名（相対パス）を配列で指定する。
- `02_prof_a.bash` / `03_prof_b.bash`
  - プロファイルのサンプル実装。環境変数や `export` を定義して利用する。
- `00_secrets.bash`
  - 機密情報の読み込み先（`bash/public/20_load_secrets.bash` から参照）。Git で共有しない値をここに記載する。

## 利用手順

1. `cp bash/envs/01_select_env.sample.bash bash/envs/01_select_env.bash`
2. `01_select_env.bash` を編集し、`BDOT_ENV_PROFILE_FILES` に読み込みたいファイル名を追加する。
3. 必要に応じて `02_prof_a.bash` 等を編集し、環境変数や設定を書き込む。
4. 新しいターミナルを開くと、指定したプロファイルの内容が自動で読み込まれる。

## 注意点

- ここに置く機密情報は `00_secrets.bash` のように Git で管理しないファイルに記載してください。
- 読み込み順は `BDOT_ENV_PROFILE_FILES` に書かれた順序に従います。依存関係がある場合は並びに注意してください。
