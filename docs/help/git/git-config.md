# git config

## 設定の種類と場所

Gitの設定ファイルは `system`, `global`, `local` の3種類ある。
git config コマンドで指定する場合はそれぞれ `--system`, `--global`, `--local` とする。

|  種類  |                 対象範囲                 |         場所の例         | 備考                     |
| :----: | :--------------------------------------: | :----------------------: | :----------------------- |
| system | システム全体（全ユーザーの全リポジトリ） |     `/etc/gitconfig`     | -                        |
| global |        該当ユーザーの全リポジトリ        |      `~/.gitconfig`      | ホーム直下               |
| local  |              該当リポジトリ              | `repository/.git/config` | 各リポジトリの .git 直下 |

参考 : <https://note.nkmk.me/git-config-setting/>

## 設定の確認

```bash
git config <設定項目名>
git config -l/--list  一覧表示
```

`--system`, `--global`, `--local` をつけない場合は、コマンドを実行したディレクトリで有効になっている設定が表示される。

## 設定の変更

```bash
git config <設定項目名> <設定する値>
```

デフォルト（オプションなし）では local の設定が変更される。
Gitリポジトリの外側でオプションなしで実行するとエラーとなる。
global や system の設定を変更したい場合はオプションを付ける。

## 設定の編集

`git config -e` をするとエディタ (vim) で編集できる。
もちろん `.gitconfig` を直接編集しても反映される。
