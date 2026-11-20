# du コマンド

GNU/Linux の `du` は、指定したファイルやディレクトリが使用しているディスク容量を表示するコマンドです。ディレクトリを指定すると、その中のファイルやサブディレクトリも再帰的に集計します。

## Syntax

```bash
du [OPTIONS] [FILE or DIRECTORY]...
```

## よく使うオプション

以下の長いオプション名は GNU Coreutils で使われる表記です。

- `-h`, `--human-readable` はサイズを読みやすい単位で表示する。
- `-s`, `--summarize` は指定したパスごとの合計を表示する。
- `-a`, `--all` はファイルとディレクトリのサイズを表示する。
- `-d N`, `--max-depth=N` は指定した深さまでの集計結果を表示する。表示を省いた深い階層も、親ディレクトリの合計には含まれる。
- `-x`, `--one-file-system` は別のファイルシステムにあるディレクトリを集計対象から除外する。
- `--apparent-size` はファイルの見かけ上のサイズを表示する。GNU Coreutils 9.10 以降では `-A` も使える。

## 使用例

```bash
# ディレクトリ全体の合計サイズを表示する
du -sh ~/Downloads

# 直下のディレクトリとカレントディレクトリの合計を大きい順に表示する
du -h -d 1 . | sort -hr

# ファイルとディレクトリを合わせて、大きい項目を上位10件表示する
du -ah . | sort -hr | head -n 10

# 別のファイルシステムに入らずに容量を集計する
du -xh -d 1 /

# GNU/Linux でファイルの見かけ上のサイズを表示する
du -sh --apparent-size .
```

`-a` を使った結果には、ディレクトリの合計とその中のファイルのサイズが表示されます。起点に指定した `.` の合計も含まれるため、上位10件に表示されることがあります。容量の大きなファイルやディレクトリを探す例は [`find_large_directory.md`](./find_large_directory.md) も参照してください。

`dust` については [`dust.md`](./dust.md) を参照してください。

## OS ごとの違い

macOS に付属する `du` は BSD 系です。GNU/Linux と同じ `-d N` で深さを指定でき、見かけ上のサイズには `-A` を使います。GNU/Linux では `--apparent-size` を使います。macOS では `--max-depth` や `--apparent-size` のような GNU の長いオプション名は使えません。また、`-a` と `-d` は同時に指定できません。ブロック単位の既定値は GNU/Linux が通常1024バイト、macOS は `BLOCKSIZE` 未設定時に512バイトです。単位をそろえて並べ替えるときは、両方で使える `-k` を指定できます。

```bash
# Linux と macOS で共通の短いオプションを使い、直下のディレクトリを大きい順に表示する
du -k -d 1 . | sort -nr

# macOS で見かけ上のサイズを表示する
du -sh -A .
```

Windows では Git Bash に付属する GNU `du` や WSL の Linux `du` を使えます。Microsoft Sysinternals の `du.exe` も利用できますが別のコマンドで、サブディレクトリの深さは `-l N` で指定します。Sysinternals の実行ファイルを展開したディレクトリから起動するときは、相対パスを明示します。

```powershell
# PowerShell から WSL の du を実行する
wsl du -h -d 1 .

# 展開したディレクトリ内の Sysinternals du.exe を使う
.\du.exe -l 1 "$env:USERPROFILE\Downloads"
```

## 参考資料

- [GNU Coreutils の du マニュアル](https://www.gnu.org/software/coreutils/manual/html_node/du-invocation.html)
- [Apple の du マニュアル](https://github.com/apple-oss-distributions/file_cmds/blob/main/du/du.1)
- [Apple の du 実装](https://github.com/apple-oss-distributions/file_cmds/blob/main/du/du.c)
- [Microsoft Sysinternals の Disk Usage](https://learn.microsoft.com/en-us/sysinternals/downloads/du)
- [Microsoft の WSL ファイルシステムとコマンド相互運用](https://learn.microsoft.com/ja-jp/windows/wsl/filesystems)
