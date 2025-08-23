# Mise - Tasks

mise の機能のうち、タスクに関する内容をまとめます。

- 詳細は公式ドキュメントを参照: <https://mise.jdx.dev/tasks/>

`mise.toml` の `[tasks]` セクションを使用して、プロジェクト固有のタスクを定義できます。

```toml
[tasks]
build = "npm run build"
test = "npm test"
```

**目次**

- [Mise - Tasks](#mise---tasks)
  - [タスクの依存関係](#タスクの依存関係)
    - [depends](#depends)
    - [depends_post](#depends_post)
    - [wait_for](#wait_for)
  - [変数と環境変数](#変数と環境変数)
    - [デフォルトの環境変数](#デフォルトの環境変数)
    - [env](#env)
      - [Tips: 環境変数の書き方](#tips-環境変数の書き方)
        - [`$some` の書き方に軍配が上がる場合](#some-の書き方に軍配が上がる場合)
          - [シェルの機能と組み合わせたいとき](#シェルの機能と組み合わせたいとき)
          - [複雑なコマンドの中で自然に使える](#複雑なコマンドの中で自然に使える)
    - [vars](#vars)
  - [引数](#引数)
    - [positions argument](#positions-argument)
    - [option](#option)
    - [flag](#flag)
  - [その他のオプション](#その他のオプション)
    - [run_windows](#run_windows)
    - [description](#description)
    - [confirm](#confirm)
    - [quiet](#quiet)
    - [silent](#silent)

## タスクの依存関係

mise はタスク同士を依存させて実行順序や並列性を管理します。
すべてのタスクとその依存関係の有向非巡回グラフ (DAG) を作成することで以下のことを保証します。

- タスクの実行順序
- 独立したタスクの並列実行
- 循環した依存関係がないこと
- 失敗した依存関係によってタスクを中止すること

### depends

test は lint と build に成功しないと実行されません。

```toml
[tasks.test]
depends = ["lint", "build"]
run = "npm test"
```

### depends_post

cleanup, notify は deploy の後に実行されます。（deploy の成功、失敗に関わらず）

```toml
[tasks.deploy]
depends = ["build", "test"]
depends_post = ["cleanup", "notify"]
run = "kubectl apply -f deployment.yaml"
```

### wait_for

ソフトな依存関係を定義します。
wait_for で指定されたタスクが実行中の場合にのみ、タスクが実行を待機します。

```toml
[tasks.integration-test]
wait_for = ["start-services"]  # Only waits if start-services is also being run
run = "npm run test:integration"
```

**実行シナリオ:**

- `mise run integration-test` を実行した場合: `start-services` は実行対象ではないため、`integration-test` は何も待たずにすぐに開始されます。
- `mise run start-services integration-test` を実行した場合: `start-services` が実行対象に含まれているため、`integration-test` は `start-services` が完了するのを待ってから開始されます。

このように、`wait_for` は複数のタスクを同時に実行する際の順序を制御したい場合に便利です。

## 変数と環境変数

### デフォルトの環境変数

mise でタスクを実行するときに自動的に設定される環境変数があります。これらは、タスクの実行環境を制御するために使用できます。

```yml
MISE_ORIGINAL_CWD: タスクが実行された元の作業ディレクトリ。
MISE_CONFIG_ROOT: タスクが定義された mise.toml ファイルを含むディレクトリ。もし構成パスが ~/src/myproj/.config/mise.toml のような場合は ~/src/myproj になります。
MISE_PROJECT_ROOT: プロジェクトのルート。
MISE_TASK_NAME: 実行中のタスクの名前。
MISE_TASK_DIR: タスクスクリプトが含まれるディレクトリ。
MISE_TASK_FILE: タスクスクリプトへのフルパス。
```

### env

- Type: `{ [key]: string | int | bool }`

タスクに環境変数を設定します。これで設定した環境変数はタスクの実行時にのみ有効で、他のタスクには影響しません。

```toml
[env]
TEST_ENV_VAR = "ABC"

[tasks.test]
run = [
    "echo $TEST_ENV_VAR",
    "mise run some-other-task", # running tasks like this _will_ have TEST_ENV_VAR set of course
]
```

#### Tips: 環境変数の書き方

`{{env.SOME}}` と `$some` の両方が利用できますが、以下のような違いがあります。

- `{{env.SOME}}`
  - mise の独自のテンプレート構文を利用した書き方で、タスクのコマンドが実行される前に展開されます。
  - つまり、コマンドが実行される前に変数の値が決定されます。
  - シェルの種類に依存しないメリットがあります。
- `$some`
  - シェルの環境変数として解釈されます。
  - つまり、コマンドが実行されるときにシェルが変数を展開します。
  - シェルの種類（bash, zsh, sh, fish など）に依存する可能性があります。

実際に [mise.toml](./mise.toml) のタスクで試してみると、一目瞭然です。

```bash
mise run test_env
```

を実行してみてください。

##### `$some` の書き方に軍配が上がる場合

###### シェルの機能と組み合わせたいとき

```toml
[tasks.default]
run = "echo ${SOME:-default_value}"
```

- `${SOME:-...}` のようなシェルのデフォルト値展開
- `${SOME%foo}` のようなパラメータ展開（文字列加工）
- こうした表現は `{{env.SOME}}` では書けません。

###### 複雑なコマンドの中で自然に使える

```toml
[tasks.compose]
run = "docker compose -f compose.$SOME.yml up"
```

`compose.dev.yml` / `compose.prod.yml` の切り替えみたいに、そのままシェルコマンドで変数展開させた方がシンプル。

### vars

環境変数のようにタスク間で共有できる変数として `vars` を利用します。
vars はスクリプトに環境変数として渡されることはありません。 `mise.toml` の `vars` のセクションで定義して、以下のように利用します。

```toml
[vars]
e2e_args = '--headless'

[tasks.test]
run = './scripts/test-e2e.sh {{vars.e2e_args}}'
```

## 引数

タスク実行時に引数を渡す方法についてまとめます。

まずデフォルトでは引数はコマンドの末尾に追加されます。
配列でタスクが定義されている場合は、最後の要素の末尾に追加されます。

以下の例で `mise run test foo bar` を実行すると、`./scripts/test.sh foo bar` が実行されます。
`cargo test` には `foo` と `bar` は渡されません。

```toml
[tasks.test]
run = ['cargo test', './scripts/test-e2e.sh']
```

### positions argument

`{{arg()}}` を使用して、位置引数を参照します。
これを定義した場合は、実行時にその数だけ引数を渡す必要があります。

以下の例では、`mise run test` を実行するには、2 つの引数を渡す必要があります。
`mise run test2` では 2 番目の引数は省略可能で、デフォルト値 `file2.txt` が使用されます。

- `name=""` はヘルプやエラーメッセージで引数の名前を表示するために使用します。

※ それぞれ正しく `"` で囲まないと mise がクラッシュすることがあるので注意してください。
※ ドキュメントには `i` と `var` という要素も説明されているがいまいち使い方がわからない。

```toml
[tasks.test]
run = 'echo {{arg(name="file1")}} {{arg(name="file2")}}'

[tasks.test2]
run = 'echo {{arg(name="file1")}} {{arg(name="file2", default="file2.txt")}}'
```

### option

`{{option()}}` を利用して、任意引数を定義できます。

以下の場合は、`mise run test3 --file file1.txt` として実行すると、`file1.txt` が `{{option(name="file")}}` に渡されます。

```toml
[tasks.test3]
run = 'echo {{option(name="file")}}'
```

### flag

`{{flag()}}` を利用して、フラグ引数（値を必要としない引数）を定義します。

以下の場合は、`mise run echo --myflag` として実行すると `true` が出力され、
`--myflag` をつけない場合は `false` が出力されます。

```toml
[tasks.echo]
run = 'echo {{flag(name="myflag")}}'
```

以下の場合は `mise run maybeClean --clean` として実行すると、`{{flag(name="clean")}}` が `true` になります。

```toml
[tasks.maybeClean]
run = """
if [ "{{flag(name=\"clean\")}}" = "true" ]; then
  echo 'cleaning'
fi
"""
```

## その他のオプション

タスクにオプションを設定して、挙動を制御できます。
よく使いそうなのだけ記載しておきます。

### run_windows

Windows 環境で mise run を実行した場合に、代わりのコマンドを指定できます。

```toml
[tasks.ls]
run = "ls -la"
run_windows = "dir"
```

### description

- Type: `string`

`mise run` をタスク指定なしで実行した場合や、 `mise tasks` でタスクの一覧を表示した場合に、各タスクの説明として表示されます。

```toml
[tasks.build]
description = "Build the CLI"
run = "cargo build"
```

### confirm

- Type: `string`

タスク実行前に表示されるメッセージです。
破壊的なタスクや実行に時間のかかるタスクに便利です。タスク実行前にユーザーに確認を求めます。

```toml
[tasks.release]
confirm = "Are you sure you want to cut a release?"
description = 'Cut a new release'
file = 'scripts/release.sh'
```

### quiet

- Type: `bool`
- Default: `false`

タスクにおける mise の実行されたコマンドなどの出力を抑制します。

- 例：`[build] $ cargo build`

これを設定すると、mise はスクリプト自体の出力以外の出力を表示しません。
タスク自体の出力も非表示にしたい場合は silent を使用します。

### silent

- Type: `bool | "stdout" | "stderr"`
- Default: `false`

タスクからのすべての出力を抑制します。"stdout"または"stderr"に設定すると、そのストリームのみが抑制されます。
