# dust コマンド

`dust` は、ディレクトリやファイルの容量をツリーと割合バーで表示する `du` の代替コマンドです。容量の大きな項目をたどって確認できます。

## インストール

```bash
# Linux（Cargo）
cargo install du-dust
```

```bash
# macOS（Homebrew）
brew install dust
```

```powershell
# Windows（Scoop）
scoop install dust
```

## Syntax

```bash
dust [OPTIONS] [PATH]...
```

パスを省略するとカレントディレクトリを集計します。

## よく使うオプション

- `-d N`, `--depth N` はツリーに表示する階層の深さを指定する。
- `-n N`, `--number-of-lines N` は表示する大きな項目の数を指定する。ツリーの親項目や合計行などが加わることがある。
- `-D`, `--only-dir` はディレクトリを表示する。
- `-F`, `--only-file` はファイルに絞って表示する。
- `-X NAME`, `--ignore-directory NAME` は指定した名前のファイルやディレクトリを集計対象から除外する。
- `-x`, `--limit-filesystem` は指定したパスと同じファイルシステム内を集計する。
- `-s`, `--apparent-size` はファイルの見かけ上のサイズを集計する。
- `-p`, `--full-paths` はサブディレクトリのパスを短縮せずに表示する。

## 使用例

```bash
# カレントディレクトリの容量をツリー表示する
dust

# 2階層まで表示する
dust -d 2 .

# 容量の大きな項目を中心に表示する
dust -n 20 .

# ファイルに絞って大きな項目を確認する
dust -F .

# node_modules を集計対象から外す
dust -X node_modules .
```

`du` については [`du.md`](./du.md) を参照してください。容量の大きなファイルやディレクトリを探す例は [`find_large_directory.md`](./find_large_directory.md) にもあります。

## OS ごとの違い

`dust` の基本オプションは Linux、macOS、Windows で共通です。dust 1.2.7 の既定では、Linux と macOS は割り当てブロックを基準に容量を集計し、Windows は通常ファイルの長さを容量として扱います。Windows 版はハードリンクを複数回集計することがあります。

```powershell
# Windows PowerShell
dust -d 1 "$env:USERPROFILE\Downloads"
```

```bash
# Linux または macOS
dust -d 1 ~/Downloads
```

## 参考資料

- [`dust` の公式 README](https://github.com/bootandy/dust#usage)
- [dust 1.2.7 の Linux/macOS 容量集計実装](https://github.com/bootandy/dust/blob/v1.2.7/src/platform.rs#L34-L65)
- [dust 1.2.7 の Windows 容量集計実装](https://github.com/bootandy/dust/blob/v1.2.7/src/platform.rs)
