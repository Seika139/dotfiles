#!/usr/bin/env bash

# shellcheck disable=SC2034

# Common utilities for verify-package scripts
# This file is sourced by task scripts, not executed directly.

# ── Color constants ──────────────────────────────────────────
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
BOLD='\033[1m'
ORANGE='\033[38;2;250;180;100m'
PINK='\033[38;2;255;100;200m'
RESET='\033[0m'

# ── Print helpers ────────────────────────────────────────────
# All status output goes to stderr to keep stdout clean for function return values.
# Using %b to interpret escape sequences in color variables (avoids shellcheck SC2059)
info() { printf '%b%s%b\n' "${BLUE}ℹ " "$*" "${RESET}" >&2; }
success() { printf '%b%s%b\n' "${GREEN}✔ " "$*" "${RESET}" >&2; }
warn() { printf '%b%s%b\n' "${YELLOW}⚠ " "$*" "${RESET}" >&2; }
error() { printf '%b%s%b\n' "${RED}✖ " "$*" "${RESET}" >&2; }
header() { printf '\n%b%s%b\n' "${BOLD}${CYAN}── " "$*" " ──${RESET}" >&2; }

# Print a detected hit: hit_line <text> <file>
hit_line() { printf '  %b%s %b%b\n' "${RED}● ${RESET}" "$1" "${YELLOW}($2)${RESET}" "" >&2; }

# Print a detected hit with arrow: hit_arrow <repo> <path>
hit_arrow() { printf '  %b%b%s%b → %s\n' "${RED}●" "${RESET} ${BOLD}" "$1" "${RESET}" "$2" >&2; }

# Colored prompt (no newline): prompt_input <message>
# Write directly to /dev/tty so the prompt is visible even when stdout is piped
prompt_input() { printf '%b%s%b' "${CYAN}" "$*" "${RESET}" >/dev/tty; }
