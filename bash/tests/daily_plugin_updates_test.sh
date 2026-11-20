#!/usr/bin/env bash

set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${TEST_DIR}/../.." && pwd)"
DEFAULT_WRAPPER="${REPO_ROOT}/bash/daily/profile/default/ponytail_plugins.sh"
TEST_TEMP="$(mktemp -d "${TEST_DIR}/.daily-plugin-test.XXXXXX")"
FAKE_BIN="${TEST_TEMP}/bin"
FAKE_HOME="${TEST_TEMP}/home"
FAKE_LOG="${TEST_TEMP}/calls.log"
ORIGINAL_PATH="$PATH"

mkdir -p "$FAKE_BIN" "$FAKE_HOME"
trap 'rm -rf "$TEST_TEMP"' EXIT

if ! command -v node >/dev/null 2>&1; then
  printf '%s\n' "SKIP: node is required by the daily plugin updater tests"
  exit 0
fi

cat >"${FAKE_BIN}/claude" <<'FAKE_CLAUDE'
#!/usr/bin/env bash

stdin_tty=no
[[ -t 0 ]] && stdin_tty=yes
printf 'claude|%s|%s|stdin-tty=%s\n' "$*" "$PWD" "$stdin_tty" >>"$FAKE_LOG"

case "$*" in
  "plugin list --json")
    [[ "${FAKE_CLAUDE_LIST_FAIL:-0}" != "1" ]] || exit 10
    printf '%s\n' "${FAKE_CLAUDE_PLUGIN_JSON:-[]}"
    ;;
  "plugin install ponytail --marketplace DietrichGebert/ponytail --scope user")
    [[ "${FAKE_CLAUDE_INSTALL_FAIL:-0}" != "1" ]] || exit 11
    ;;
  "plugin marketplace update")
    [[ "${FAKE_CLAUDE_MARKETPLACE_UPDATE_FAIL:-0}" != "1" ]] || exit 12
    ;;
  "plugin update "*)
    [[ "$*" != "plugin update ${FAKE_CLAUDE_UPDATE_FAIL_ID:-} --scope user" ]] || exit 13
    ;;
  *)
    printf 'Unexpected fake Claude invocation: %s\n' "$*" >&2
    exit 14
    ;;
esac
FAKE_CLAUDE

cat >"${FAKE_BIN}/codex" <<'FAKE_CODEX'
#!/usr/bin/env bash

stdin_tty=no
[[ -t 0 ]] && stdin_tty=yes
printf 'codex|%s|%s|stdin-tty=%s\n' "$*" "$PWD" "$stdin_tty" >>"$FAKE_LOG"

case "$*" in
  "plugin list --json")
    [[ "${FAKE_CODEX_LIST_FAIL:-0}" != "1" ]] || exit 20
    printf '%s\n' "$FAKE_CODEX_PLUGIN_JSON"
    ;;
  "plugin marketplace list --json")
    [[ "${FAKE_CODEX_MARKETPLACES_FAIL:-0}" != "1" ]] || exit 21
    printf '%s\n' "$FAKE_CODEX_MARKETPLACES_JSON"
    ;;
  "plugin list --marketplace ponytail --available --json")
    [[ "${FAKE_CODEX_AVAILABLE_FAIL:-0}" != "1" ]] || exit 22
    printf '%s\n' "$FAKE_CODEX_AVAILABLE_JSON"
    ;;
  "plugin marketplace add DietrichGebert/ponytail")
    [[ "${FAKE_CODEX_ADD_MARKETPLACE_FAIL:-0}" != "1" ]] || exit 23
    ;;
  "plugin add ponytail@ponytail")
    [[ "${FAKE_CODEX_INSTALL_FAIL:-0}" != "1" ]] || exit 24
    ;;
  "plugin marketplace upgrade")
    [[ "${FAKE_CODEX_UPGRADE_FAIL:-0}" != "1" ]] || exit 25
    ;;
  *)
    printf 'Unexpected fake Codex invocation: %s\n' "$*" >&2
    exit 26
    ;;
esac
FAKE_CODEX

chmod +x "${FAKE_BIN}/claude" "${FAKE_BIN}/codex"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  local file="$1"
  local expected="$2"
  grep -F -- "$expected" "$file" >/dev/null || fail "missing log entry: ${expected}"
}

assert_not_contains() {
  local file="$1"
  local unexpected="$2"
  if grep -F -- "$unexpected" "$file" >/dev/null; then
    fail "unexpected log entry: ${unexpected}"
  fi
}

assert_count() {
  local expected_count="$1"
  local file="$2"
  local needle="$3"
  local actual_count
  actual_count="$(grep -F -c -- "$needle" "$file" || true)"
  [[ "$actual_count" == "$expected_count" ]] || fail "expected ${expected_count} occurrences of '${needle}', got ${actual_count}"
}

