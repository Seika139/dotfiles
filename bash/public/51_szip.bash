szip() {
  tgt=$(abs_path "$*")
  (cd "$HOME/programs/tools/zipper/" && mise run encrypt "${tgt}")
}

suz() {
  tgt=$(abs_path "$*")
  (cd "$HOME/programs/tools/zipper/" && mise run decrypt "${tgt}")
}
