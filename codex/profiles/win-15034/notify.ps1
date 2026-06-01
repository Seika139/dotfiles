param(
    [string]$Argument,
    [double]$Volume = 0.3
)

$Message = "Codex finished"

# 既定では着信音 (MP3 / Beep) を鳴らさない。
# CODEX_NOTIFY_RINGTONE=1 (true/on/yes) で明示的に有効化する。bash 版 notify.sh と挙動を揃える。
$ringtoneEnabled = $false
if ($env:CODEX_NOTIFY_RINGTONE -and ($env:CODEX_NOTIFY_RINGTONE.Trim().ToLower() -in @('1', 'true', 'on', 'yes'))) {
    $ringtoneEnabled = $true
}

# 音量も bash 版と同じ環境変数で上書きできるようにする。
if ($env:CODEX_NOTIFY_RINGTONE_VOLUME) {
    [double]::TryParse($env:CODEX_NOTIFY_RINGTONE_VOLUME, [ref]$Volume) | Out-Null
}

if (-not [string]::IsNullOrWhiteSpace($Argument) -and $Argument -ne '{message}') {
    try {
        $payload = $Argument | ConvertFrom-Json -ErrorAction Stop
        $candidate = $payload.'last-assistant-message'

        if ([string]::IsNullOrWhiteSpace($candidate) -and $payload.'input-messages') {
            $candidate = $payload.'input-messages'[-1]
        }

        if ([string]::IsNullOrWhiteSpace($candidate) -and $payload.type) {
            $candidate = "Codex event: $($payload.type)"
        }

        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $Message = $candidate.Trim()
        }
        else {
            $Message = ($payload | ConvertTo-Json -Compress)
        }
    }
    catch {
        $Message = $Argument
    }
}

# Show toast notification if BurntToast is available.
try {
    Import-Module BurntToast -ErrorAction Stop
    New-BurntToastNotification -Text 'Codex On Windows', $Message, (Get-Date).ToString('HH:mm:ss')
}
catch {
    Write-Verbose "BurntToast unavailable: $($_.Exception.Message)"
}

# Play a random ringtone (or fallback beep) on the STA thread.
# 既定では無効。CODEX_NOTIFY_RINGTONE=1 のときだけ再生する。
if ($ringtoneEnabled) {
    Add-Type -AssemblyName presentationCore
    $homePath = [Environment]::GetFolderPath('UserProfile')
    $ringtoneDir = Join-Path $homePath 'dotfiles\codex\ringtones'

    if (Test-Path -LiteralPath $ringtoneDir) {
        $candidates = Get-ChildItem -LiteralPath $ringtoneDir -File |
        Where-Object { $_.Extension -match '^\.(mp3|wav)$' }

        if ($candidates) {
            $pick = Get-Random -InputObject $candidates
            $player = New-Object System.Windows.Media.MediaPlayer
            $player.Volume = $Volume
            $player.Open([Uri]$pick.FullName)
            $player.Play()
            Start-Sleep -Seconds 12
        }
        else {
            [Console]::Beep(880, 300)
        }
    }
    else {
        [Console]::Beep(880, 300)
    }
}
