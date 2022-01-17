#!/usr/bin/env bash

cat <<EOS
       )
    ／⌒⌒⌒ヽ                     ／⌒⌒⌒ヽ
   ﾉ ﾉﾉLL人ﾊ     きょう も     ((ﾉﾉ从从⭐️
  (_Cﾘﾟ‐ﾟﾉﾘ)     いちにち      ﾉ从ﾟヮﾟ人
  ﾉﾉ⊂)卯(つヽ    がんばろう   （(⊂ｿ辷ｿつ)
（( くzzzz> ))                  くzzzz>
     し∪                          し∪
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOS

# 上で使ってる太線は http://bubuzuke.s7.xrea.com/ISO10646/ruled.html で手に入れた

# それぞれのファイルで定義した設定を読み込む
DIRS=(
    "${BDOTDIR}/public"
    "${BDOTDIR}/private"
)

for dir in ${DIRS[@]}; do
    # .gitkeep を除くファイルが存在する時にそれらを読み込む
    if [[ $(find "${dir}" -type f | grep -v ".gitkeep" | wc -l) -gt 0 ]]; then
        for bashrc in "${dir}/*"; do
            # echo "loading ${bashrc}"
            source ${bashrc}
        done
    fi
done
unset DIRS dir bashrc

cat <<EOS

Finish loading bashrc files
type "hlp" if you want some help

EOS
