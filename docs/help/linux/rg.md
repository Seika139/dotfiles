# rg (ripgrep) コマンド

Rust で書かれた高速な検索ツールで、 grep コマンドの上位互換として使用されます。

## Syntax

```bash
rg [OPTIONS] PATTERN [PATH...]
```

rg コマンドは PATH 以下のディレクトリを再帰的に検索し、ファイル内の検索条件にマッチする行を表示します。
PATH を指定しない場合はカレントディレクトリが検索対象になります。

## オプション

### SEARCH OPTIONS

|       オプション        | 説明                                                                                      |
| :---------------------: | :---------------------------------------------------------------------------------------- |
|  `-i`, `--ignore-case`  | 大文字と小文字の違いを無視（デフォルトでは区別する）                                      |
| `-F`, `--fixed-strings` | 検索条件を正規表現ではなく、固定文字列として解釈する                                      |
|  `-w`, `--word-regexp`  | 単語単位でマッチ（例: `rg -w "cat"` は cat にマッチするが concat にはマッチしない）       |
| `-v`, `--invert-match`  | マッチしない行を表示する（例: `rg -v "cat"` は cat を含まない行を表示）                   |
|  `-m`, `--max-count=N`  | マッチした行を最大 N 行まで表示する（例: `rg -m 5 "cat"` は cat を含む最初の 5 行を表示） |
|   `-U`, `--multiline`   | 1 つのマッチが複数行にまたがることを許可する（既定では 1 行単位でしかマッチしない）       |
|  `--multiline-dotall`   | `--multiline` 有効時に `.` を `\n` にもマッチさせる（PCRE の dotall / `(?s)` 相当）       |

### FILTER OPTIONS

|       オプション       | 説明                                                                                   |
| :--------------------: | :------------------------------------------------------------------------------------- |
|    `-L`, `--follow`    | シンボリックリンクをたどる（デフォルトではたどらない）                                 |
|     `-g`, `--glob`     | glob パターンでフィルタ（例: `rg -g "*.{txt,md}"`: .txt または .md のみを検索）        |
|     `-t`, `--type`     | ファイルタイプ（例: `rg -t js` : JavaScript ファイルのみを検索）                       |
|   `-T`, `--type-not`   | ファイルタイプで除外（例: `rg -T js` は JavaScript ファイルを検索対象から除外）        |
|    `-.`, `--hidden`    | 隠しファイルも検索対象に含める（デフォルトでは除外）                                   |
|     `--no-ignore`      | .gitignore に記載されたファイルも検索対象に含める（デフォルトでは除外）                |
| `-u`, `--unrestricted` | 隠しファイルや .gitignore に記載されたファイルも検索対象に含める（デフォルトでは除外） |

※ `-t` で指定できるファイルタイプは `rg --type-list` で確認できます。

#### glob パターンの例

- `-g "*.{js.ts}"` … 拡張子が .js または .ts のファイル
- `--iglob "*test*"` … ファイル名に test や Test を含むファイル
- `-g "**/game/**/*.py"` … 任意の階層の game ディレクトリ以下の .py ファイル
- `-g "**/game/*.py"` … 任意の階層の game ディレクトリ直下の .py ファイル
- `-g "/.*"` … この階層のドットファイル

### OUTPUT OPTIONS

|         オプション         | 説明                              |
| :------------------------: | :-------------------------------- |
|   `-n`, `--line-number`    | 行番号を表示する                  |
| `-A`, `--after-context=N`  | マッチした行の後 N 行も表示する   |
| `-B`, `--before-context=N` | マッチした行の前 N 行も表示する   |
|    `-C`, `--context=N`     | マッチした行の前後 N 行も表示する |

### OUTPUT MODE

|          オプション          | 説明                                       |
| :--------------------------: | :----------------------------------------- |
|           `--json`           | 検索結果を JSON 形式で出力                 |
|       `-c`, `--count`        | マッチした行数を表示する                   |
| `-l`, `--files-with-matches` | マッチした行があるファイル名のみを表示する |
|   `--files-without-match`    | マッチした行がないファイル名のみを表示する |

## 複数のキーワードを含むファイルを検索する方法

rg は 1 回の呼び出しでは原則 1 つのパターンしか取れないため、AND 検索（複数キーワードをすべて含む）を行うには工夫が必要です。
状況に応じて次の方法を使い分けます。

### 1. ファイル単位で AND したい — パイプで `-l` を連結

