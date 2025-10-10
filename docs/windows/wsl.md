# WSL

Windows Subsystem for Linux (WSL) を使用すると、Windows 上で Linux 環境を実行できます。
これにより、Linux 用のツールやアプリケーションをネイティブに実行できるようになります。

WSL を介することで Ubuntu on Windows をはじめとする様々な Linux ディストリビューションを Windows 上で実行できる。

WSL では Windows カーネルが Linux のシステムコールをエミュレートして実行する方式だったため、一部の機能が制限されていたが、その後に登場した WSL2 では軽量な仮想マシン上で実際に Linux カーネルを使用する方式に変更され、より高い互換性とパフォーマンスが実現されている。

そのため、現在は WSL2 を使用することが推奨されている。

## WSL のバージョン確認方法

```bash
$ wsl -l -v
  NAME              STATE           VERSION
* Ubuntu-24.04      Running         2
  docker-desktop    Running         2
```

## Ubuntu on Windows (WSL2) のインストール

winget で Ubuntu をインストールする。

```bash
$ winget search ubuntu
名前               ID                          バージョン  一致            ソース
----------------------------------------------------------------------------------
Ubuntu             9PDXGNCFSCZV                Unknown                     msstore
Ubuntu 24.04.1 LTS 9NZ3KLHXDJP5                Unknown                     msstore
Ubuntu 22.04.5 LTS 9PN20MSR04DW                Unknown                     msstore
Ubuntu 20.04.6 LTS 9MTTCL66CPXJ                Unknown                     msstore
Ubuntu 18.04.6 LTS 9PNKSF5ZN4SW                Unknown                     msstore
Ubuntu (Preview)   9P7BDVKVNXZ6                Unknown                     msstore
Ubuntu             Canonical.Ubuntu            2204.1.8.0                  winget
Ubuntu 18.04 LTS   Canonical.Ubuntu.1804       1804.6.4.0  Command: ubuntu winget
Ubuntu 20.04 LTS   Canonical.Ubuntu.2004       2004.6.16.0 Command: ubuntu winget
Ubuntu 22.04 LTS   Canonical.Ubuntu.2204       2204.2.47.0 Command: ubuntu winget
Ubuntu 24.04 LTS   Canonical.Ubuntu.2404       2404.0.5.0  Command: ubuntu winget
YTDownloader       aandrew-me.ytDownloader     3.19.3      Tag: ubuntu     winget
alarm-cron         bl00mber.alarm-cron         0.1.1       Tag: ubuntu     winget
SODA for SPARC     fairdataihub.SODA-for-SPARC 16.2.1      Tag: ubuntu     winget
```

ソースが winget となっていて、IDが Canonical.Ubuntu.2404 となっているものを選ぶ。

```bash
winget install -e --id Canonical.Ubuntu.2404
```

Ubuntu を起動する。Windowsのスタートメニューから "Ubuntu 24.04 LTS" を選ぶか、以下のコマンドを実行する。

```bash
ubuntu2404.exe
```

初回起動時はユーザー名とパスワードの設定が求められる。
適当な名前とパスワードを設定する。
今回はユーザー名を `ken` とした。
パスワードはいつものにした。

```bash
$ ubuntu2404.exe
Installing, this may take a few minutes...
Please create a default UNIX user account. The username does not need to match your Windows username.
For more information visit: https://aka.ms/wslusers
Enter new UNIX username: ken
New password:
Retype new password:
passwd: password updated successfully
Installation successful!
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

Welcome to Ubuntu 24.04 LTS (GNU/Linux 5.15.167.4-microsoft-standard-WSL2 x86_64)
```

これで Ubuntu on Windows (WSL2) が使えるようになった。

```bash
$ wsl -l -v
  NAME              STATE           VERSION
* docker-desktop    Running         2
  Ubuntu-24.04      Running         2
```

また、単に `wsl` と実行することでも起動できる。

```bash
$ wsl
ken@CG15034:~$
```
