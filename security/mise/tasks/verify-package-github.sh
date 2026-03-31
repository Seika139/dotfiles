#!/usr/bin/env bash

#MISE description="Search for vulnerable packages in GitHub org repositories"
#MISE alias="vph"
#MISE quiet=true

set -eu

# ── Load common utilities ────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

# ── Constants ────────────────────────────────────────────────
DEPENDENCY_FILES=(
  "package.json"
  "package-lock.json"
  "requirements.txt"
  "pyproject.toml"
  "poetry.lock"
  "uv.lock"
  "composer.json"
  "composer.lock"
  "Brewfile"
  "scoop-export.json"
)

# ── Functions ────────────────────────────────────────────────

usage() {
  cat <<EOF
Usage: mise run verify-package [OPTIONS]

Search for vulnerable packages across GitHub organization repositories
using the GitHub Search API.

Options:
  -p, --package PACKAGES  Comma-separated list of package names to search
  -o, --org ORG           GitHub organization name (interactive if omitted)
  -h, --help              Show this help message

Examples:
  mise run verify-package --package lodash --org my-org
  mise run verify-package --package "axios,crypto-js" --org my-org
  mise run verify-package  # interactive mode with fzf
EOF
}

check_prerequisites() {
  local missing=0
  for cmd in gh jq; do
    if ! command -v "$cmd" &>/dev/null; then
      error "Required command not found: $cmd"
      missing=1
    fi
  done
  if ! command -v fzf &>/dev/null; then
    warn "fzf not found — interactive selection disabled"
  fi
  if [[ $missing -ne 0 ]]; then
    exit 1
  fi
  if ! gh auth status &>/dev/null; then
    error "Not authenticated with GitHub CLI. Run: gh auth login"
    exit 1
  fi
}

select_org() {
  local org=""

  # Use DEFAULT_GH_ORG from mise.toml if set
  if [[ -n "${DEFAULT_GH_ORG:-}" ]]; then
    org="$DEFAULT_GH_ORG"
    info "Using default org: $org"
    echo "$org"
    return
  fi

  if ! command -v fzf &>/dev/null; then
    error "No org specified and fzf not available. Use --org flag."
    exit 1
  fi

  info "Fetching GitHub organizations..."
  local orgs
  orgs=$(gh api user/orgs --jq '.[].login' 2>/dev/null) || {
    error "Failed to fetch organizations"
    exit 1
  }

  if [[ -z "$orgs" ]]; then
    error "No organizations found for your GitHub account"
    exit 1
  fi

  org=$(echo "$orgs" | fzf --prompt="Select organization > " --height=~50%) || {
    error "No organization selected"
    exit 1
  }

  echo "$org"
}

select_packages() {
  local packages=""

  # Resolve vulnerable-packages.txt relative to the security directory
  local vuln_file
  vuln_file="$(cd "${SCRIPT_DIR}/../../.." && pwd)/security/vulnerable-packages.txt"

  if command -v fzf &>/dev/null && [[ -f "$vuln_file" ]]; then
    info "Loading package candidates from vulnerable-packages.txt"
    packages=$(grep -v '^\s*#' "$vuln_file" | grep -v '^\s*$' |
      fzf --multi --prompt="Select packages (TAB to multi-select, Enter to confirm) > " \
        --height=~50% |
      tr '\n' ',') || true
    # Remove trailing comma
    packages="${packages%,}"
  fi

  if [[ -z "$packages" ]]; then
    if command -v fzf &>/dev/null && [[ -f "$vuln_file" ]]; then
      warn "No packages selected from list"
    fi
    prompt_input "Enter package names (comma-separated): "
    read -r packages </dev/tty
  fi

  if [[ -z "$packages" ]]; then
    error "No packages specified"
    exit 1
  fi

  echo "$packages"
}

search_package_in_org() {
  local pkg="$1"
  local org="$2"
  local found=0

  for filename in "${DEPENDENCY_FILES[@]}"; do
    local results
    results=$(gh search code "$pkg" \
      --owner "$org" \
      --filename "$filename" \
      --json repository,path,textMatches \
      --jq '.[] | "\(.repository.nameWithOwner)\t\(.path)"' 2>/dev/null) || continue

    if [[ -n "$results" ]]; then
      while IFS=$'\t' read -r repo path; do
        hit_arrow "$repo" "$path"
        found=$((found + 1))
      done <<<"$results"
    fi
  done

  return $found
}

# ── Argument parsing ─────────────────────────────────────────
PACKAGES=""
ORG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
  -p | --package)
    PACKAGES="$2"
    shift 2
    ;;
  -o | --org)
    ORG="$2"
    shift 2
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    error "Unknown option: $1"
    usage
    exit 1
    ;;
  esac
done

# ── Main ─────────────────────────────────────────────────────
check_prerequisites

if [[ -z "$ORG" ]]; then
  ORG=$(select_org)
fi

if [[ -z "$PACKAGES" ]]; then
  PACKAGES=$(select_packages)
fi

printf "%s%b%s%b\n" "Executing: " "${PINK}" \
  "mise run verify-package-github -o $ORG -p $PACKAGES" "${RESET}"

header "Scanning org: $ORG"

total_hits=0
pkg_count=0

IFS=',' read -ra PKG_ARRAY <<<"$PACKAGES"
for pkg in "${PKG_ARRAY[@]}"; do
  pkg=$(echo "$pkg" | xargs) # trim whitespace
  [[ -z "$pkg" ]] && continue

  pkg_count=$((pkg_count + 1))
  header "Searching: $pkg"

  hits=0
  search_package_in_org "$pkg" "$ORG" || hits=$?
  total_hits=$((total_hits + hits))

  if [[ $hits -eq 0 ]]; then
    success "No references found"
  else
    warn "Found $hits reference(s)"
  fi

  # Rate limit: gh search code allows 30 req/min
  if [[ $pkg_count -lt ${#PKG_ARRAY[@]} ]]; then
    sleep 1
  fi
done

# ── Summary ──────────────────────────────────────────────────
header "Summary"
if [[ $total_hits -gt 0 ]]; then
  warn "Found ${total_hits} total reference(s) across ${pkg_count} package(s) in org '${ORG}'"
else
  success "No references found for ${pkg_count} package(s) in org '${ORG}'"
fi
