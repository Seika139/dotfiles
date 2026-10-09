#!/usr/bin/env bash
# grm の統合テスト
#
# 実行: bash bash/tests/grm_test.sh

set -euo pipefail

TEST_ROOT=$(mktemp -d)
trap 'rm -rf "${TEST_ROOT}"' EXIT

ORIGIN="${TEST_ROOT}/origin.git"
REPO="${TEST_ROOT}/repo"

echo_yellow() {
  printf '%s\n' "$*"
}

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../public/12_git_alias.bash
source "${TEST_DIR}/../public/12_git_alias.bash"

pass_count=0
fail_count=0

_ok() {
  pass_count=$((pass_count + 1))
  printf 'ok %s\n' "$1"
}

_fail() {
  fail_count=$((fail_count + 1))
  printf 'FAIL %s\n' "$1"
  if [[ -n "${2:-}" ]]; then
    printf '  %s\n' "$2"
  fi
  return 0
}

assert_branch_exists() {
  local branch="$1" expected="$2" actual
  if git -C "${REPO}" show-ref --verify --quiet "refs/heads/${branch}"; then
    actual="present"
  else
    actual="absent"
  fi
  if [[ "${actual}" == "${expected}" ]]; then
    _ok "branch ${branch} is ${expected}"
  else
    _fail "branch ${branch} is ${expected}" "actual: ${actual}"
  fi
}

assert_worktree_exists() {
  local path="$1" expected="$2" actual
  if [[ -d "${path}" ]]; then
    actual="present"
  else
    actual="absent"
  fi
  if [[ "${actual}" == "${expected}" ]]; then
    _ok "worktree ${path##*/} is ${expected}"
  else
    _fail "worktree ${path##*/} is ${expected}" "actual: ${actual}"
  fi
}

new_branch() {
  local branch="$1" file="$2" content="$3"
  git -C "${REPO}" switch main >/dev/null
  git -C "${REPO}" switch -c "${branch}" >/dev/null
  printf '%s\n' "${content}" >"${REPO}/${file}"
  git -C "${REPO}" add "${file}"
  git -C "${REPO}" commit -m "add ${file}" >/dev/null
  git -C "${REPO}" push -u origin "${branch}" >/dev/null
}

merge_normally_and_delete_remote() {
  local branch="$1" worktree_path="$2"
  git -C "${REPO}" switch main >/dev/null
  git -C "${REPO}" merge --no-ff "${branch}" -m "merge ${branch}" >/dev/null
  git -C "${REPO}" push origin main >/dev/null
  git -C "${REPO}" push origin --delete "${branch}" >/dev/null
  git -C "${REPO}" worktree add "${worktree_path}" "${branch}" >/dev/null
}

create_squash_candidate() {
  local branch="$1" file="$2" worktree_path="$3"
  new_branch "${branch}" "${file}" "${branch}"
  git -C "${REPO}" switch main >/dev/null
  git -C "${REPO}" merge --squash "${branch}" >/dev/null
  git -C "${REPO}" commit -m "squash ${branch}" >/dev/null
  git -C "${REPO}" push origin main >/dev/null
  git -C "${REPO}" push origin --delete "${branch}" >/dev/null
  git -C "${REPO}" worktree add "${worktree_path}" "${branch}" >/dev/null
}

git init --bare --initial-branch=main "${ORIGIN}" >/dev/null
git clone "${ORIGIN}" "${REPO}" >/dev/null 2>&1
git -C "${REPO}" config user.name "grm test"
git -C "${REPO}" config user.email "grm@example.invalid"
git -C "${REPO}" commit --allow-empty -m "initial commit" >/dev/null
git -C "${REPO}" push -u origin main >/dev/null
git -C "${REPO}" remote set-head origin main

new_branch normal normal.txt normal
merge_normally_and_delete_remote normal "${TEST_ROOT}/wt-normal"

new_branch squash squash.txt squash
git -C "${REPO}" switch main >/dev/null
git -C "${REPO}" merge --squash squash >/dev/null
git -C "${REPO}" commit -m "squash squash" >/dev/null
git -C "${REPO}" push origin main >/dev/null
git -C "${REPO}" push origin --delete squash >/dev/null
git -C "${REPO}" worktree add "${TEST_ROOT}/wt-squash" squash >/dev/null

