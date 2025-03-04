import argparse
import difflib
from pathlib import Path

from file_reader import read


class FileComparer:
    def __init__(
        self,
        fileA: Path,
        fileB: Path,
        ignore_whitespace: bool = False,
        line_break_chars: list[str] = [],
        wrap_length: int = 0,
    ):
        self.fileA = fileA
        self.fileB = fileB
        self.linesA = read(fileA)
        self.linesB = read(fileB)

        # if ignore_whitespace:
        #     self.linesA = [line.strip() for line in self.linesA]
        #     self.linesB = [line.strip() for line in self.linesB]

        self.unified_diff = difflib.unified_diff(
            self.linesA,
            self.linesB,
            fromfile=str(self.fileA),
            tofile=str(self.fileB),
            lineterm="",
        )

        self.ndiff = difflib.ndiff(self.linesA, self.linesB)

    def get_differences(self):
        differences = [
            line
            for line in self.ndiff
            if line.startswith("- ") or line.startswith("+ ")
        ]
        return differences

    def output_differences_to_file(self):
        differences = self.get_differences()
        output_file = (
            Path(__file__).parents[1]
            / "output"
            / f"{self.fileA.stem}_vs_{self.fileB.stem}.txt"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            for line in differences:
                f.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two files with optional settings."
    )
    parser.add_argument("fileA", type=Path, help="First file to compare")
    parser.add_argument("fileB", type=Path, help="Second file to compare")
    parser.add_argument(
        "-i",
        "--ignore-whitespace",
        action="store_true",
        help="Ignore whitespace and line breaks differences",
    )
    parser.add_argument(
        "-l",
        "--line-break-chars",
        nargs="+",
        help="Characters to use as line breaks",
        default=[],
    )
    parser.add_argument(
        "-w",
        "--wrap-length",
        type=int,
        help="Wrap lines to the specified length",
        default=0,
    )

    args = parser.parse_args()

    comparer = FileComparer(
        args.fileA,
        args.fileB,
        args.ignore_whitespace,
        args.line_break_chars,
        args.wrap_length,
    )
    comparer.output_differences_to_file()


if __name__ == "__main__":
    main()


# ファイルを読み込む
# それぞれのテキストを変形する
# compareする
# 結果を出力する

# def normalize_content(content):
#     # 空白を削除し、カンマで分割した各要素をリストにまとめる
#     return [part.strip() for part in content.split(",")]


# # ファイルの内容を読み込む
# with open("develop_tools/sql_new.sql", "r", encoding="utf-8") as file1, open(
#     "develop_tools/sql_old.sql", "r", encoding="utf-8"
# ) as file2:
#     content1 = file1.read()
#     content2 = file2.read()

# # カンマごとに改行してリストに変換
# normalized_lines1 = normalize_content(content1)
# normalized_lines2 = normalize_content(content2)

# # 差分を取得
# diff = difflib.HtmlDiff().make_file(
#     normalized_lines1, normalized_lines2, fromdesc="File 1", todesc="File 2"
# )

# # 結果をHTMLファイルに保存
# with open("diff.html", "w", encoding="utf-8") as output_file:
#     output_file.write(diff)

# print("差分は'diff.html'ファイルに保存されました。ブラウザで開いて確認してください。")

# # 差分を取得
# diff = difflib.ndiff(normalized_lines1, normalized_lines2)

# # 違いがある行だけを抽出
# differences = [line for line in diff if line.startswith("- ") or line.startswith("+ ")]

# # 結果を表示
# print("違いがある行:")
# for line in differences:
#     print(line)
#     print()
