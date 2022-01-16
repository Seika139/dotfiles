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
for bashrc in ${BDOTDIR}/public/* ${BDOTDIR}/private/*; do
    echo "loading ${bashrc}"
    source ${bashrc}
done

cat <<EOS

Finish loading bashrc files
type "hlp" if you want some help

EOS
