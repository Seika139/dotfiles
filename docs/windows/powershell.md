# PowerShell

## PowerShell 7 のインストール

もともと入ってた PowerShell を起動すると以下のように最新のものを使えと言われるので、winget で PowerShell 7 をインストールした。

```powershell
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

新機能と改善のために最新の PowerShell をインストールしてください!https://aka.ms/PSWindows

PS C:\WINDOWS\system32>
```

```bash
winget search Microsoft.PowerShell
winget install --id Microsoft.PowerShell --source winget
```

### パスを通す

`bash\private\02_path.bash` に以下を追加した。

```bash
add_path '/c/Program Files/PowerShell/7'
```

これで `pwsh` コマンドで PowerShell 7 が起動できるようになる。

```bash
$ pwsh
PowerShell 7.5.2
PS C:\Users\S13316\dotfiles>
```