# Store JSON fixtures as data; the helper does not evaluate their contents.
set_json_fixture() {
  case "$1" in
    FAKE_CLAUDE_PLUGIN_JSON)
      FAKE_CLAUDE_PLUGIN_JSON="$2"
      export FAKE_CLAUDE_PLUGIN_JSON
      ;;
    FAKE_CODEX_PLUGIN_JSON)
      FAKE_CODEX_PLUGIN_JSON="$2"
      export FAKE_CODEX_PLUGIN_JSON
      ;;
    FAKE_CODEX_MARKETPLACES_JSON)
      FAKE_CODEX_MARKETPLACES_JSON="$2"
      export FAKE_CODEX_MARKETPLACES_JSON
      ;;
    FAKE_CODEX_AVAILABLE_JSON)
      FAKE_CODEX_AVAILABLE_JSON="$2"
      export FAKE_CODEX_AVAILABLE_JSON
      ;;
    *)
      fail "unknown JSON fixture variable: $1"
      ;;
  esac
}

reset_scenario() {
  : >"$FAKE_LOG"
  unset FAKE_CLAUDE_LIST_FAIL FAKE_CLAUDE_INSTALL_FAIL FAKE_CLAUDE_MARKETPLACE_UPDATE_FAIL
  unset FAKE_CLAUDE_UPDATE_FAIL_ID FAKE_CODEX_LIST_FAIL FAKE_CODEX_MARKETPLACES_FAIL
  unset FAKE_CODEX_AVAILABLE_FAIL FAKE_CODEX_ADD_MARKETPLACE_FAIL FAKE_CODEX_INSTALL_FAIL
  unset FAKE_CODEX_UPGRADE_FAIL
  set_json_fixture FAKE_CLAUDE_PLUGIN_JSON '[]'
  set_json_fixture FAKE_CODEX_PLUGIN_JSON '{"installed":[],"available":[]}'
  set_json_fixture FAKE_CODEX_MARKETPLACES_JSON '{"marketplaces":[]}'
  set_json_fixture FAKE_CODEX_AVAILABLE_JSON '{"available":[]}'
  export FAKE_LOG HOME="$FAKE_HOME" PATH="${FAKE_BIN}:${ORIGINAL_PATH}"
}

run_common() {
  local expected_status="${1:-0}"
  local actual_status=0
  bash "$DEFAULT_WRAPPER" || actual_status=$?
  [[ "$actual_status" == "$expected_status" ]] || fail "expected updater exit ${expected_status}, got ${actual_status}"
}

# Missing Ponytail is installed, all existing enabled user plugins are updated once,
# and both CLIs refresh all registered marketplaces (including unrelated ones).
reset_scenario
set_json_fixture FAKE_CLAUDE_PLUGIN_JSON '[{"id":"shared@market-a","scope":"user","enabled":true},{"id":"shared@market-a","scope":"user","enabled":true},{"id":"disabled@market-b","scope":"user","enabled":false},{"id":"project@market-c","scope":"project","enabled":true}]'
set_json_fixture FAKE_CODEX_PLUGIN_JSON '{"installed":[{"pluginId":"other@market-a","installed":true,"enabled":true}],"available":[]}'
set_json_fixture FAKE_CODEX_MARKETPLACES_JSON '{"marketplaces":[{"name":"other","root":"/other"}]}'
run_common
assert_count 1 "$FAKE_LOG" 'claude|plugin install ponytail --marketplace DietrichGebert/ponytail --scope user'
assert_count 1 "$FAKE_LOG" 'claude|plugin marketplace update'
assert_count 1 "$FAKE_LOG" 'claude|plugin update shared@market-a --scope user'
assert_count 1 "$FAKE_LOG" 'claude|plugin update ponytail@ponytail --scope user'
assert_not_contains "$FAKE_LOG" 'claude|plugin update disabled@market-b --scope user'
assert_not_contains "$FAKE_LOG" 'claude|plugin update project@market-c --scope user'
assert_count 1 "$FAKE_LOG" 'codex|plugin marketplace add DietrichGebert/ponytail'
assert_count 1 "$FAKE_LOG" 'codex|plugin add ponytail@ponytail'
assert_count 1 "$FAKE_LOG" 'codex|plugin marketplace upgrade'
assert_contains "$FAKE_LOG" "|${FAKE_HOME}|stdin-tty=no"

# Existing Ponytail is not reinstalled or re-enabled; enabled plugin IDs are deduplicated.
reset_scenario
set_json_fixture FAKE_CLAUDE_PLUGIN_JSON '[{"id":"ponytail@ponytail","scope":"user","enabled":false},{"id":"shared@market-a","scope":"user","enabled":true},{"id":"shared@market-a","scope":"user","enabled":true}]'
set_json_fixture FAKE_CODEX_PLUGIN_JSON '{"installed":[{"pluginId":"ponytail@ponytail","installed":true,"enabled":false}],"available":[]}'
run_common
assert_not_contains "$FAKE_LOG" 'claude|plugin install ponytail'
assert_not_contains "$FAKE_LOG" 'claude|plugin update ponytail@ponytail --scope user'
assert_count 1 "$FAKE_LOG" 'claude|plugin update shared@market-a --scope user'
assert_not_contains "$FAKE_LOG" 'codex|plugin add ponytail@ponytail'
assert_not_contains "$FAKE_LOG" 'codex|plugin marketplace add DietrichGebert/ponytail'
assert_count 1 "$FAKE_LOG" 'claude|plugin marketplace update'
assert_count 1 "$FAKE_LOG" 'codex|plugin marketplace upgrade'

