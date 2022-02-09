#!/usr/bin/env bash

# ref : https://takuya-1st.hatenablog.jp/entry/20090828/1251474360
# ref : https://qiita.com/bezeklik/items/56a597acc2eb568860d7

export HISTCONTROL=ignoreboth
# ignorespace(空白文字で始まる行を保存しない) と ignoredups(ひとつ前の履歴エントリと一致する行を保存しない) の両方
export HISTSIZE=5000                             # historyの履歴を増やす
export HISTTIMEFORMAT='%F %T '                   # 日時を前に追加
export HISTIGNORE='history:pwd:ls:ll:w:top:df *' # 保存しないコマンド
