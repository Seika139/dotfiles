szip() {
    tgt=$(abs_path "$*")
    (cd "$HOME/programs/scribe/" && mise run encrypt "${tgt}")
}

suz() {
    tgt=$(abs_path "$*")
    (cd "$HOME/programs/scribe/" && mise run decrypt "${tgt}")
}
