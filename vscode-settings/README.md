# VS Code Settings

mise を使用して、VS Code と Cursor の設定ファイルを同期し、管理するためのツールです。

`mise run dump` コマンドを使用して、現在のエディタの keybindings.json・tasks.json・snippets と拡張機能リストをプロファイルへエクスポートします。settings.json はエクスポートされず、書き戻しには `mise run pull` を使います (後述)。
`mise run sync` コマンドを使用して、VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。

## Dependencies

- `mise`: タスクランナー。インストール方法は、[mise の公式サイト](https://mise.jdx.dev/getting-started.html)を参照してください。
- `bash`: Unix シェル。通常は Linux や macOS にプリインストールされていますが、Windows では WSL（Windows Subsystem for Linux）や Git Bash などの Unix 互換環境を使用してください。

## Usage

`mise run` コマンドを使用して、設定ファイルの操作を行います。以下は主なタスクです。

### vars

設定ファイルの変数や、実行環境に関する情報を表示します。

```bash
mise run vars
```

### status

エディタの設定ファイルが正しく同期されているかを確認します。

```bash
mise run status
```

### dump

現在のエディタの keybindings.json・tasks.json・snippets と拡張機能リストをプロファイルへエクスポートします。settings.json はスキップされるので、`mise run settings-diff` で差分を確認し、`mise run pull` で該当する層に書き戻してください。
`editor` は `vscode`、`cursor`、`antigravity` のいずれかで、省略すると `vscode` です。

```bash
mise run dump <vscode|cursor|antigravity>
```

### sync

VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。
どの設定が同期されるかは `mise run vars` コマンドで確認できます。

```bash
mise run sync
```

### pull

エディタで変更した settings.json を、3 層 (shared / profile / local) へテキストのまま書き戻します。まず `--dry-run` で更新・追加・削除の一覧を確認してから実行してください。

```bash
mise run pull --dry-run
mise run pull
mise run pull --editor cursor --prune
```

- オプションは `--prof <prof>`、`--editor <vscode|cursor|agy>` (既定は `vscode`)、`--dry-run`、`--prune`、`--local` です。
- 値が変わった既存キーは、そのキーが属する層のエントリの値だけを置換します。リーダーコメント、キー行、行末コメントは残ります。元の値が 1 行なら 1 行で、複数行なら `indent=2` 相当で整形して書きます。値の内部にあったコメントは消えます。
- shared に属するキーの値を変えた場合も、shared のファイルが更新されます。他の PC に影響するので内容を確認してください。
- エディタにだけあるキーは、既定で `profiles/<PC>/settings.json` に追加されます。`--local` を付けるか機密判定に該当するキーは `settings.local.json` に追加され、無ければ作成されます。追加後は昇順の位置に並びます。
- shared へは自動追加しません。共通にしたいキーは手で shared に移してください。
- 機密判定は、キーまたは値の文字列 (入れ子も含む) が `cygames`、`ochlo`、`/Users/`、`/home/`、`C:\Users`、`AppData`、`~/` で始まるパス、`.jp` `.local` `.internal` `.corp` の URL のいずれかに該当する場合、またはキー名が `github-enterprise` で始まる場合です。判定の正規表現は `settings.py` の `SENSITIVE_PATTERNS` にあり、追加できます。
- 画面にはキー名と行き先だけを表示し、値は表示しません。
- 合成結果にあってエディタに無いキーは「削除されたキー」として報告するだけです。`--prune` を付けたときだけ、そのキーを属する層からリーダーコメントごと削除します。
- 同じキーが複数の層にある場合は、エラーで中断します。
- 書き込みの前に、全層の変更後テキストの検証と、pull 後の合成結果がエディタの内容と意味的に一致することの確認を行い、失敗した場合は何も書きません。
- `settings.local.json` は未追跡のため、変更する場合のみ `settings.local.json.bak-日時` を同じディレクトリに残します。他の層は git で戻せるのでバックアップを作りません。

### settings-diff / settings-check

`mise run settings-diff` は合成した settings.json と各エディタの現在の settings.json を意味的に比較し、追加・削除・変更されたキーを表示します。コメントとキーの順序の差は無視されます。

`mise run settings-check` は全プロファイルについて、重複キーとソート違反を検査します。違反があると非 0 で終了します。

## settings.json の 3 層構成

settings.json は symlink ではなく、次の 3 層を合成した結果を各エディタに実ファイルとして書き込みます。

- `shared/settings.json`: 全 PC 共通の設定です。コミットします。
- `profiles/<PC>/settings.json`: PC 固有の設定です。コミットします。
- `profiles/<PC>/settings.local.json`: 社内ホスト名やホームパスなど、公開したくない値を置く層です。`.gitignore` により未追跡で、無くても構いません。

合成の順序は shared、profile、local です。各層のトップレベルエントリを、直前のコメント (リーダーコメント) ごとテキストのまま連結するので、コメントは消えません。

### キーは 1 層にだけ置く

同じトップレベルキーが複数の層に現れると、`render` と `check` はエラーになります。上書きはできないので、キーはちょうど 1 つの層に置いてください。共通にしたい値は shared に移し、各 profile から削除します。

### ソート規則

各層のファイル内のトップレベルキーは、文字列の昇順 (単純な ASCII ソート) に並べます。リーダーコメントはキーと一緒に動き、ネストした中身はソートしません。

並べ替えは `mise run sort` で行います。対象は shared、選んだプロファイルの `settings.json`、存在する場合の `settings.local.json` です。

```bash
mise run sort --dry-run
mise run sort
mise run sort --all
```

- `--prof <prof>` でプロファイルを選べます。省略時は `DEFAULT_PROFILE` です。`--all` を付けると全プロファイルが対象になります。
- `--dry-run` は並べ替えが必要なファイルを表示するだけで、何も書きません。
- 全ファイルを検証してから、並べ替えが必要なファイルだけを書き込みます。変更が無ければ「並べ替えは不要です」と表示します。
- `settings.local.json` は未追跡なので、書き換える場合のみ `settings.local.json.bak-日時` を同じディレクトリに残します。
- 並べ替え後に、対象プロファイルの `check` を実行して結果を表示します。

### 新規プロファイルの作り方

`profiles/<PC>/settings.json` を `{}` だけの内容で作成し、`mise run settings-check` で検査してください。共通設定は shared から合成されるので、その PC 固有の設定だけを追記します。公開したくない値は `profiles/<PC>/settings.local.json` に置きます。

### スクリプト

`mise/scripts/settings.py` のサブコマンドは `render --profile <PC> [--output PATH]`、`check --profile <PC>`、`sort FILE...`、`diff --profile <PC> --target PATH` です。標準ライブラリのみで動作し、テストは `python3 mise/scripts/test_settings.py` で実行できます。

### sync / status / dump の挙動

- `sync` は settings.json を合成して実ファイルとして書きます。既存が symlink なら削除してから書きます。既存が実ファイルで合成結果と意味的に異なる場合は、上書きせずに警告して非 0 で終了し、`mise run settings-diff` を案内します。旧方式の残骸などで不要なら `mise run sync -- --force` で、`settings.json.bak-日時` を同じディレクトリに残して上書きできます。実ファイルへの書き込みは同じディレクトリの一時ファイルを `mv` する方式です。エディタのパスが空・相対パスの場合はそのエディタをスキップします。
- keybindings.json、tasks.json、snippets は従来どおり symlink で同期します。
- `status` は settings.json を合成結果との意味的な比較で判定します。
- `dump` は settings.json をスキップします。合成結果でプロファイルを上書きしないためです。エディタで編集した内容は `mise run settings-diff` で確認し、`mise run pull` で該当する層に書き戻してください。

## External Variables

各種ターゲットを実行する際に `mise run <task> -- --prof=<profile-name>` のようにプロファイルを指定できます。
コマンドからプロファイルを指定することで、特定のプロファイルに対して操作を行うことができます。
引数を省略した場合は、デフォルトのプロファイルが使用されます。デフォルトのプロファイルは `.env` ファイルの `DEFAULT_PROFILE` で指定されています。
