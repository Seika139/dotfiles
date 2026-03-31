#!/usr/bin/env bash

#MISE description="Scan local filesystem for vulnerable package references"
#MISE alias="vpl"
#MISE quiet=true

set -eu

# ── Load common utilities ────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

# ── Functions ────────────────────────────────────────────────

usage() {
  cat <<EOF
Usage: mise run verify-package-local [OPTIONS]

Scan local directories for references to vulnerable packages
in dependency/lock files.

Options:
  -p, --package PACKAGES  Comma-separated list of package names to search
  -d, --dir DIRECTORY     Target directory to scan (default: current directory)
  -h, --help              Show this help message

Examples:
  mise run verify-package-local --package jq --dir ~/dotfiles
  mise run verify-package-local --package "axios,lodash"
  mise run verify-package-local  # interactive mode with fzf
EOF
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

# Normalize pip package name: lowercase + replace - with _
normalize_pip_name() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr '-' '_'
}

# ── Per-format scan functions ────────────────────────────────

scan_npm() {
  local file="$1"
  local pkg="$2"
  local found=0

  if command -v jq &>/dev/null; then
    # Search in dependencies, devDependencies, peerDependencies, optionalDependencies
    local match
    match=$(jq -r --arg p "$pkg" '
      [.dependencies, .devDependencies, .peerDependencies, .optionalDependencies]
      | map(select(. != null))
      | map(to_entries[])
      | map(select(.key == $p))
      | .[]
      | "\(.key)@\(.value)"
    ' "$file" 2>/dev/null) || true

    if [[ -n "$match" ]]; then
      while IFS= read -r line; do
        hit_line "$line" "$file"
        found=$((found + 1))
      done <<<"$match"
    fi

    # For package-lock.json: also search in packages/dependencies
    if [[ "$(basename "$file")" == "package-lock.json" ]]; then
      match=$(jq -r --arg p "$pkg" '
        (.packages // {}) | to_entries[]
        | select(.key | endswith("node_modules/" + $p))
        | "\($p)@\(.value.version // "?")"
      ' "$file" 2>/dev/null) || true

      if [[ -n "$match" ]]; then
        while IFS= read -r line; do
          hit_line "$line" "$file"
          found=$((found + 1))
        done <<<"$match"
      fi
    fi
  else
    # Fallback: plain grep
    if grep -qi "\"$pkg\"" "$file" 2>/dev/null; then
      hit_line "$pkg found" "$file"
      found=1
    fi
  fi

  return $found
}

scan_pip() {
  local file="$1"
  local pkg="$2"
  local found=0
  local norm_pkg
  norm_pkg=$(normalize_pip_name "$pkg")

  # Build regex: match both - and _ variants, case-insensitive
  local pattern

  pattern="${norm_pkg//_/[-_]}"
  case "$(basename "$file")" in
  requirements*.txt)
    local match
    match=$(grep -iE "^${pattern}([>=<!\[;[:space:]]|$)" "$file" 2>/dev/null) || true
    if [[ -n "$match" ]]; then
      while IFS= read -r line; do
        hit_line "$line" "$file"
        found=$((found + 1))
      done <<<"$match"
    fi
    ;;
  pyproject.toml)
    local match
    match=$(grep -iE "\"${pattern}([>=<!\[]|\")" "$file" 2>/dev/null) || true
    if [[ -z "$match" ]]; then
      match=$(grep -iE "'${pattern}([>=<!\[]|')" "$file" 2>/dev/null) || true
    fi
    if [[ -n "$match" ]]; then
      while IFS= read -r line; do
        # shellcheck disable=SC2001
        line=$(echo "$line" | sed 's/^[[:space:]]*//')
        hit_line "$line" "$file"
        found=$((found + 1))
      done <<<"$match"
    fi
    ;;
  poetry.lock)
    local match
    match=$(grep -iE "^name = \"${pattern}\"" "$file" 2>/dev/null) || true
    if [[ -n "$match" ]]; then
      hit_line "$match" "$file"
      found=1
    fi
    ;;
  uv.lock)
    local match
    match=$(grep -iE "^name = \"${pattern}\"" "$file" 2>/dev/null) || true
    if [[ -n "$match" ]]; then
      hit_line "$match" "$file"
      found=1
    fi
    ;;
  esac

  return $found
}

