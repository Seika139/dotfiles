szip() {
    tgt=$(abs_path "$*")
    (cd "$HOME/programs/scribe/" && make zip "TGT=${tgt}")
}

suz() {
    tgt=$(abs_path "$*")
    (cd "$HOME/programs/scribe/" && make unzip "TGT=${tgt}")
}
