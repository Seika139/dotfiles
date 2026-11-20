# df コマンド

`df` は、ファイルシステムごとの容量と空き容量を表示するコマンドです。指定したパスが属するファイルシステムの統計を取得するため、ディレクトリ以下のファイルを再帰的に調べません。

## Syntax

```bash
df [OPTIONS] [FILE or DIRECTORY]...
```

パスを指定すると、そのパスが属するファイルシステムを表示します。パスを省略すると、マウントされているファイルシステムを表示します。

## よく使うオプション

- `-h` はサイズを読みやすい単位で表示する。
- `-k` はサイズを KiB 単位で表示する。
- `-i` は inode の使用数と空き数を確認する。
- `-l` はローカルのファイルシステムに絞る。

Linux では `-T` を付けると、ファイルシステムの種類を表示します。

## 出力の見方

GNU/Linux の出力例を示します。

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/example    100G   61G   34G  65% /
```

- `Filesystem` はデバイス名やファイルシステム名。
- `Size` はファイルシステムの合計容量。
- `Used` は使用中の容量。
- `Avail` はユーザーが利用できる空き容量。
- `Use%` は使用率。
- `Mounted on` はマウント先。

`Avail` は予約領域などの影響を受けるため、`Size` から `Used` を引いた値と一致しないことがあります。

## 使用例

```bash
# ホームディレクトリが属するファイルシステムの空き容量を確認する
df -h "$HOME"

# ルートファイルシステムの空き容量を確認する
df -h /

# 現在のディレクトリが属するファイルシステムの inode 使用状況を確認する
df -i .

# Linux でファイルシステムの種類も表示する
df -hT .
```

`df -h "$HOME"` はホームが属するファイルシステムの容量と空き容量を表示します。ディレクトリ自体と配下の合計を調べるときは [`du.md`](./du.md) を参照してください。

## OS ごとの違い

Linux と macOS では `df -h PATH` のように、調べたいパスが属するファイルシステムを確認できます。Linux の `-T` は種類の表示に使い、`-i` は inode の使用状況へ切り替えます。macOS 付属の `df` では `-T TYPE` が種類による絞り込み、`-Y` が種類の表示です。macOS では inode 使用数も既定で表示されます。

Windows の PowerShell では `Get-PSDrive -PSProvider FileSystem` でファイルシステムのドライブと空き容量を確認できます。WSL では `wsl df -h /` が Linux 側のファイルシステムを示し、Windows の C ドライブを確認するには `wsl df -h /mnt/c` を使います。

```powershell
# PowerShell で Windows のファイルシステムドライブを表示する
Get-PSDrive -PSProvider FileSystem

# WSL の Linux ファイルシステムと Windows の C ドライブを確認する
wsl df -h /
wsl df -h /mnt/c
```

## 参考資料

- [GNU Coreutils の df マニュアル](https://www.gnu.org/software/coreutils/manual/html_node/df-invocation.html)
- [Apple の df マニュアル](https://github.com/apple-oss-distributions/file_cmds/blob/main/df/df.1)
- [Microsoft の Get-PSDrive マニュアル](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-psdrive)
- [容量の大きい項目を探す手順](./reduce_disk_capacity_with_du_dust.md)
