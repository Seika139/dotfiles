#!/bin/bash

#MISE description="現在のプロファイル設定と install 状況を確認"
#MISE depends=["check_env"]
#MISE quiet=true
#USAGE flag "--prof <prof>" help="プロファイル名"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSPECT_SCRIPT="${ROOT_DIR}/mise/scripts/inspect_apm_yml.py"

PROFILE="${usage_prof:-${DEFAULT_AGENTS_PROFILE:-}}"
PROFILE_PATH="${ROOT_DIR}/$PROFILES_DIR/$PROFILE"
PROFILE_YML="$PROFILE_PATH/apm.yml"
PRIVATE_PATH="${ROOT_DIR}/$PROFILES_DIR/private"
PRIVATE_YML="$PRIVATE_PATH/apm.yml"
PRIVATE_LOCK="$PRIVATE_PATH/apm.lock.yaml"
HAS_PRIVATE=false
if [ -f "$PRIVATE_YML" ]; then
  HAS_PRIVATE=true
fi

# 🦄 セクション 1: Environment Check
printf "%s\n" "🦄 Environment Check"
printf "OS                   =\\033[36m %s\\033[0m\n" "$(uname -s)"
printf "IS_WSL               =\\033[36m %s\\033[0m\n" "$IS_WSL"
printf "config_root          =\\033[36m %s\\033[0m\n" "${ROOT_DIR}"
printf "Selected profile     =\\033[36m %s\\033[0m\n" "$PROFILE"
printf "Profile path         =\\033[36m %s\\033[0m\n" "$PROFILE_PATH"
if [ "$HAS_PRIVATE" = "true" ]; then
  printf "Private overlay      =\\033[36m %s\\033[0m\n" "$PRIVATE_YML"
else
  printf "Private overlay      =\\033[2m (none)\\033[0m\n"
fi

if [ ! -d "$PROFILE_PATH" ]; then
  printf "❌ Profile directory does not exist:\\033[36m %s\\033[0m\n" "$PROFILE_PATH"
  exit 1
fi

# 📂 セクション 2: apm.yml dependencies
if [ ! -f "$PROFILE_YML" ]; then
  printf "\n📂 apm.yml: \\033[31m❌ does not exist\\033[0m\n"
  exit 1
fi

INSPECT_ARGS=(--base "$PROFILE_YML")
if [ "$HAS_PRIVATE" = "true" ]; then
  INSPECT_ARGS+=(--overlay "$PRIVATE_YML")
fi
INSPECT_OUT="$(uv run --quiet "$INSPECT_SCRIPT" "${INSPECT_ARGS[@]}")"

TARGETS_CSV="$(printf "%s\n" "$INSPECT_OUT" | awk -F'\t' '$1=="target"{print $2}' | paste -sd, -)"
APM_BASE="$(printf "%s\n" "$INSPECT_OUT" | awk -F'\t' '$1=="apm-base"{print $2}')"
APM_OVERLAY="$(printf "%s\n" "$INSPECT_OUT" | awk -F'\t' '$1=="apm-overlay"{print $2}')"
DECLARED_SORTED="$(printf "%s\n" "$INSPECT_OUT" | awk -F'\t' '$1=="apm-merged"{print $2}' | sort -u)"

# declared package を primitive 種別で分類する。
# instructions (例: commit-message) は ~/.claude/rules/ に、agents は ~/.claude/agents/
# に配備されるため、skills 一覧 (~/.claude/skills/) には現れない。
# 種別は ~/.apm/apm_modules の .apm/ 構造で判定する。
classify_is_instruction() {
  compgen -G "$HOME/.apm/apm_modules/*/*/packages/$1/.apm/instructions" >/dev/null 2>&1
}
classify_is_agent() {
  compgen -G "$HOME/.apm/apm_modules/*/*/packages/$1/.apm/agents" >/dev/null 2>&1
}
DECLARED_SKILLS=""
DECLARED_INSTRUCTIONS=""
DECLARED_AGENTS=""
while IFS= read -r _pkg; do
  [ -n "$_pkg" ] || continue
  _is_instruction=false
  _is_agent=false
  if classify_is_instruction "$_pkg"; then
    DECLARED_INSTRUCTIONS+="${_pkg}"$'\n'
    _is_instruction=true
  fi
  if classify_is_agent "$_pkg"; then
    DECLARED_AGENTS+="${_pkg}"$'\n'
    _is_agent=true
  fi
  if [ "$_is_instruction" = "false" ] && [ "$_is_agent" = "false" ]; then
    DECLARED_SKILLS+="${_pkg}"$'\n'
  fi
done <<EOF
$DECLARED_SORTED
EOF
DECLARED_SKILLS="$(printf "%s" "$DECLARED_SKILLS" | sort -u)"
DECLARED_INSTRUCTIONS="$(printf "%s" "$DECLARED_INSTRUCTIONS" | sort -u)"
DECLARED_AGENTS="$(printf "%s" "$DECLARED_AGENTS" | sort -u)"

