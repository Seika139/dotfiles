# Windows のパッケージマネージャー

1. **Windows Package Manager (winget)**:

   - Microsoft が提供する公式のパッケージマネージャーです。コマンドラインツールであり、ソフトウェアの検索、インストール、アップデート、アンインストールが可能です。
   - 例: `winget install <パッケージ名>`

2. **Chocolatey**:

   - Windows 向けのパッケージマネージャーで、非常に多くのパッケージが利用可能です。PowerShell を利用して操作します。
   - 例: `choco install <パッケージ名>`

3. **Scoop**:
   - シンプルで軽量なパッケージマネージャーです。主に開発者向けのツールやユーティリティのインストールに適しています。
   - 例: `scoop install <パッケージ名>`

## 参考

- [Windows セットアップメモ](https://zenn.dev/masinc/scraps/58fbceb57ebac7)
- [パッケージ管理システムのすすめ｜ woinary](https://note.com/woinary/n/n2b4ef236f2ba)

## インストールする

最初は Microsoft 公式の winget を試そうとしたが、それ自体のインストールが大変でうまくいかなかったので断念した。
代わりに scoop を入れる。

[ScoopInstaller/Scoop: A command-line installer for Windows.](https://github.com/ScoopInstaller/Scoop)

このページの Installation の項目を PowerShell で実行する。
管理者モードで実行すると失敗するので、普通のモードで実行する。

### GitBash から PowerShell を起動する

```bash
powershell # ターミナルが powershell になる
powershell -Command "some command" # powershell を通してコマンドを実行する
```

## scoop のコマンドを一部紹介

```bash
scoop install [app] # インストールする
scoop list # インストールしたものの一覧を表示する
scoop uninstall [app] # アンインストールする
scoop update # アプリやscoopをアップデートする
```