最も単純で高速。各段階が線形時間で済むため、巨大リポジトリでも安心して使えます。

```bash
# TODO と FIXME の両方を含むファイル名を列挙
rg -l TODO | xargs rg -l FIXME

# 3 つ以上でも段数を増やすだけ
rg -l TODO | xargs rg -l FIXME | xargs rg -l WIP
```

`-l` (`--files-with-matches`) は「マッチがあったファイル名だけ」を返すので、後段の `rg` への入力として使い回せます。

### 2. 同一行内で AND したい — `regex_and` で順不同正規表現を生成

`~/dotfiles/bash/public/11_alias.bash` に定義された `regex_and` 関数を使うと、引数の全順列を `|` で OR した正規表現が得られます。

```bash
regex_and TODO FIXME
# -> TODO.*FIXME|FIXME.*TODO

# Markdown ファイルで TODO と FIXME が同じ行にある箇所を検索
rg -t md "$(regex_and TODO FIXME)" bash/
```

引数の順序を問わずにマッチさせたい場合に有効。引数 N 個に対し N! 通りの順列を展開するため、`regex_and` 側で 6 個までに制限されています。
それ以上は方法 1 のパイプ連結に切り替えます。

### 3. 行をまたいで AND したい — `-U` + dotall

`regex_and` の出力は `.*` を含むため、既定では同一行内しかマッチしません。
複数行にまたがる AND を行うには `-U` でマッチ範囲を行単位からファイル全体に拡張し、さらに `.` を `\n` にマッチさせる必要があります。

```bash
# --multiline-dotall でフラグとして指定
rg -U --multiline-dotall "$(regex_and TODO FIXME)" path/

# (?s) インラインフラグでも等価
rg -U "(?s)$(regex_and TODO FIXME)" path/
```

`-U` だけでは `.` は依然として改行にマッチしないため、両方が必要です。
`.` の暴走（ファイル全体を貪欲に飲み込む）を防ぎたい場合は、文字クラス `[\s\S]` で距離を制限する書き換えが有効です。

```bash
# TODO と FIXME が 500 文字以内の距離で共起する箇所だけ
rg -U "$(regex_and TODO FIXME | sed 's/\.\*/[\\s\\S]{0,500}/g')" path/
```

### 4. OR 検索 — `regex_or` または `-e` の繰り返し

複数キーワードのいずれかを含む行を探したい場合は OR 検索です。

```bash
# regex_or は IFS='|' で連結するだけのシンプルな実装
rg "$(regex_or TODO FIXME WIP)"
# -> rg "TODO|FIXME|WIP" と等価

# rg 標準の -e オプションを複数指定する書き方も可
rg -e TODO -e FIXME -e WIP
```

### 5. A を含み B を含まない検索

同じ行の中で「A は含むが B は含まない」箇所を探すだけなら、まず A で検索してから `-v` で B を含む行を除外します。

```bash
# TODO を含み、DEBUG を含まない行を表示
rg TODO path/ | rg -v DEBUG
```

ファイル単位で「A を含むファイルのうち、B を含まないファイル」を列挙したい場合は、A にマッチしたファイル一覧を後段の `rg --files-without-match` に渡します。

```bash
# TODO を含み、DEBUG を含まないファイル名を列挙
rg -l TODO path/ | xargs rg --files-without-match DEBUG

# パスに空白などが含まれる可能性がある場合
rg -l -0 TODO path/ | xargs -0 rg --files-without-match DEBUG
```

`rg -v B` は「B を含まない行」を表示するオプションです。
ファイル単位で B を含まないことを確認したい場合は、`rg --files-without-match B` を使います。

### 使い分けの指針

|             やりたいこと             | 推奨                                           |
| :----------------------------------: | :--------------------------------------------- |
|    ファイル単位で AND（順序不問）    | `rg -l A \| xargs rg -l B`                     |
|      同一行内で AND（順序不問）      | `rg "$(regex_and A B)"`                        |
|           行をまたいで AND           | `rg -U --multiline-dotall "$(regex_and A B)"`  |
|               OR 検索                | `rg "$(regex_or A B C)"` / `rg -e A -e B -e C` |
| 同一行内で A を含み B を含まない検索 | `rg A \| rg -v B`                              |
| ファイル単位で A を含み B を含まない | `rg -l A \| xargs rg --files-without-match B`  |

## インストール方法

**macOS**

```bash
brew install ripgrep
```

**Debian/Ubuntu**

```bash
sudo apt install ripgrep
```
