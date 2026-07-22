#!/usr/bin/env bash
# repo-preset lib.sh の単体テスト
#
# 実行: bash mise/scripts/repo-preset/tests/lib_test.sh

set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "${TESTS_DIR}/.." && pwd)"

# shellcheck disable=SC1091
source "${LIB_DIR}/lib.sh"

c_green=$'\033[32m'
c_red=$'\033[31m'
c_yellow=$'\033[33m'
c_reset=$'\033[0m'

pass_count=0
fail_count=0
skip_count=0

_ok() {
  pass_count=$((pass_count + 1))
  printf '%s  ok%s %s\n' "$c_green" "$c_reset" "$1"
}

_fail() {
  fail_count=$((fail_count + 1))
  printf '%s  FAIL%s %s\n' "$c_red" "$c_reset" "$1"
  [[ -n "${2:-}" ]] && printf '       %s\n' "$2"
}

_skip() {
  skip_count=$((skip_count + 1))
  printf '%s  skip%s %s\n' "$c_yellow" "$c_reset" "$1"
}

# 出力(複数行文字列)に語が全て含まれるか
assert_contains_all() {
  local desc="$1" haystack="$2"
  shift 2
  local word missing=()
  for word in "$@"; do
    if ! grep -qxF "$word" <<<"$haystack"; then
      missing+=("$word")
    fi
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    _ok "$desc"
  else
    _fail "$desc" "missing: ${missing[*]}"
  fi
}

assert_not_contains() {
  local desc="$1" haystack="$2" needle="$3"
  if grep -qxF "$needle" <<<"$haystack"; then
    _fail "$desc" "unexpectedly contains: $needle"
  else
    _ok "$desc"
  fi
}

assert_first_line() {
  local desc="$1" haystack="$2" expected="$3"
  local first
  first="$(head -1 <<<"$haystack")"
  if [[ "$first" == "$expected" ]]; then
    _ok "$desc"
  else
    _fail "$desc" "expected first line '$expected', got '$first'"
  fi
}

assert_failure() {
  local desc="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    _fail "$desc" "command unexpectedly succeeded: $*"
  else
    _ok "$desc"
  fi
}

assert_str_contains() {
  local desc="$1" haystack="$2" needle="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    _ok "$desc"
  else
    _fail "$desc" "expected to contain '$needle'"
  fi
}

# ---- rp_resolve_closure ----

out="$(rp_resolve_closure spell)"
assert_contains_all "rp_resolve_closure spell includes _common pre-commit spell js" "$out" \
  "_common" "pre-commit" "spell" "js"
assert_first_line "rp_resolve_closure spell starts with _common" "$out" "_common"

out="$(rp_resolve_closure textlint)"
assert_contains_all "rp_resolve_closure textlint includes _common pre-commit textlint markdown js" "$out" \
  "_common" "pre-commit" "textlint" "markdown" "js"

out="$(rp_resolve_closure toml)"
assert_contains_all "rp_resolve_closure toml includes _common pre-commit toml" "$out" \
  "_common" "pre-commit" "toml"
assert_not_contains "rp_resolve_closure toml does not include js" "$out" "js"

assert_failure "rp_resolve_closure foobar fails" rp_resolve_closure foobar

# process substitution 経路でも全件出ること（set -e 下で `<(...)` の
# subshell に errexit が継承されても途中で打ち切られない回帰テスト）。
ps_out=""
while IFS= read -r _c; do ps_out+="${_c}"$'\n'; done < <(rp_resolve_closure spell)
assert_contains_all "rp_resolve_closure spell via process-substitution includes all" "$ps_out" \
  "_common" "pre-commit" "spell" "js"

# ---- rp_selectable_components ----

out="$(rp_selectable_components)"
assert_not_contains "rp_selectable_components excludes js (HIDDEN=1)" "$out" "js"
if grep -qxF "markdown" <<<"$out"; then
  _ok "rp_selectable_components includes markdown"
else
  _fail "rp_selectable_components includes markdown"
fi

# ---- rp_merge_mise_toml ----

tmp_toml="$(mktemp)"
rp_merge_mise_toml "$tmp_toml" markdown js

tools_section_count="$(grep -c '^\[tools\]$' "$tmp_toml" || true)"
if [[ "$tools_section_count" -eq 1 ]]; then
  _ok "rp_merge_mise_toml produces exactly one [tools] section"
else
  _fail "rp_merge_mise_toml produces exactly one [tools] section" "found ${tools_section_count}"
