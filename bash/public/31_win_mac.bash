#!/usr/bin/env bash

path_posix_to_win() {
    local path="$1"
    if [ -z "$path" ]; then
        echo "Error: No path provided" >&2
        return 1
    fi

    # /c/foo/bar → C:\foo\bar
    if [[ "$path" =~ ^/([a-zA-Z])/(.*)$ ]]; then
        local drive="${BASH_REMATCH[1]}"
        local rest="${BASH_REMATCH[2]}"
        local win_rest="${rest//\//\\}"
        printf '%s\n' "${drive^^}:\\$win_rest"
        return 0
    fi

    # /mnt/c/foo/bar → C:\foo\bar (WSL)
    if [[ "$path" =~ ^/mnt/([a-zA-Z])/(.*)$ ]]; then
        local drive="${BASH_REMATCH[1]}"
        local rest="${BASH_REMATCH[2]}"
        local win_rest="${rest//\//\\}"
        printf '%s\n' "${drive^^}:\\$win_rest"
        return 0
    fi

    # UNC: //server/share/path → \\server\share\path
    if [[ "$path" =~ ^//([^/]+)/([^/]+)(/.*)?$ ]]; then
        local server="${BASH_REMATCH[1]}"
        local share="${BASH_REMATCH[2]}"
        local tail="${BASH_REMATCH[3]}"
        local win_tail="${tail//\//\\}"
        printf '%s\n' "\\\\$server\\$share$win_tail"
        return 0
    fi

    # それ以外（相対パスなど）は / → \ の置換だけ
    local win="${path//\//\\}"
    printf '%s\n' "$win"
}

path_win_to_posix() {
    local path="$1"
    if [ -z "$path" ]; then
        echo "Error: No path provided" >&2
        return 1
    fi

    # バックスラッシュ → スラッシュ
    path="${path//\\//}"

    # C:/foo/bar → /c/foo/bar
    if [[ "$path" =~ ^([a-zA-Z]):/(.*)$ ]]; then
        local drive="${BASH_REMATCH[1],,}"
        local rest="${BASH_REMATCH[2]}"
        printf '/%s/%s\n' "$drive" "$rest"
        return 0
    fi

    # UNC: //server/share/path はそのまま POSIX で通す
    if [[ "$path" =~ ^// ]]; then
        printf '%s\n' "$path"
        return 0
    fi

    # それ以外（相対パスなど）
    printf '%s\n' "$path"
}
