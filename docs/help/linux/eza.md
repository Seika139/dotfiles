# eza コマンド

Rust 製の ls コマンドの代替ツールです。ls よりも高速で、より多くの機能を提供します。

## Syntax

```bash
eza [OPTIONS] [PATH]
```

## Display Options

- `-l`, `--long` : 長い形式（詳細情報付き）で表示
- `-T`, `--tree` : ディレクトリ構造をツリー形式で表示
- `-R`, `--recursive` : ディレクトリを再帰的に表示
- `-L`, `--level N` : ツリー表示の深さを指定 (例: `-L 2` は 2 階層まで表示)

## Filtering and Sorting Options

- `-a`, `--all` : 隠しファイルも表示
- `--git-ignore` : .gitignore に記載されたファイルを表示から除外
- `-D`, `--only-dirs` : ディレクトリのみを表示
- `-F`, `--only-files` : ファイルのみを表示
- `--group-directories-first` : ディレクトリをファイルより先に表示
- `--group-directories-last` : ディレクトリをファイルより後に表示
- `-s`, `--sort` : ソート方法を指定
  - `name`, `extension`, `size`, `modified`, `changed`, `accessed`, `created`, `inode`, `type`, `none`.

**時刻の表示について**

- `modified` : ファイルの内容が最後に変更された日時
  - ファイルのサイズが変わったり、中身のバイナリデータが書き換わったりした時に更新されます
- `changed` : ファイルのメタデータが最後に変更された日時（内容の変更も含む）
  - chmod などでパーミッションを変更したとき
  - chown などで所有者やグループを変更したとき
  - ファイルの名前やディレクトリの位置を変更したとき
- `accessed` : ファイルが最後にアクセス（読み込まれたり、実行されたり）された日時
- `created` : ファイルが作成された日時

## LONG VIEW OPTIONS

`-l`, `--long` オプションを使用するときに、利用可能なオプションです。

- `-g`, `--group` : グループ名を表示
- `--git` : Git の状態を表示
- `-h`, `--header` : ヘッダー行を表示
- `--inode` : ファイルの inode 番号を表示
- `-o`, `--octal-permissions` : パーミッションを 8 進数で表示 (例: `755`)
- `--permissions` : ファイルのパーミッションを表示
- `--total-size` : ディレクトリの合計サイズを表示（重い処理になる可能性があります）
- `-t`, `--time=WORD` : 表示するタイムスタンプの種類を指定します。
  - `modified`, `changed`, `accessed`, `created`
  - `-u`, `--accessed` オプションを使用して、アクセス日時を表示することもできます。
  - `-U`, `--created` オプションを使用して、作成日時を表示することもできます。
- `--time-style=STYLE` : タイムスタンプのフォーマット方法を指定します。
  - `default`, `iso`, `long-iso`, `full-iso`, `relative`
  - またはカスタムスタイル `+<FORMAT>` (例: `+%Y-%m-%d %H:%M` => `2024-06-01 12:34`)

## インストール方法

**macOS**

```bash
brew install eza
```

**Debian/Ubuntu**

```bash
sudo apt install eza
```