fi

if grep -q '^dprint = ' "$tmp_toml" && grep -q '^node = ' "$tmp_toml"; then
  _ok "rp_merge_mise_toml includes dprint and node in [tools]"
else
  _fail "rp_merge_mise_toml includes dprint and node in [tools]"
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 -c '
import sys
try:
    import tomllib
except ImportError:
    sys.exit(2)
with open(sys.argv[1], "rb") as fh:
    tomllib.load(fh)
' "$tmp_toml"; then
    _ok "rp_merge_mise_toml output is valid TOML"
  else
    rc=$?
    if [[ "$rc" -eq 2 ]]; then
      _skip "rp_merge_mise_toml output is valid TOML (tomllib unavailable)"
    else
      _fail "rp_merge_mise_toml output is valid TOML"
    fi
  fi
else
  _skip "rp_merge_mise_toml output is valid TOML (python3 unavailable)"
fi
rm -f "$tmp_toml"

# ---- rp_generate_aggregate_tasks ----

out="$(rp_generate_aggregate_tasks markdown shell)"
if [[ "$out" == *'"markdown:lint"'* && "$out" == *'"shell:lint"'* ]]; then
  _ok "rp_generate_aggregate_tasks includes markdown:lint and shell:lint in depends"
else
  _fail "rp_generate_aggregate_tasks includes markdown:lint and shell:lint in depends" "$out"
fi

# ---- rp_compose_dependabot ----

tmp_yml="$(mktemp)"
rp_compose_dependabot "$tmp_yml" "${COMPONENTS_DIR}/github/.github/dependabot.yml" python js github

assert_str_contains "rp_compose_dependabot includes uv entry" "$(cat "$tmp_yml")" 'package-ecosystem: "uv"'
assert_str_contains "rp_compose_dependabot includes npm entry" "$(cat "$tmp_yml")" 'package-ecosystem: "npm"'
assert_str_contains "rp_compose_dependabot includes github-actions entry" "$(cat "$tmp_yml")" 'package-ecosystem: "github-actions"'

gha_count="$(grep -c 'package-ecosystem: "github-actions"' "$tmp_yml" || true)"
if [[ "$gha_count" -eq 1 ]]; then
  _ok "rp_compose_dependabot does not duplicate github-actions entry"
else
  _fail "rp_compose_dependabot does not duplicate github-actions entry" "found ${gha_count}"
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 -c '
import sys
try:
    import yaml
except ImportError:
    sys.exit(2)
with open(sys.argv[1]) as fh:
    yaml.safe_load(fh)
' "$tmp_yml"; then
    _ok "rp_compose_dependabot output is valid YAML (pyyaml)"
  else
    rc=$?
    if [[ "$rc" -eq 2 ]]; then
      if command -v yamllint >/dev/null 2>&1; then
        if yamllint -d relaxed "$tmp_yml" >/dev/null 2>&1; then
          _ok "rp_compose_dependabot output is valid YAML (yamllint)"
        else
          _fail "rp_compose_dependabot output is valid YAML (yamllint)"
        fi
      else
        _skip "rp_compose_dependabot output is valid YAML (pyyaml/yamllint unavailable)"
      fi
    else
      _fail "rp_compose_dependabot output is valid YAML (pyyaml)"
    fi
  fi
else
  _skip "rp_compose_dependabot output is valid YAML (python3 unavailable)"
fi
rm -f "$tmp_yml"

# ---- rp_copy_component ----

tmp_dir="$(mktemp -d)"
out="$(rp_copy_component markdown "$tmp_dir" --dry-run)"
assert_str_contains "rp_copy_component --dry-run lists dprint.json" "$out" "dprint.json"
assert_not_contains "rp_copy_component --dry-run excludes meta.sh" "$out" "  + meta.sh"
assert_not_contains "rp_copy_component --dry-run excludes mise.fragment.toml" "$out" "  + mise.fragment.toml"
rmdir "$tmp_dir" 2>/dev/null || rm -rf "$tmp_dir"

# ---- summary ----

echo
total=$((pass_count + fail_count + skip_count))
printf '%d passed, %d failed, %d skipped (total %d)\n' "$pass_count" "$fail_count" "$skip_count" "$total"

if [[ "$fail_count" -eq 0 ]]; then
  printf '%sALL TESTS PASSED%s\n' "$c_green" "$c_reset"
  exit 0
else
  printf '%sTESTS FAILED%s\n' "$c_red" "$c_reset"
  exit 1
fi