scan_scoop() {
  local file="$1"
  local pkg="$2"
  local found=0

  if command -v jq &>/dev/null; then
    local match
    match=$(jq -r --arg p "$pkg" '
      .apps[]? | select(.Name | ascii_downcase == ($p | ascii_downcase))
      | "\(.Name) (source: \(.Source // "unknown"))"
    ' "$file" 2>/dev/null) || true

    if [[ -n "$match" ]]; then
      while IFS= read -r line; do
        hit_line "$line" "$file"
        found=$((found + 1))
      done <<<"$match"
    fi
  else
    if grep -qi "\"$pkg\"" "$file" 2>/dev/null; then
      hit_line "$pkg found" "$file"
      found=1
    fi
  fi

  return $found
}

scan_composer() {
  local file="$1"
  local pkg="$2"
  local found=0

  if command -v jq &>/dev/null; then
    local match

    if [[ "$(basename "$file")" == "composer.json" ]]; then
      # Search in require and require-dev
      match=$(jq -r --arg p "$pkg" '
        [.require, .["require-dev"]]
        | map(select(. != null))
        | map(to_entries[])
        | map(select(.key == $p))
        | .[]
        | "\(.key)@\(.value)"
      ' "$file" 2>/dev/null) || true
    else
      # composer.lock: search in packages and packages-dev
      match=$(jq -r --arg p "$pkg" '
        [.packages, .["packages-dev"]]
        | map(select(. != null))
        | map(.[]?)
        | map(select(.name == $p))
        | .[]
        | "\(.name)@\(.version)"
      ' "$file" 2>/dev/null) || true
    fi

    if [[ -n "$match" ]]; then
      while IFS= read -r line; do
        hit_line "$line" "$file"
        found=$((found + 1))
      done <<<"$match"
    fi
  else
    if grep -qi "\"$pkg\"" "$file" 2>/dev/null; then
      hit_line "$pkg found" "$file"
      found=1
    fi
  fi

  return $found
}

scan_brew() {
  local file="$1"
  local pkg="$2"
  local found=0

  local match
  match=$(grep -iE "^(brew|cask|tap)\s+['\"]${pkg}['\"]" "$file" 2>/dev/null) || true

  if [[ -n "$match" ]]; then
    while IFS= read -r line; do
      hit_line "$line" "$file"
      found=$((found + 1))
    done <<<"$match"
  fi

  return $found
}

scan_file() {
  local file="$1"
  local pkg="$2"
  local basename
  basename="$(basename "$file")"

  case "$basename" in
  package.json | package-lock.json)
    scan_npm "$file" "$pkg"
    ;;
  requirements*.txt | pyproject.toml | poetry.lock | uv.lock)
    scan_pip "$file" "$pkg"
    ;;
  composer.json | composer.lock)
    scan_composer "$file" "$pkg"
    ;;
  scoop-export.json)
    scan_scoop "$file" "$pkg"
    ;;
  Brewfile)
    scan_brew "$file" "$pkg"
    ;;
  esac
}

# ── Argument parsing ─────────────────────────────────────────
PACKAGES=""
TARGET_DIR="."

while [[ $# -gt 0 ]]; do
  case "$1" in
  -p | --package)
    PACKAGES="$2"
    shift 2
    ;;
  -d | --dir)
    TARGET_DIR="$2"
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
if [[ ! -d "$TARGET_DIR" ]]; then
  error "Directory not found: $TARGET_DIR"
  exit 1
fi

# Resolve to absolute path
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

if [[ -z "$PACKAGES" ]]; then
  PACKAGES=$(select_packages)
fi

printf "%s%b%s%b\n" "Executing: " "${PINK}" \
  "mise run verify-package-local -d $TARGET_DIR -p $PACKAGES" "${RESET}"

header "Scanning directory: $TARGET_DIR"

# Find all dependency files
info "Searching for dependency files..."
dep_files=()
while IFS= read -r -d '' file; do
  dep_files+=("$file")
done < <(find "$TARGET_DIR" \
  -type f \( \
  -name "package.json" -o \
  -name "package-lock.json" -o \
  -name "requirements*.txt" -o \
  -name "pyproject.toml" -o \
  -name "poetry.lock" -o \
  -name "uv.lock" -o \
  -name "composer.json" -o \
  -name "composer.lock" -o \
  -name "scoop-export.json" -o \
  -name "Brewfile" \
  \) \
  -not -path "*node_modules*" \
  -not -path "*.venv*" \
  -not -path "*venv*" \
  -not -path "*vendor*" \
  -not -path "*.git/*" \
  -not -path "*__pycache__*" \
  -not -path "*dist/*" \
  -not -path "*build/*" \
  -print0 2>/dev/null)

if [[ ${#dep_files[@]} -eq 0 ]]; then
  warn "No dependency files found in $TARGET_DIR"
  exit 0
fi

info "Found ${#dep_files[@]} dependency file(s)"

total_hits=0
pkg_count=0

IFS=',' read -ra PKG_ARRAY <<<"$PACKAGES"
for pkg in "${PKG_ARRAY[@]}"; do
  pkg=$(echo "$pkg" | xargs) # trim whitespace
  [[ -z "$pkg" ]] && continue

  pkg_count=$((pkg_count + 1))
  header "Searching: $pkg"

  pkg_hits=0
  for file in "${dep_files[@]}"; do
    hits=0
    scan_file "$file" "$pkg" || hits=$?
    pkg_hits=$((pkg_hits + hits))
  done

  total_hits=$((total_hits + pkg_hits))

  if [[ $pkg_hits -eq 0 ]]; then
    success "No references found"
  else
    warn "Found $pkg_hits reference(s)"
  fi
done

# ── Summary ──────────────────────────────────────────────────
header "Summary"
info "Scanned ${#dep_files[@]} dependency file(s) for ${pkg_count} package(s)"
if [[ $total_hits -gt 0 ]]; then
  warn "Found ${total_hits} total reference(s)"
else
  success "No references found"
fi
