#!/bin/bash

#MISE description="agmsg (cross-agent messaging) を pin した SHA から install / update する。APM 非管理の peer tool"
#MISE depends=["sqlite3-available"]
#MISE quiet=true
#USAGE flag "--cmd <cmd>" help="コマンド名 (default: agmsg)。Claude は slash、Codex は dollar prefix で起動"
#USAGE flag "--ref <ref>" help="導入する agmsg のコミット SHA か ref (default は pin 済み SHA)"

# ---------------------------------------------------------------------------
# 設計 (docs/agmsg-integration.md 参照):
#   agmsg は APM パッケージではなく自前 installer を持つ peer tool。profiles/*/apm.yml
#   には載せず、この専用 task で導入する。
#
#   - 取得: setup.sh の curl|bash は使わず、SHA pin で clone → checkout → ローカルの
#           install.sh を実行する (供給網対策)。
#   - 冪等: 既存 install (~/.agents/skills/<cmd>/.agmsg) があれば DB/team を保持する
#           `install.sh --update`、無ければ新規 `install.sh --cmd <cmd>`。
#   - 配置先 (全て実体, symlink 汚染なし):
#       ~/.agents/skills/<cmd>/   (scripts + SQLite DB)
#       ~/.claude/commands/<cmd>.md  (Claude slash command)
#       ~/.codex/config.toml         (writable_roots を追記。版管理外なので各 PC で要実行)
#
#   APM prune は dotfiles/agents の install/update task では使われないため、APM が
#   agmsg dir を消す心配はない。唯一の注意は APM package 名に <cmd> を使わないこと。
# ---------------------------------------------------------------------------

set -euo pipefail

# pin。更新時は agmsg の差分をレビューしてから SHA を上げる。
DEFAULT_AGMSG_REF="5aad45e85d8a541d5d202ecc58c4011749804618"

CMD="${usage_cmd:-agmsg}"
AGMSG_REF="${usage_ref:-$DEFAULT_AGMSG_REF}"
SKILL_MARKER="${HOME}/.agents/skills/${CMD}/.agmsg"

printf "%s\n" "🛰️  Installing agmsg (cmd: ${CMD}, ref: ${AGMSG_REF})"

TMP_DIR="$(mktemp -d -t agmsg-install.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

# 全 SHA を取りに行けるよう blob フィルタ付きで clone し、pin した ref を checkout する。
git clone --filter=blob:none --no-checkout --quiet \
  https://github.com/fujibee/agmsg.git "$TMP_DIR/agmsg"
git -C "$TMP_DIR/agmsg" checkout --quiet "$AGMSG_REF"

INSTALLER="$TMP_DIR/agmsg/install.sh"
if [ ! -f "$INSTALLER" ]; then
  printf "%s\n" "❌ Error: install.sh が ref '${AGMSG_REF}' に見つかりません" >&2
  exit 1
fi
chmod +x "$INSTALLER"

if [ -f "$SKILL_MARKER" ]; then
  printf "%s\n" "   ♻️  既存 install を検出 → --update (DB / team 設定を保持)"
  "$INSTALLER" --update
else
  printf "%s\n" "   ✨ 新規 install → --cmd ${CMD}"
  "$INSTALLER" --cmd "$CMD"
fi

printf "%s\n" "✅ agmsg ready: Claude では /${CMD}, Codex では \$${CMD}"
printf "%s\n" "   ⚠️  ~/.codex/config.toml への writable_roots 追記は版管理外。別 PC では本 task を再実行すること"
