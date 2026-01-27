# git diff

```bash
git diff [before]..[after]
```

afterで追加された部分が + で表され、before から消えた部分が - で表される。
`..` は ` `（空白）でも同じ。
片方を省略すると HEAD との差分を比較する。

```bash
git diff                     # 作業ディレクトリとステージングエリアの差分
git diff --cached / --staged # ステージングエリアとHEADの差分。つまり次にコミットされうる内容
git diff A...B               # ドットが3つの時は A と B の共通の祖先と B との差分を比較する
```

## オプション

|   `-- [path]`   | 対象ファイルの変更のみを表示する                                              |
| :-------------: | :---------------------------------------------------------------------------- |
|    `--stat`     | 変更量をファイル単位で確認                                                    |
|  `--stat=[n]`   | 表示するファイル名を n 文字までにする。長い場合は省略する。デフォルトは80文字 |
| `--color-words` | 行単位ではなく、単語単位で差分を表示する                                      |
|      `-w`       | 改行コードや空白を無視                                                        |
|  `--no-index`   | git管理対象外のファイルも含める                                               |
|     `-U[n]`     | 変更の前後 n 行を表示する。0にすると表示されない                              |

## diff-filter

```bash
git diff --diff-filter=[フィルター]
git diff --diff-filter=AM # 作成または編集された差分のみを表示
```

- フィルターに指定する文字: `A`, `C`, `D`, `M`, `R`

Add, Copied, Deleted, Modified, Renamed などの差分の種類でフィルタをかけられる。
大文字の場合はその種類だけで絞り込む。
小文字の場合はその種類を除外する。
詳細は man git-diffを参照。

**参考**

- <https://qiita.com/rana_kualu/items/09d2dd379019b8ef0335>
- <https://git.command-ref.com/cmd-git-diff.html>
- <https://qiita.com/shibukk/items/8c9362a5bd399b9c56be>
- <https://qiita.com/yuya_presto/items/ef199e08021dea777715#2-1>

## 自作 git 拡張コマンド

```bash
gdd author commit1 commit2 [option]
```

commit1 と commit2 の間で author が作成した差分を一覧表示する
author を `-` にすると author で絞り込まない
option は git diff に用いられるものが使えるが、「commit1 と commit2 の間で author が作成した差分」を渡している以上、ファイルの絞り込みはできない。