new_branch unmerged unmerged.txt unmerged
git -C "${REPO}" switch main >/dev/null
git -C "${REPO}" push origin --delete unmerged >/dev/null
git -C "${REPO}" worktree add "${TEST_ROOT}/wt-unmerged" unmerged >/dev/null

new_branch dirty dirty.txt dirty
merge_normally_and_delete_remote dirty "${TEST_ROOT}/wt-dirty"
printf '%s\n' "modified" >>"${TEST_ROOT}/wt-dirty/dirty.txt"
printf '%s\n' "untracked" >"${TEST_ROOT}/wt-dirty/untracked.txt"

new_branch locked locked.txt locked
merge_normally_and_delete_remote locked "${TEST_ROOT}/wt-locked"
git -C "${REPO}" worktree lock --reason "grm test" "${TEST_ROOT}/wt-locked"

# origin/main には含まれないローカル main のコミットを、削除根拠にしないこと。
new_branch local-only local-only.txt local-only
git -C "${REPO}" switch main >/dev/null
git -C "${REPO}" merge --no-ff local-only -m "merge local-only locally" >/dev/null
git -C "${REPO}" push origin --delete local-only >/dev/null
git -C "${REPO}" worktree add "${TEST_ROOT}/wt-local-only" local-only >/dev/null

if (cd "${REPO}" && grm) >"${TEST_ROOT}/grm.log" 2>&1; then
  cat "${TEST_ROOT}/grm.log"
  _fail "grm returns failure when candidates must be retained"
else
  cat "${TEST_ROOT}/grm.log"
  _ok "grm reports candidates that must be retained"
fi

assert_branch_exists normal absent
assert_worktree_exists "${TEST_ROOT}/wt-normal" absent
assert_branch_exists squash absent
assert_worktree_exists "${TEST_ROOT}/wt-squash" absent
assert_branch_exists unmerged present
assert_worktree_exists "${TEST_ROOT}/wt-unmerged" present
assert_branch_exists dirty present
assert_worktree_exists "${TEST_ROOT}/wt-dirty" present
if [[ -f "${TEST_ROOT}/wt-dirty/untracked.txt" ]]; then
  _ok "untracked file in dirty worktree is preserved"
else
  _fail "untracked file in dirty worktree is preserved"
fi
assert_branch_exists locked present
assert_worktree_exists "${TEST_ROOT}/wt-locked" present
assert_branch_exists local-only present
assert_worktree_exists "${TEST_ROOT}/wt-local-only" present

new_branch cwd cwd.txt cwd
merge_normally_and_delete_remote cwd "${TEST_ROOT}/wt-cwd"
if (cd "${TEST_ROOT}/wt-cwd" && grm) >"${TEST_ROOT}/grm-cwd.log" 2>&1; then
  _fail "grm returns failure when the current directory is inside a candidate worktree"
else
  _ok "grm reports a candidate worktree containing the current directory"
fi
assert_branch_exists cwd present
assert_worktree_exists "${TEST_ROOT}/wt-cwd" present

# duplicate checkout は最初の path だけを消さず、branch と両 worktree を残す。
create_squash_candidate duplicate duplicate.txt "${TEST_ROOT}/wt-duplicate-1"
git -C "${REPO}" worktree add --force "${TEST_ROOT}/wt-duplicate-2" duplicate >/dev/null

# branch tip が worktree 状態確認後に進んだ場合は、削除前の再確認で止める。
create_squash_candidate race-before race-before.txt "${TEST_ROOT}/wt-race-before"
# worktree の取り外し中に tip が進んでも、削除前の OID 再確認で新 tip を保護する。
create_squash_candidate race-after race-after.txt "${TEST_ROOT}/wt-race-after"
RACE_BEFORE_OLD_OID=$(git -C "${REPO}" rev-parse refs/heads/race-before)
RACE_AFTER_OLD_OID=$(git -C "${REPO}" rev-parse refs/heads/race-after)

