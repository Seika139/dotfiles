param(
    [ValidateSet("All", "Audio")]
    [string]$Mode = "All"
)

$ErrorActionPreference = "Stop"

# 一時停止スイッチ。
# $false に戻すと、Stop hook 時の音声読み上げ・着信音再生も再開されます。
# トースト通知と Slack 通知はこの値に関係なく動きます。
$TemporarilyDisableAudioNotification = $true

# Windows のトースト通知だけを表示します。
# BurntToast モジュールがない環境では何もせず終了します。
function Invoke-ToastNotification {
    try {
        Import-Module BurntToast -ErrorAction Stop
        $toolName = $env:NOTIFY_TOOL_NAME
        if ([string]::IsNullOrWhiteSpace($toolName)) {
            $toolName = "Claude"
        }
        $title = "$toolName Code"
        $body = "実行中の $toolName が停止しました.`n$env:USERNAME@$env:COMPUTERNAME"
        New-BurntToastNotification -Text $title, $body | Out-Null
    }
    catch {
        return
    }
}

# 音声読み上げ・着信音・beep fallback を順番に試します。
# 今は上の一時停止スイッチにより、通常の Stop hook からは呼ばれません。
function Invoke-AudioNotification {
    try {
        Start-Sleep -Seconds 9.7

        try {
            Add-Type -AssemblyName System.Speech
            $toolName = $env:NOTIFY_TOOL_NAME
            if ([string]::IsNullOrWhiteSpace($toolName)) {
                $toolName = "Claude"
            }
            $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
            try {
                $speaker.Speak("$toolName が停止しました")
            }
            finally {
                $speaker.Dispose()
            }
        }
        catch {
            # Continue to the ringtone fallback even if speech synthesis is unavailable.
        }

        Add-Type -AssemblyName PresentationCore
        $homePath = [Environment]::GetFolderPath("UserProfile")
        $dir = Join-Path $homePath "dotfiles\claude\ringtones"
        $files = @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -match "^\.(mp3|wav)$" })

        if ($files.Count -gt 0) {
            $pick = $files | Get-Random
            $player = New-Object System.Windows.Media.MediaPlayer
            $player.Volume = 0.4
            $player.Open([uri]$pick.FullName)
            $player.Play()
            Start-Sleep -Seconds 10
            $player.Close()
        }
        else {
            [console]::Beep(880, 300)
        }
    }
    catch {
        return
    }
}

try {
    # 子プロセスとして -Mode Audio で呼ばれた場合の処理です。
    # 一時停止中は何も鳴らさず、正常終了だけします。
    if ($Mode -eq "Audio") {
        if (-not $TemporarilyDisableAudioNotification) {
            Invoke-AudioNotification
        }
        exit 0
    }

    if ($env:CLAUDE_NOTIFY_DISABLE_TOAST -ne "1") {
        Invoke-ToastNotification
    }

    # 音声通知は遅延実行したいので、通常は別 PowerShell プロセスで起動します。
    # 一時停止中はここを通らないため、音声用の子プロセス自体を作りません。
    $pwsh = (Get-Command pwsh.exe -ErrorAction SilentlyContinue).Source
    if (-not $pwsh) {
        $pwsh = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
    }

    if (
        -not $TemporarilyDisableAudioNotification -and
        $pwsh -and
        $env:CLAUDE_NOTIFY_DISABLE_AUDIO -ne "1"
    ) {
        Start-Process -FilePath $pwsh `
            -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-Mode", "Audio") `
            -WindowStyle Hidden | Out-Null
    }
}
catch {
}

exit 0