printf "\n🎯 Targets:\\033[36m %s\\033[0m\n" "${TARGETS_CSV:-(none)}"

APM_BASE_COUNT="$(printf "%s" "$APM_BASE" | grep -c . || true)"
APM_OVERLAY_COUNT="$(printf "%s" "$APM_OVERLAY" | grep -c . || true)"
PROFILE_YML_REL="${PROFILE_YML#"${ROOT_DIR}"/}"
PRIVATE_YML_REL="${PRIVATE_YML#"${ROOT_DIR}"/}"

printf "\n📂 dependencies.apm:\n"
printf "   base    : %b%2d packages%b (%s)\n" '\033[36m' "$APM_BASE_COUNT" '\033[0m' "$PROFILE_YML_REL"
if [ "$HAS_PRIVATE" = "true" ]; then
  printf "   overlay : %b%2d packages%b (%s)\n" '\033[36m' "$APM_OVERLAY_COUNT" '\033[0m' "$PRIVATE_YML_REL"
fi

# 🔒 セクション 3: apm.lock.yaml
printf "\n🔒 apm.lock.yaml:\n"
if [ "$HAS_PRIVATE" = "true" ]; then
  if [ -f "$PRIVATE_LOCK" ]; then
    printf "   ✅ %s (gitignored)\n" "$PRIVATE_LOCK"
  else
    printf "\\033[33m%s\\033[0m\n" "   ⚠️ private overlay 有効だが lock 未生成 (run 'mise run install')"
  fi
elif [ -f "$PROFILE_PATH/apm.lock.yaml" ]; then
  printf "   ✅ %s\n" "$PROFILE_PATH/apm.lock.yaml"
else
  printf "\\033[33m%s\\033[0m\n" "   ⚠️ not generated yet (run 'mise run install')"
fi

# 🌐 セクション 4: Installed at user scope
#   - claude / agents: APM が declared package を実体配備する正の install 先
#   - codex / gemini : `~/.agents/skills/` を読みに行くため per-tool には配備されない。
#                      actual を参考表示し、手動配備の遺物 (codex-primary-runtime 等) の
#                      可視化に留める
list_actual() {
  local dir="$1"
  if [ -d "$dir" ]; then
    find "$dir" -mindepth 1 -maxdepth 1 -not -name '.*' -exec basename {} \; 2>/dev/null | sort -u
  fi
}

# rules/ は package 名 = `<name>.md` (file) なので比較用に拡張子を剥がす
# (skills/ は dir 名 = package 名で一致するため list_actual で足りる)
list_actual_rules() {
  local dir="$1"
  if [ -d "$dir" ]; then
    find "$dir" -mindepth 1 -maxdepth 1 -not -name '.*' -exec basename {} \; 2>/dev/null | sed 's/\.md$//' | sort -u
  fi
}

# agents primitive は package 名と配備ファイル名が一致しないことがある。
# APM module 側の .apm/agents/*.md が ~/.claude/agents/ に全て存在すれば
# package 単位で installed とみなす。
agent_package_installed() {
  local pkg="$1" agent_dir file all_found has_file
  for agent_dir in "$HOME"/.apm/apm_modules/*/*/packages/"$pkg"/.apm/agents; do
    [ -d "$agent_dir" ] || continue
    all_found=true
    has_file=false
    for file in "$agent_dir"/*.md; do
      [ -f "$file" ] || continue
      has_file=true
      if [ ! -f "$HOME/.claude/agents/$(basename "$file")" ]; then
        all_found=false
        break
      fi
    done
    if [ "$has_file" = "true" ] && [ "$all_found" = "true" ]; then
      return 0
    fi
  done
  return 1
}

list_actual_agent_packages() {
  local agent_dir pkg
  for agent_dir in "$HOME"/.apm/apm_modules/*/*/packages/*/.apm/agents; do
    [ -d "$agent_dir" ] || continue
    pkg="$(basename "$(dirname "$(dirname "$agent_dir")")")"
    if agent_package_installed "$pkg"; then
      printf "%s\n" "$pkg"
    fi
  done
  list_unmanaged_agent_files
}

list_known_agent_files() {
  local file
  for file in "$HOME"/.apm/apm_modules/*/*/packages/*/.apm/agents/*.md; do
    [ -f "$file" ] || continue
    basename "$file" .md
  done | sort -u
}

list_unmanaged_agent_files() {
  local file name
  [ -d "$HOME/.claude/agents" ] || return 0
  for file in "$HOME"/.claude/agents/*.md; do
    [ -f "$file" ] || continue
    name="$(basename "$file" .md)"
    if ! printf "%s\n" "${KNOWN_AGENT_FILES:-}" | grep -Fxq "$name"; then
      printf "unmanaged:%s\n" "$name"
    fi
  done | sort -u
}

# 非 APM の peer tool (agmsg 等) を識別する。APM が宣言しない skill dir でも、
# agmsg installer が必ず置く `.agmsg` マーカー (固定名, cmd 名を変えても同じ) を持つ
# ものは drift ではなく external として扱い、declared vs actual 比較から除外する。
list_external_skills() {
  local dir="$1" d
  [ -d "$dir" ] || return 0
  for d in "$dir"/*/; do
    [ -d "$d" ] || continue
    if [ -e "${d}.agmsg" ]; then
      basename "$d"
    fi
  done | sort -u
}