# Failed or malformed inventory is never treated as absence, but marketplace refreshes continue.
reset_scenario
set_json_fixture FAKE_CLAUDE_PLUGIN_JSON 'not-json'
FAKE_CODEX_LIST_FAIL=1
export FAKE_CODEX_LIST_FAIL
run_common
assert_not_contains "$FAKE_LOG" 'claude|plugin install ponytail'
assert_not_contains "$FAKE_LOG" 'codex|plugin marketplace add DietrichGebert/ponytail'
assert_count 1 "$FAKE_LOG" 'claude|plugin marketplace update'
assert_count 1 "$FAKE_LOG" 'codex|plugin marketplace upgrade'

# A registered marketplace named ponytail must prove its source before installation.
reset_scenario
set_json_fixture FAKE_CLAUDE_PLUGIN_JSON '[{"id":"ponytail@ponytail","scope":"user","enabled":true}]'
set_json_fixture FAKE_CODEX_MARKETPLACES_JSON '{"marketplaces":[{"name":"ponytail","root":"/ponytail"},{"name":"other","root":"/other"}]}'
set_json_fixture FAKE_CODEX_AVAILABLE_JSON '{"available":[{"pluginId":"ponytail@ponytail","marketplaceSource":{"sourceType":"git","source":"someone-else/ponytail"}}]}'
run_common
assert_count 1 "$FAKE_LOG" 'codex|plugin list --marketplace ponytail --available --json'
assert_not_contains "$FAKE_LOG" 'codex|plugin add ponytail@ponytail'
assert_count 1 "$FAKE_LOG" 'codex|plugin marketplace upgrade'

# An existing same-named marketplace is used only when its catalog proves the expected source.
reset_scenario
set_json_fixture FAKE_CLAUDE_PLUGIN_JSON '[{"id":"ponytail@ponytail","scope":"user","enabled":false}]'
set_json_fixture FAKE_CODEX_MARKETPLACES_JSON '{"marketplaces":[{"name":"ponytail","root":"/ponytail"}]}'
set_json_fixture FAKE_CODEX_AVAILABLE_JSON '{"available":[{"pluginId":"ponytail@ponytail","marketplaceSource":{"sourceType":"git","source":"DietrichGebert/ponytail.git"}}]}'
run_common
assert_count 1 "$FAKE_LOG" 'codex|plugin list --marketplace ponytail --available --json'
assert_count 1 "$FAKE_LOG" 'codex|plugin add ponytail@ponytail'
assert_not_contains "$FAKE_LOG" 'codex|plugin marketplace add DietrichGebert/ponytail'

# One install/update failure does not block other plugin work or the other CLI.
reset_scenario
set_json_fixture FAKE_CLAUDE_PLUGIN_JSON '[{"id":"first@market","scope":"user","enabled":true},{"id":"second@market","scope":"user","enabled":true}]'
FAKE_CLAUDE_INSTALL_FAIL=1
FAKE_CLAUDE_UPDATE_FAIL_ID='first@market'
FAKE_CLAUDE_MARKETPLACE_UPDATE_FAIL=1
FAKE_CODEX_INSTALL_FAIL=1
FAKE_CODEX_UPGRADE_FAIL=1
export FAKE_CLAUDE_INSTALL_FAIL FAKE_CLAUDE_UPDATE_FAIL_ID FAKE_CLAUDE_MARKETPLACE_UPDATE_FAIL
export FAKE_CODEX_INSTALL_FAIL FAKE_CODEX_UPGRADE_FAIL
run_common 1
assert_count 1 "$FAKE_LOG" 'claude|plugin update first@market --scope user'
assert_count 1 "$FAKE_LOG" 'claude|plugin update second@market --scope user'
assert_count 1 "$FAKE_LOG" 'codex|plugin marketplace upgrade'

# All six profiles route through the shared updater.
for profile in cg-m2-mac default hm-m1-mac win-15034 wsl-ubuntu xsv-linux-1; do
  wrapper="${REPO_ROOT}/bash/daily/profile/${profile}/ponytail_plugins.sh"
  [[ -f "$wrapper" ]] || fail "missing ${profile} wrapper"
  grep -F "exec bash \"\${DAILY_DIR}/common/update_agent_plugins.sh\"" "$wrapper" >/dev/null || fail "${profile} wrapper does not call common updater"
done

printf '%s\n' "PASS: daily plugin update behavior"
