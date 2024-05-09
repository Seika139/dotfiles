#!/bin/bash

# JSON 形式の文字列に含まれる余計な文字を取り除く
parse_json() {
    # 出力ファイルのパス（元のファイル名に "_modified" を追加したもの）
    output_file="${json_file%.*}_modified.${json_file##*.}"
    # ファイルが存在しない、または引数が指定されていない場合は終了
    if [ ! -f "$json_file" ]; then
        echo "指定されたファイルが存在しません: $json_file"
        return 1
    fi

    # まずバックスラッシュが連続するものを一つに置き換えて新しいファイルに出力する
    sed 's/\\\{2,\}/\\/g' "$json_file" >"$output_file"

    # \" を " に置き換える
    sed -i -e 's/\\"/"/g' "$output_file"

    # "{ と }" を { と } にする
    sed -i -e 's/"{/{/g' -e 's/}"/}/g' "$output_file"

    # 結果を出力
    echo "置換が完了しました: $output_file"
}

# 使い方（実行すると file_modified が出力される）
# parse_json file
