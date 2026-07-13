#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="${1:?root directory is required}"
CODEX_HOME_DIR="${2:?codex home is required}"
SOURCE_DIR="${ROOT_DIR}/agents"
TARGET_DIR="${CODEX_HOME_DIR}/agents"
MANIFEST="${CODEX_HOME_DIR}/.codex-dotfiles-native-agents.manifest"

backup_target() {
  local target="$1"
  local backup
  backup="${target}.backup.$(date +%Y%m%d_%H%M%S)"
  while [ -e "$backup" ] || [ -L "$backup" ]; do
    backup="${target}.backup.$(date +%Y%m%d_%H%M%S)_$RANDOM"
  done
  mv -- "$target" "$backup"
  printf "%s\n" "$backup"
}

mkdir -p "$CODEX_HOME_DIR"
if [ -L "$TARGET_DIR" ]; then
  target_backup="$(backup_target "$TARGET_DIR" | tail -n 1)"
  printf "   agents directory symlink をバックアップ: %s -> %s\n" "$TARGET_DIR" "$target_backup"
elif [ -e "$TARGET_DIR" ] && [ ! -d "$TARGET_DIR" ]; then
  printf "❌ Agent target is not a directory: %s\n" "$TARGET_DIR" >&2
  exit 1
fi
mkdir -p "$TARGET_DIR"

is_managed_name() {
  local name="$1"
  [ -f "$MANIFEST" ] && tr -d '\r' <"$MANIFEST" | grep -Fqx -- "$name"
}

copy_to_temp() {
  local source="$1"
  local target="$2"
  local temporary="${target}.tmp.$$.$RANDOM"
  while [ -e "$temporary" ] || [ -L "$temporary" ]; do
    temporary="${target}.tmp.$$.$RANDOM"
  done
  cp -p -- "$source" "$temporary"
  printf "%s\n" "$temporary"
}

install_file() {
  local source="$1"
  local target="$2"
  local name="$3"
  local temporary
  local backup=""

  temporary="$(copy_to_temp "$source" "$target")"
  if is_managed_name "$name"; then
    if [ -f "$target" ] && [ ! -L "$target" ]; then
      mv -f -- "$temporary" "$target"
      return 0
    fi
    if [ -e "$target" ] || [ -L "$target" ]; then
      backup="$(backup_target "$target" | tail -n 1)"
      printf "   managed agent の不正な target をバックアップ: %s -> %s\n" "$target" "$backup"
    fi
    if mv -f -- "$temporary" "$target"; then
      return 0
    fi
    rm -f -- "$temporary"
    if [ -n "$backup" ] && [ ! -e "$target" ] && [ ! -L "$target" ]; then
      mv -- "$backup" "$target" || true
    fi
    return 1
  fi

  if [ -e "$target" ] || [ -L "$target" ]; then
    backup="$(backup_target "$target" | tail -n 1)"
    printf "   既存 agent をバックアップ: %s -> %s\n" "$target" "$backup"
  fi
  if mv -f -- "$temporary" "$target"; then
    return 0
  fi
  rm -f -- "$temporary"
  if [ -n "$backup" ] && [ ! -e "$target" ] && [ ! -L "$target" ]; then
    mv -- "$backup" "$target" || true
  fi
  return 1
}

current_manifest="${MANIFEST}.tmp.$$"
cleanup() { rm -f -- "$current_manifest"; }
trap cleanup EXIT
: >"$current_manifest"

if [ -d "$SOURCE_DIR" ]; then
  for source in "$SOURCE_DIR"/*.toml; do
    [ -f "$source" ] || continue
    name="$(basename "$source")"
    target="$TARGET_DIR/$name"
    if [ -e "$target" ] || [ -L "$target" ]; then
      if ! is_managed_name "$name" && [ ! -f "$target" ]; then
        printf "   ⚠️  unmanaged agent を保持: %s\n" "$target"
        continue
      fi
    fi
    install_file "$source" "$target" "$name" || exit 1
    printf "%s\n" "$name" >>"$current_manifest"
    printf "   ✅ agent file: %s\n" "$target"
  done
fi

if [ -f "$MANIFEST" ]; then
  while IFS= read -r name; do
    name="${name%$'\r'}"
    [ -n "$name" ] || continue
    case "$name" in
      */*|.*) continue ;;
    esac
    grep -Fqx -- "$name" "$current_manifest" && continue
    target="$TARGET_DIR/$name"
    if [ -e "$target" ] || [ -L "$target" ]; then
      printf "   🗑️  stale managed agent を削除: %s\n" "$target"
      rm -f -- "$target"
    fi
  done <"$MANIFEST"
fi

mv -f -- "$current_manifest" "$MANIFEST"
trap - EXIT