# shellcheck disable=SC2032 # Test-only wrapper intercepts grm commands, not xargs.
git() {
  if [[ "$1" == "-C" && "$3" == "status" && "${2##*/}" == "wt-race-before" ]]; then
    command git "$@"
    local git_status=$?
    if [[ "${git_status}" -ne 0 ]]; then
      return "${git_status}"
    fi
    printf '%s\n' "concurrent update" >"${2}/race-update.txt"
    command git -C "$2" add race-update.txt || return $?
    command git -C "$2" commit -m "advance race-before during status check" >/dev/null || return $?
    return 0
  fi

  if [[ "$1" == "-C" && "$3" == "worktree" && "$4" == "remove" && "${5##*/}" == "wt-race-after" ]]; then
    printf '%s\n' "concurrent update" >"${5}/race-update.txt"
    command git -C "$5" add race-update.txt || return $?
    command git -C "$5" commit -m "advance race-after during removal" >/dev/null || return $?
  fi

  command git "$@"
}

if (cd "${REPO}" && grm) >"${TEST_ROOT}/grm-race.log" 2>&1; then
  _fail "grm reports branch ref races"
else
  _ok "grm reports branch ref races"
fi
assert_branch_exists race-before present
assert_worktree_exists "${TEST_ROOT}/wt-race-before" present
assert_branch_exists race-after present
assert_worktree_exists "${TEST_ROOT}/wt-race-after" absent
assert_branch_exists duplicate present
assert_worktree_exists "${TEST_ROOT}/wt-duplicate-1" present
assert_worktree_exists "${TEST_ROOT}/wt-duplicate-2" present
RACE_BEFORE_NEW_OID=$(git -C "${REPO}" rev-parse refs/heads/race-before)
RACE_AFTER_NEW_OID=$(git -C "${REPO}" rev-parse refs/heads/race-after)
if [[ "${RACE_BEFORE_NEW_OID}" != "${RACE_BEFORE_OLD_OID}" && -f "${TEST_ROOT}/wt-race-before/race-update.txt" ]]; then
  _ok "tip advanced after status check is retained with its worktree"
else
  _fail "tip advanced after status check is retained with its worktree"
fi
if [[ "${RACE_AFTER_NEW_OID}" != "${RACE_AFTER_OLD_OID}" ]]; then
  _ok "tip advanced during worktree removal is retained by pre-delete OID recheck"
else
  _fail "tip advanced during worktree removal is retained by pre-delete OID recheck"
fi

# custom merge driver があれば、squash 判定で worktree やブランチを削除しない。
ORIGIN="${TEST_ROOT}/custom-origin.git"
REPO="${TEST_ROOT}/custom-repo"
git init --bare --initial-branch=main "${ORIGIN}" >/dev/null
git clone "${ORIGIN}" "${REPO}" >/dev/null 2>&1
git -C "${REPO}" config user.name "grm test"
git -C "${REPO}" config user.email "grm@example.invalid"
git -C "${REPO}" commit --allow-empty -m "initial commit" >/dev/null
git -C "${REPO}" push -u origin main >/dev/null
git -C "${REPO}" remote set-head origin main
new_branch custom-squash custom-squash.txt custom-squash
git -C "${REPO}" switch main >/dev/null
git -C "${REPO}" merge --squash custom-squash >/dev/null
git -C "${REPO}" commit -m "squash custom-squash" >/dev/null
git -C "${REPO}" push origin main >/dev/null
git -C "${REPO}" push origin --delete custom-squash >/dev/null
git -C "${REPO}" worktree add "${TEST_ROOT}/wt-custom-squash" custom-squash >/dev/null
git -C "${REPO}" config merge.custom.driver "cat %O > %A"
if (cd "${REPO}" && grm) >"${TEST_ROOT}/grm-custom-driver.log" 2>&1; then
  _fail "grm returns failure when custom merge driver disables squash detection"
else
  _ok "grm reports a squash candidate when a custom merge driver is configured"
fi
assert_branch_exists custom-squash present
assert_worktree_exists "${TEST_ROOT}/wt-custom-squash" present

printf 'Passed: %d, failed: %d\n' "${pass_count}" "${fail_count}"
[[ "${fail_count}" -eq 0 ]]
