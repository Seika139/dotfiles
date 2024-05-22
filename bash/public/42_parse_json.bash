#!/bin/bash

# JSON 形式の文字列に含まれる余計な文字を取り除く
parse_json() {
    # ファイルが指定されていて、かつ存在しない場合はエラーメッセージを表示して終了
    if [ "$#" -gt 0 ] && [ ! -f "$1" ]; then
        echo "指定されたファイルが存在しません: $1" >&2
        return 1
    fi

    # 引数が指定されている場合はそのファイルを読み込み、そうでない場合は標準入力から読み込む
    if [ "$#" -gt 0 ]; then
        input="$1"
    else
        input="-" # ハイフンはsedで標準入力を意味する
    fi

    # 処理した結果を標準出力に送る
    # まずバックスラッシュが連続するものを一つに置き換える
    sed 's/\\\{2,\}/\\/g' "$input" |

        # 続けて \" を " に置き換える
        sed -e 's/\\"/"/g' |

        # "{ と }" を { と } にする
        sed -e 's/"{/{/g' -e 's/}"/}/g'

    # 処理結果は標準出力に送る
}

# スクリプトの使用例
# ファイル名を指定して実行する場合:
# parse_json "input.json"

# 標準入力からデータを受け取る場合（パイプを使用するなど）:
# cat "input.json" | parse_json
# echo '{"key":"value\\"example\\""}' | parse_json

parse2_json() {
    # ファイルが指定されていて、かつ存在しない場合はエラーメッセージを表示して終了
    if [ "$#" -gt 0 ] && [ ! -f "$1" ]; then
        echo "指定されたファイルが存在しません: $1" >&2
        return 1
    fi

    # 引数が指定されている場合はそのファイルを読み込み、そうでない場合は標準入力から読み込む
    if [ "$#" -gt 0 ]; then
        input="$1"
    else
        input="-" # ハイフンはsedで標準入力を意味する
    fi

    # 処理した結果を標準出力に送る
    # まずバックスラッシュが連続するものを一つに置き換える
    sed 's/\\\{2,\}/\\/g' "$input" |

        # 続けて \" を ' に置き換える
        sed "s/\\\\\"/'/g" |

        # "{ と }" を { と } にする
        sed -e 's/"{/{/g' -e 's/}"/}/g' |

        # "\\{closure}" を "\\{closure}\" に置き換える
        sed 's/\\{closure}/\\{closure}"/g' |

        # バックスラッシュが連続するものはそのまま残し、単一のバックスラッシュを二つに置き換える
        sed 's/\\\([^\\]\|$\)/\\\\\1/g'

    # 処理結果は標準出力に送る
}
