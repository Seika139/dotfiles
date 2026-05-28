#!/bin/bash

#MISE description="link.sh で作られた legacy symlink を Trash 退避して APM 配備の邪魔をしないようにする (新規 PC で mise run install 前に 1 回実行)"
#MISE quiet=true

# ---------------------------------------------------------------------------
# 新規 PC で dotfiles の claude/codex/gemini link.sh を回したことがある場合、
# ~/.claude/{commands,skills}, ~/.codex/skills/<n>, ~/.gemini/commands といった
# 場所に dotfiles を指す symlink が残っている。これらは APM 配備物 (real dir)
# と衝突したり、symlink を通じて書き込みが dotfiles 内に透過したりするため、
# `mise run install` 前に Trash 退避するのが安全。
#
# 安全策: Trash 経由 (= macOS Finder ゴミ箱) なので reversible。冪等。
# ---------------------------------------------------------------------------

set -eu

TS=$(date +%Y%m%d_%H%M%S)
TRASH_DIR=~/.Trash/apm-migrate-$TS
mkdir -p "$TRASH_DIR"

echo "=== Trash dir: $TRASH_DIR ==="
echo ""

# ---------------------------------------------------------------------------
# Step 1: ~/.claude/commands (link.sh が作る symlink → dotfiles)
# ---------------------------------------------------------------------------
echo "--- Step 1: ~/.claude/commands ---"
if [ -L ~/.claude/commands ]; then
  target=$(readlink ~/.claude/commands)
  case "$target" in
  */dotfiles/*)
    mv ~/.claude/commands "$TRASH_DIR/claude-commands"
    echo "  💾 moved (was symlink → $target)"
    ;;
  *)
    echo "  ⏭️   skipped: symlink points elsewhere ($target)"
    ;;
  esac
elif [ -e ~/.claude/commands ]; then
  echo "  ⏭️   skipped: exists but not a symlink (real file/dir — APM may have already created it)"
else
  echo "  ✅ already gone"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 2: ~/.gemini/commands (link.sh が作る symlink → dotfiles)
# ---------------------------------------------------------------------------
echo "--- Step 2: ~/.gemini/commands ---"
if [ -L ~/.gemini/commands ]; then
  target=$(readlink ~/.gemini/commands)
  case "$target" in
  */dotfiles/*)
    mv ~/.gemini/commands "$TRASH_DIR/gemini-commands"
    echo "  💾 moved (was symlink → $target)"
    ;;
  *)
    echo "  ⏭️   skipped: symlink points elsewhere ($target)"
    ;;
  esac
elif [ -e ~/.gemini/commands ]; then
  echo "  ⏭️   skipped: exists but not a symlink (real file/dir)"
else
  echo "  ✅ already gone"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 3: ~/.codex/skills/ 配下の dotfiles を指す per-skill symlink
#         (link.sh の旧バージョンが per-skill symlink を作っていた)
# ---------------------------------------------------------------------------
echo "--- Step 3: ~/.codex/skills/ per-skill symlinks → dotfiles ---"
if [ -d ~/.codex/skills ]; then
  mkdir -p "$TRASH_DIR/codex-skills"
  moved=0
  skipped=0
  for entry in ~/.codex/skills/* ~/.codex/skills/.[!.]*; do
    [ -e "$entry" ] || continue
    if [ -L "$entry" ]; then
      target=$(readlink "$entry")
      case "$target" in
      */dotfiles/*)
        mv "$entry" "$TRASH_DIR/codex-skills/"
        moved=$((moved + 1))
        ;;
      *)
        skipped=$((skipped + 1))
        ;;
      esac
    fi
  done
  echo "  💾 moved: $moved, ⏭️   skipped (non-dotfiles or real dirs): $skipped"
  rmdir "$TRASH_DIR/codex-skills" 2>/dev/null && echo "  (empty trash subdir cleaned)" || true
else
  echo "  ✅ ~/.codex/skills/ does not exist"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 4: ~/.claude/skills (link.sh が作る dir-level symlink → dotfiles)
# ---------------------------------------------------------------------------
echo "--- Step 4: ~/.claude/skills ---"
if [ -L ~/.claude/skills ]; then
  target=$(readlink ~/.claude/skills)
  case "$target" in
  */dotfiles/*)
    mv ~/.claude/skills "$TRASH_DIR/claude-skills"
    echo "  💾 moved (was symlink → $target)"
    ;;
  *)
    echo "  ⏭️   skipped: symlink points elsewhere ($target)"
    ;;
  esac
elif [ -e ~/.claude/skills ]; then
  echo "  ⏭️   skipped: exists but not a symlink (real file/dir — APM may have already created it)"
else
  echo "  ✅ already gone"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 5: ~/.claude/rules (link.sh が作る dir-level symlink → dotfiles)
#         rules は APM instructions primitive (例: commit-message) として
#         ~/.claude/rules/<n>.md に配備されるようになったため、symlink を外して
#         APM が real dir として書けるようにする。
# ---------------------------------------------------------------------------
echo "--- Step 5: ~/.claude/rules ---"
if [ -L ~/.claude/rules ]; then
  target=$(readlink ~/.claude/rules)
  case "$target" in
  */dotfiles/*)
    mv ~/.claude/rules "$TRASH_DIR/claude-rules"
    echo "  💾 moved (was symlink → $target)"
    ;;
  *)
    echo "  ⏭️   skipped: symlink points elsewhere ($target)"
    ;;
  esac
elif [ -e ~/.claude/rules ]; then
  echo "  ⏭️   skipped: exists but not a symlink (real file/dir — APM may have already created it)"
else
  echo "  ✅ already gone"
fi
echo ""

# 注意: ~/.agents/skills/ は削除しない。default flag (`apm install -g --frozen`) では
# ここが cross-tool 共有先として Codex/Gemini/Cursor/Copilot の skill 配備先になるため
# (load-bearing)。legacy symlink の掃除は Step 1-4 で完了。

# ---------------------------------------------------------------------------
# 検証: 残っているものを表示
# ---------------------------------------------------------------------------
echo "=== AFTER ==="
show_command_skill_entries() {
  local base=$1
  local matched=0
  local entry
  for entry in "$base"/commands "$base"/commands-* "$base"/skills "$base"/skills-*; do
    [ -e "$entry" ] || [ -L "$entry" ] || continue
    ls -ld "$entry"
    matched=1
  done
  [ "$matched" -eq 1 ] || echo "  (no commands/skills entries)"
}

echo "--- ~/.claude/ ---"
show_command_skill_entries "$HOME/.claude"
echo ""
echo "--- ~/.gemini/ ---"
show_command_skill_entries "$HOME/.gemini"
echo ""
echo "--- ~/.codex/skills/ remaining ---"
ls -la ~/.codex/skills/ 2>/dev/null || echo "  (~/.codex/skills/ removed)"
echo ""
echo "--- ~/.agents/skills/ remaining ---"
ls -1 ~/.agents/skills/ 2>/dev/null || echo "  (~/.agents/skills/ does not exist)"
echo ""
echo "--- Trash contents ---"
ls -la "$TRASH_DIR/"

echo ""
echo "✅ Migration complete. Next: 'mise run install' で APM 配備を開始してください。"
