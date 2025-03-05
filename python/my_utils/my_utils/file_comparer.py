import argparse
import difflib
import re
from datetime import datetime
from pathlib import Path

from file_scribe import FileScribe


class Comparer:
    """
    2つの list[str] を比較するクラス
    """

    def __init__(self, str_list_1: list[str], str_list_2: list[str]) -> None:
        if not isinstance(str_list_1, list) or not isinstance(str_list_2, list):
            raise TypeError("str_list_1 and str_list_2 must be lists.")
        if not all(isinstance(item, str) for item in str_list_1 + str_list_2):
            raise TypeError("All items in str_list_1 and str_list_2 must be strings.")
        self.str_list_1 = str_list_1
        self.str_list_2 = str_list_2
        self.ndiff = list(difflib.ndiff(self.str_list_1, self.str_list_2))
        self.unified_diff = list(difflib.unified_diff(self.str_list_1, self.str_list_2))
        self.short_diff = [
            l for l in self.ndiff if l.startswith("+ ") or l.startswith("- ")
        ]

    def save_ndiff(self, filepath: str | Path) -> None:
        FileScribe().write(filepath, "\n".join(self.ndiff))

    def save_unified_diff(self, filepath: str | Path) -> None:
        FileScribe().write(filepath, "\n".join(self.unified_diff))

    def save_short_diff(self, filepath: str | Path) -> None:
        FileScribe().write(filepath, "\n".join(self.short_diff))

    def save_html_diff(
        self,
        filepath: str | Path,
        fromdesc: str = "File A",
        todesc: str = "File B",
    ) -> None:
        # 2つのシーケンスの差分をHTML形式でファイルに保存します。

        FileScribe().write(
            filepath,
            difflib.HtmlDiff().make_file(
                self.str_list_1, self.str_list_2, fromdesc=fromdesc, todesc=todesc
            ),
        )


def process_line_break_chars(content: str, line_break_chars: list[str]) -> list[str]:
    """
    指定された line_break_chars を用いて、content を分割します
    """
    if not line_break_chars:
        return [content]

    # line_break_charsに含まれるすべての文字をエスケープして、正規表現パターンを作成します。
    split_pattern = "(" + "|".join(re.escape(char) for char in line_break_chars) + ")"
    # 正規表現パターンで content を分割します。
    normalized_content = re.split(split_pattern, content)
    normalized_content = [
        part for part in normalized_content if not re.fullmatch(split_pattern, part)
    ]
    # 分割した結果のリストを返します。
    return normalized_content


def get_args() -> argparse.Namespace:
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

    print(parser.parse_args())
    print()
    return parser.parse_args()


def main():
    args = get_args()

    # 引数で指定されたファイルを読み込む
    scribe1 = FileScribe()
    scribe1.read(args.fileA)
    scribe2 = FileScribe()
    scribe2.read(args.fileB)

    # content1 = scribe1.content.splitlines()
    content1 = "),\n".join(scribe1.content.split("),")).splitlines()
    # content1 = [
    #     " ".join(
    #         [l.strip() for l in scribe1.content.replace("\\r\\n", "\r\n").splitlines()]
    #     )
    # ]
    # content2 = scribe2.content.splitlines()
    content2 = "),\n".join(scribe2.content.split("),")).splitlines()
    # content2 = [
    #     " ".join(
    #         [l.strip() for l in scribe2.content.replace("\\r\\n", "\r\n").splitlines()]
    #     )
    # ]

    line_count_1 = len(content1)
    line_count_2 = len(content2)

    max_text_length_1 = max(len(line) for line in content1)
    max_text_length_2 = max(len(line) for line in content2)

    print(f"About {scribe1.filepath}")
    print(f"encode: {scribe1.encoding}")
    print("行数:", line_count_1)
    print("最大文字数:", max_text_length_1)
    print()
    print(f"About {scribe2.filepath}")
    print(f"encode: {scribe2.encoding}")
    print("行数:", line_count_2)
    print("最大文字数:", max_text_length_2)
    print()

    # Optional: --ignore-whitespace オプションで空白と改行の違いを無視する
    if args.ignore_whitespace:
        content1 = [line.strip() for line in content1]
        content2 = [line.strip() for line in content2]

    # Optional: --line-break-chars オプションで指定された文字列で改行を統一する
    if args.line_break_chars:
        content1 = [
            part
            for l in content1
            for part in process_line_break_chars(l, args.line_break_chars)
        ]
        content2 = [
            part
            for l in content2
            for part in process_line_break_chars(l, args.line_break_chars)
        ]

    # Optional: --wrap-length オプションで行を指定された長さで折り返す
    if args.wrap_length:
        temp_content1 = []
        for line in content1:
            while len(line) > args.wrap_length:
                temp_content1.append(line[: args.wrap_length])
                line = line[args.wrap_length :]
            temp_content1.append(line)
        content1 = temp_content1
        temp_content2 = []
        for line in content2:
            while len(line) > args.wrap_length:
                temp_content2.append(line[: args.wrap_length])
                line = line[args.wrap_length :]
            temp_content2.append(line)
        content2 = temp_content2

    # Optional: --ignore-whitespace オプションで空白と改行の違いを無視する
    if args.ignore_whitespace:
        content1 = [line.strip() for line in content1]
        content2 = [line.strip() for line in content2]

    save_dir = (
        Path(__file__).parents[1]
        / "output"
        / f"{scribe1.filepath.stem}_vs_{scribe2.filepath.stem}"
    )
    save_dir.mkdir(exist_ok=True)

    comparer = Comparer(content1, content2)
    print("違いの概要:")
    print("ndiff:", len(comparer.ndiff), "行")
    print("short_diff:", len(comparer.short_diff), "行")

    comparer.save_ndiff(save_dir / "ndiff.txt")
    comparer.save_unified_diff(save_dir / "unified_diff.txt")
    comparer.save_short_diff(save_dir / "short_diff.txt")
    comparer.save_html_diff(
        save_dir / "diff.html", scribe1.filepath.name, scribe2.filepath.name
    )


if __name__ == "__main__":
    main()
