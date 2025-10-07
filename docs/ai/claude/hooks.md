# Hooks

Claude の実行に際して hook を設定することで、AI の応答が完了した際に通知を受け取ったり、他のアプリケーションを起動したりできます。
例えば、コードを生成した後に自動で整形したり、Slack に通知を送ったりすることが可能です。

個人的には、Claude の応答が完了した際に Windows の通知を表示し、Slack に通知を送るように設定しています。
これによって長時間の処理が完了したときに気づくことが可能になり、処理を待つ間に他の作業に集中できます。

- <https://docs.claude.com/ja/docs/claude-code/hooks>

## 設定方法

`~/.claude/settings.json` に以下のような設定を追加します。

```json
{
  "hooks": {
    "onComplete": [
      {
        "type": "command",
        "command": "pwsh -c \"New-BurntToastNotification -Text 'Claude finished', (Get-Date).ToString('HH:mm:ss')\""
      },
      {
        "type": "command",
        "command": "curl https://hooks.slack.com/triggers/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"
      }
    ]
  }
}
```

2025 年 10 月現在では `type` に指定できるのは `command` のみです。
`command` には実行したいコマンドを指定します。

## 通知を出す方法（Mac）

brew で Mac OS の通知を出すためのツールをインストールします。

```bash
brew install terminal-notifier
```

```json
{
  "type": "command",
  "command": "terminal-notifier -title '🦄 Claude Code' -message 'Claude Code has stopped' -sound Glass"
}
```

## 通知を出す方法（Windows）

Windows は通知ができるようになるまで苦労した。自分の環境では以下のようにすれば動いたが再現性は不明。

ポイント

- powershell を使う場合は `powershell` ではなく `powershell.exe` とする
- 新しい powershell (pwsh) を使う場合は `pwsh.exe` でも `pwsh` でもよい

### 最も単純な音を鳴らす方法

```json
{
  "type": "command",
  "command": "powershell.exe -c \"[console]::beep(1000,500)\""
}
```

### 文字の読み上げ

```json
{
  "type": "command",
  "command": "mshta vbscript:Execute(\"CreateObject(\"\"SAPI.SpVoice\"\").Speak(\"\"クロードが停止しました\"\"):close\")"
}
```

### 任意の音声ファイルを鳴らす

```json
{
  "type": "command",
  "command": "pwsh.exe -sta -c \"Add-Type -AssemblyName presentationCore; $m=New-Object System.Windows.Media.MediaPlayer; $m.Open([uri]'C:\\Path\\to\\your\\sound.mp3'); $m.Play(); Start-Sleep 3\""
}
```

`~/dotfiles/claude/ringtones` に音声ファイルを置いておき、ランダムに選んで鳴らすようにするのも良い。

```json
{
  "type": "command",
  "command": "pwsh -sta -c \"Add-Type -AssemblyName presentationCore; $homePath=[Environment]::GetFolderPath('UserProfile'); $dir=Join-Path $homePath 'dotfiles\\claude\\ringtones'; $files=Get-ChildItem -LiteralPath $dir -File | Where-Object { $_.Extension -match '^\\.(mp3|wav)$' }; if($files){ $pick=$files | Get-Random; $m=New-Object System.Windows.Media.MediaPlayer; $m.Open([uri]$pick.FullName); $m.Play(); Start-Sleep 10 } else { [console]::Beep(880,300) }\""
},
```

powershell（新しい方）で BurntToast モジュールをインストールする。

```powershell
Install-Module BurntToast -Scope CurrentUser
```

```json
{
  "type": "command",
  "command": "pwsh -c \"New-BurntToastNotification -Text 'Claude finished', (Get-Date).ToString('HH:mm:ss')\""
}
```

## Slack に通知を送る

Slack の Incoming Webhooks を使うと、指定した URL に対して HTTP リクエストを送ることで Slack にメッセージを投稿できます。

```json
{
  "type": "command",
  "command": "curl https://hooks.slack.com/triggers/some_example_url"
}
```