print_diff() {
  local label="$1" dir="$2" declared="$3" actual="$4" missing extra m_count e_count a_count d_count count_color
  d_count="$(printf "%s" "$declared" | grep -c . || true)"
  a_count="$(printf "%s" "$actual" | grep -c . || true)"
  missing="$(comm -23 <(printf "%s\n" "$declared") <(printf "%s\n" "$actual"))"
  extra="$(comm -13 <(printf "%s\n" "$declared") <(printf "%s\n" "$actual"))"
  m_count="$(printf "%s" "$missing" | grep -c . || true)"
  e_count="$(printf "%s" "$extra" | grep -c . || true)"

  printf "   %s (%s):\n" "$label" "$dir"
  if [ "$d_count" = "$a_count" ]; then
    count_color='\033[32m' # green: declared と actual の件数が一致
  else
    count_color='\033[31m' # red: 件数が不一致
  fi
  printf "    %b declared=%s actual=%s\\033[0m" "$count_color" "$d_count" "$a_count"
  if [ "$m_count" = "0" ] && [ "$e_count" = "0" ]; then
    printf " \\033[32m✅ in sync\\033[0m\n"
    return
  fi
  printf "\n"
  if [ "$m_count" != "0" ]; then
    printf "     \\033[33m⚠️ missing (%s):\\033[0m\n" "$m_count"
    printf "%s\n" "$missing" | sed 's/^/       - /'
  fi
  if [ "$e_count" != "0" ]; then
    printf "     \\033[38;5;200m• extra (%s, not declared):\\033[0m\n" "$e_count"
    printf "%s\n" "$extra" | sed 's/^/       - /'
  fi
}

print_actual() {
  local label="$1" dir="$2" actual a_count
  actual="$(list_actual "$dir")"
  a_count="$(printf "%s" "$actual" | grep -c . || true)"
  printf "   %s (%s):\n" "$label" "$dir"
  if [ "$a_count" = "0" ]; then
    printf "     \\033[2m(empty — APM は cross-tool 配備のみ)\\033[0m\n"
    return
  fi
  printf "     \\033[2mactual=%s (cross-tool 配備のため declared 比較なし):\\033[0m\n" "$a_count"
  printf "%s\n" "$actual" | sed 's/^/       - /'
}

printf "\n🌐 Skills (declared vs actual):\n"
print_diff "claude" "$HOME/.claude/skills" "$DECLARED_SKILLS" "$(list_actual "$HOME/.claude/skills")"

# agents skills は APM cross-tool 配備先だが、非 APM の peer tool (agmsg) も同居する。
# external を actual から除いて APM の drift だけを比較し、external は別枠で可視化する。
AGENTS_ACTUAL="$(list_actual "$HOME/.agents/skills")"
AGENTS_EXTERNAL="$(list_external_skills "$HOME/.agents/skills")"
if [ -n "$AGENTS_EXTERNAL" ]; then
  AGENTS_ACTUAL="$(comm -23 <(printf "%s\n" "$AGENTS_ACTUAL") <(printf "%s\n" "$AGENTS_EXTERNAL"))"
fi
print_diff "agents" "$HOME/.agents/skills" "$DECLARED_SKILLS" "$AGENTS_ACTUAL"
if [ -n "$AGENTS_EXTERNAL" ]; then
  printf "     \\033[36m🔌 external (非 APM / agmsg-managed, drift 比較から除外):\\033[0m\n"
  printf "%s\n" "$AGENTS_EXTERNAL" | sed 's/^/       - /'
fi

printf "\n🤖 Agents (declared vs actual):\n"
KNOWN_AGENT_FILES="$(list_known_agent_files)"
print_diff "claude agents" "$HOME/.claude/agents" "$DECLARED_AGENTS" "$(list_actual_agent_packages | sort -u)"

printf "\n📐 Instructions / rules (declared vs actual):\n"
print_diff "claude rules" "$HOME/.claude/rules" "$DECLARED_INSTRUCTIONS" "$(list_actual_rules "$HOME/.claude/rules")"

printf "\n📎 Per-tool dirs (参考表示 / Codex・Gemini は ~/.agents/skills/ を読む):\n"
print_actual "codex" "$HOME/.codex/skills"
print_actual "gemini" "$HOME/.gemini/skills"

# 💡 セクション 5: Commands ヒント
printf "\n💡 Commands:\n"
printf "   install : mise run install [--prof <profile>]\n"
printf "   update  : mise run update  [--prof <profile>]\n"
printf "   list    : mise run list\n"
