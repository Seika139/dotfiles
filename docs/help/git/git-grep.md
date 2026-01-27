# git grep

## grep に対する git grep のメリット

1. リポジトリ内のみを検索するため、Linuxのgrepコマンドよりも検索速度が速い。
2. リポジトリ内で追跡しているファイルのみを対象に検索ができる。キャッシュなどの不要なファイルを検索しなくて済む。
3. 過去の時点のファイルの状態を検索できる。

## 基本

```bash
git grep [option] [検索条件] [tree]
```

tree(コミットIDやブランチ名)の時点でファイル内の該当する文字列を検索する。
treeを指定しない場合はHEADの状態を検索する。

※ grep の使い方は git grep と大体同じ。詳しくは [grep.md](../linux/grep.md) を参照。検索条件での正規表現についてもこっちに記述する。

## オプション

```bash
-i / --ignore-case            # 大文字と小文字の違いを無視する
-l                            # 検索条件を満たすファイル名のみを表示する
-c                            # 検索条件を満たすファイル名と一致した件数を表示する
--break                       # 検索結果をファイル毎に空行を入れて見やすく表示する
```

### `-n` 行番号を表示

`git config --global grep.lineNumber true` で `.gitconfig` に設定できる。

```bash
git grep -n
git grep --line-number
```

### `--column`

検索条件に一致する行の先頭から「最初に検索条件に一致する箇所の1始まりのバイトオフセット」を表示する。
`git config grep.column true` で `.gitconfig` に設定できる。

### 前後の行を表示

```bash
-n / -C n / --context n   # 検索結果の前後 n 行を表示
-A n / --after-context n  # 検索結果の後 n 行を表示
-B n / --before-context n # 検索結果の前 n 行を表示
```

### 絞り込み

```bash
-- [path]   # path 内のディレクトリを検索する
-- [:!path] # path 内のディレクトリを以外を検索する。[:^path] でも良い
-W / --function-context # 関数名を含む前の行から次の関数名の前の行までのテキストを表示する。YAMLやテキストファイルでは微妙な使い味
-G / --basic-regexp # 検索条件に基本正規表現(BRE)を使用する。デフォルトはこれ。
-F / --fixed-strings # 検索条件を正規表現ではなく、固定文字列として解釈する。
-E / --extended-regexp # 検索条件に拡張正規表現(ERE)を使用する。ただし `.*?` が左方最短一致ではなく最長一致にしかならない。詳細は hlp_grep を参照。
```

### tree と同時に指定できないオプション

```bash
--no-index  # git管理対象外のファイルも含める
--cached    # ステージングエリアから検索する。
--untracked # ワークツリーで追跡されたファイルを検索するだけでなく、追跡されていないファイルも検索する。
```

## 複数条件

`--and` / `--or` / `--not` :`-e 検索条件1 --and -e 検索条件2` のようにして指定する。 `--or` は省略できる。

**参考**

- <https://www.r-staffing.co.jp/engineer/entry/20200605_1>
- <https://tracpath.com/docs/git-grep/> ← <https://git-scm.com/docs/git-grep> の和訳
- <https://dev.classmethod.jp/articles/useful-git-grep-command/>
- <https://future-architect.github.io/articles/20200611/>
