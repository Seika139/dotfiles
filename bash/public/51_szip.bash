szip() {
  tgt=$(abs_path "$*")
  (cd "$HOME/programs/tools/zipper/" && mise run encrypt "${tgt}")
}

suz() {
  tgt=$(abs_path "$*")
  (cd "$HOME/programs/tools/zipper/" && mise run decrypt "${tgt}")
}

repo-preset() {
  # See: repo-preset/README.md
  tgt=$(abs_path "$*")
  local repo_root
  if [ -d "$tgt" ]; then
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      repo_root=$(git rev-parse --show-toplevel)
    else
      echo_red -n "✗ Error: "
      echo_yellow -n "'$tgt'"
      echo " is not a git repository." >&2
      return 1
    fi
  else
    echo_red -n "✗ Error: "
    echo_yellow -n "'$tgt'"
    echo " is not a valid directory." >&2
    return 1
  fi
  (cd "$DOTPATH" && mise trust -a && mise run repo-preset-install --target "${repo_root}")
}
