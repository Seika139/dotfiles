import argparse
import difflib
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
        context: bool = False,
    ) -> None:
        # 2つのシーケンスの差分をHTML形式でファイルに保存します。

        FileScribe().write(
            filepath,
            difflib.HtmlDiff().make_file(
                self.str_list_1, self.str_list_2, fromdesc, todesc, context
            ),
        )


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

    args = parser.parse_args()
    max_arg_length = max(
        len(arg) for arg in ["ignore_whitespace", "line_break_chars", "wrap_length"]
    )
    print("\n[Settings]")
    for arg in ["ignore_whitespace", "line_break_chars", "wrap_length"]:
        print(f"{arg.ljust(max_arg_length)}: {getattr(args, arg)}")
    print()
    return args


def split_and_join(contents: list[str], split_char: str) -> list[str]:
    """
    文字列のリストについて、それぞれの要素を split_char で分割し、分割に使用した文字列を含めてリストにします。

    例:
    split_and_join(["a-b-c", "d-e-f"], "-") -> ["a-", "b-", "c", "d-", "e-", "f"]
    """
    result = []
    for element in contents:
        parts = element.split(split_char)
        result.extend([part + split_char for part in parts[:-1]])
        result.append(parts[-1])
    return result


def main():
    args = get_args()

    # 引数で指定されたファイルを読み込む
    scribe1 = FileScribe()
    scribe1.read(args.fileA)
    scribe2 = FileScribe()
    scribe2.read(args.fileB)

    content1 = scribe1.content.splitlines()
    content2 = scribe2.content.splitlines()
    if len(content1) == 1 and len(content2) > 1:
        content1 = [" ".join(content1)]
        content2 = [" ".join(content2)]
    elif len(content1) > 1 and len(content2) == 1:
        content1 = [" ".join(content1)]
        content2 = [" ".join(content2)]

    # Optional: --line-break-chars オプションで指定された文字列でテキストを分割する
    for split_char in args.line_break_chars:
        content1 = split_and_join(content1, split_char)
        content2 = split_and_join(content2, split_char)

    # Optional: --ignore-whitespace オプションで空白と改行の違いを無視する
    if args.ignore_whitespace:
        content1 = [line.strip() for line in content1]
        content1 = [l for l in content1 if l != ""]
        content2 = [line.strip() for line in content2]
        content2 = [l for l in content2 if l != ""]

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

    line_count_1 = len(content1)
    line_count_2 = len(content2)

    max_text_length_1 = max(len(line) for line in content1)
    max_text_length_2 = max(len(line) for line in content2)

    print(f"{scribe1.filepath}")
    print(
        f"encode: {scribe1.encoding}\t行数: {line_count_1}\t 一行の最大文字数: {max_text_length_1}\n"
    )
    print(f"{scribe2.filepath}")
    print(
        f"encode: {scribe2.encoding}\t行数: {line_count_2}\t 一行の最大文字数: {max_text_length_2}\n"
    )

    save_dir = (
        Path(__file__).parents[1]
        / "output"
        / f"{scribe1.filepath.stem}_vs_{scribe2.filepath.stem}"
    )
    save_dir.mkdir(exist_ok=True)

    comparer = Comparer(content1, content2)
    comparer.save_ndiff(save_dir / "ndiff.txt")
    comparer.save_unified_diff(save_dir / "unified_diff.txt")
    comparer.save_short_diff(save_dir / "short_diff.txt")

    # 全部の行を表示する
    comparer.save_html_diff(
        save_dir / "diff_all.html",
        scribe1.filepath.name,
        scribe2.filepath.name,
        False,
    )

    # 差分の周辺のみを表示する
    comparer.save_html_diff(
        save_dir / "diff_context.html",
        scribe1.filepath.name,
        scribe2.filepath.name,
        True,
    )

    print(
        "[Result]\nndiff:",
        len(comparer.ndiff),
        "行\tunified_diff:",
        len(comparer.unified_diff),
        "行\tshort_diff:",
        len(comparer.short_diff),
        "行\n差分は以下のディレクトリに保存されました:",
        save_dir,
    )


if __name__ == "__main__":
    """
    実行例
    python file_comparer.py sample/sample1.txt sample/sample2.txt -i -l '),' '\t' -w 60
    """
    main()
