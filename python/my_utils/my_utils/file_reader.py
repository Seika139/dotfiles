import csv
import sys
from abc import ABC, abstractmethod
from pathlib import Path


class ReaderBase(ABC):
    def __init__(self, file_path: str | Path):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        self.file_path: Path = file_path

        # read で読み込んだファイルの内容を保持する
        self._content: str

        self._read()

    @property
    def content(self):
        """
        読み込んだファイルの内容を文字列として返す。

        Returns
        -------
        str
            ファイルの内容
        """
        if not hasattr(self, "_content"):
            self._read()
        return self._content

    @abstractmethod
    def _read(self):
        pass


class PlainTextFileReader(ReaderBase):
    def __init__(self, file_path: str | Path):
        super().__init__(file_path)

    def _read(self):
        # よく使われるエンコードでファイルの読み込みを試す
        encodings = ["utf-8-sig", "shift_jis", "ISO-8859-1"]
        for encoding in encodings:
            try:
                with self.file_path.open("r", encoding=encoding) as file:
                    self._content = file.read()
                    break
            except UnicodeDecodeError as e:
                print(f"Failed to read the file with encoding: {encoding}")
                last_exception = e
                continue  # 次のエンコーディングを試す
        else:
            # 全てのエンコーディングで失敗した場合エラーを投げる
            # 必要な属性を持つ例外を投げるとエラーの詳細を保持する
            raise UnicodeDecodeError(
                (
                    last_exception.encoding
                    if isinstance(last_exception, UnicodeDecodeError)
                    else "unknown"
                ),
                (
                    last_exception.object
                    if isinstance(last_exception, UnicodeDecodeError)
                    else b""
                ),
                (
                    last_exception.start
                    if isinstance(last_exception, UnicodeDecodeError)
                    else -1
                ),
                (
                    last_exception.end
                    if isinstance(last_exception, UnicodeDecodeError)
                    else -1
                ),
                "Unable to read the file with utf-8, shift_jis, or ISO-8859-1 encodings.",
            )


class CsvFileReader(ReaderBase):
    def __init__(
        self,
        file_path: str | Path,
        header_rows: int,
        data_types: list[str] | None = None,
    ):
        self.header_rows: int = header_rows
        super().__init__(file_path)
        self._parse_data_type(data_types)

    @property
    def headers(self) -> list[list[str]]:
        """
        ヘッダー行のリストを返す。

        Returns
        -------
        list[list[str]]
            ヘッダー行のリスト。ヘッダー行が複数行ある場合は、行ごとにリストに格納される。
        """
        if not hasattr(self, "_headers"):
            raise ValueError("File content is not read yet.")
        return self._headers

    @property
    def bodies(self) -> list[list[str | float | int]]:
        """
        ボディ（csvの中身）のリストを返す。

        Returns
        -------
        list[list[str|float|int]]
            ボディ（csvの中身）のリスト
        """
        if not hasattr(self, "_bodies"):
            raise ValueError("File content is not read yet.")
        return self._bodies

    @property
    def transposed(self) -> list[list[str | float | int]]:
        """
        ボディ（csvの中身）のリストを転置したリストを返す。

        Returns
        -------
        list[list[str|float|int]]
            ボディ（csvの中身）のリストを転置したリスト
        """
        if not hasattr(self, "_transposed"):
            raise ValueError("File content is not read yet.")
        return self._transposed

    @property
    def row_count(self) -> int:
        """
        ヘッダー行を除くデータ行数を返す。

        Returns
        -------
        int
            データ行数
        """
        if not hasattr(self, "_row_count"):
            raise ValueError("File content is not read yet.")
        return self._row_count

    @property
    def column_count(self) -> int:
        """
        列数を返す。

        Returns
        -------
        int
            列数
        """
        if not hasattr(self, "_column_count"):
            raise ValueError("File content is not read yet.")
        return self._column_count

    @property
    def column_types(self) -> list[str]:
        """
        各列のデータ型を返す。

        Returns
        -------
        list[str]
            各列のデータ型からなるリスト
        """
        if not hasattr(self, "_column_types"):
            raise ValueError("File content is not read yet.")
        return self._column_types

    def _read(self):
        # よく使われるエンコードでファイルの読み込みを試す
        encodings = ["utf-8-sig", "shift_jis", "ISO-8859-1"]
        for encoding in encodings:
            try:
                with self.file_path.open("r", encoding=encoding) as file:
                    reader = csv.reader(file)
                    matrix = [[c for c in row] for row in reader]
                    self._content = "\n".join([",".join(row) for row in matrix])
                    break
            except UnicodeDecodeError as e:
                print(f"Failed to read the file with encoding: {encoding}")
                last_exception = e
                continue  # 次のエンコーディングを試す
        else:
            # 全てのエンコーディングで失敗した場合エラーを投げる
            # 必要な属性を持つ例外を投げるとエラーの詳細を保持する
            raise UnicodeDecodeError(
                (
                    last_exception.encoding
                    if isinstance(last_exception, UnicodeDecodeError)
                    else "unknown"
                ),
                (
                    last_exception.object
                    if isinstance(last_exception, UnicodeDecodeError)
                    else b""
                ),
                (
                    last_exception.start
                    if isinstance(last_exception, UnicodeDecodeError)
                    else -1
                ),
                (
                    last_exception.end
                    if isinstance(last_exception, UnicodeDecodeError)
                    else -1
                ),
                "Unable to read the file with utf-8, shift_jis, or ISO-8859-1 encodings.",
            )

        # 行ごとに列数が異なる場合はエラーを投げる
        if not all(len(row) == len(matrix[0]) for row in matrix):
            raise ValueError("Number of columns in each row is different.")

        # ヘッダー行の行方向からなるリスト
        self._headers: list[list[str]] = matrix[: self.header_rows]

        # ボディ（csvの中身）の行方向からなるリスト
        self._bodies: list[list] = matrix[self.header_rows :]

        # 列方向の行列を作成する
        self._transposed: list[list] = [list(x) for x in zip(*self._bodies)]

        self._row_count: int = len(self._bodies)  # データ行数
        self._column_count: int = len(self._transposed)  # 列数

    def _parse_data_type(self, data_types: list[str] | None = None) -> None:
        """
        csv の各列のデータ型を解析する
        data_types が指定されている場合は、そのデータ型を使用して解析する
        data_types が指定されていない場合は、データから自動で解析する

        Parameters
        ----------
        data_types : list[str]| None, optional
            各列のデータ型, by default None
        """
        if data_types:
            if len(data_types) != self._column_count:
                raise ValueError(
                    f"指定されたデータ型の数が列数と一致しません。指定されたデータ型の数: {len(data_types)}, 列数: {self._column_count}"
                )
            for i, data_type in enumerate(data_types):
                if data_type not in ["int", "str", "float"]:
                    raise ValueError(
                        f"不正なデータ型が指定されています。指定されたデータ型: {data_type}"
                    )
                # self.transposed を data_types に従って解析する
                # とりあえず int か float に変換できる場合は変換する
                try:
                    self._transposed[i] = [
                        (
                            int(x)
                            if data_type == "int"
                            else float(x) if data_type == "float" else x
                        )
                        for x in self._transposed[i]
                    ]
                except ValueError:
                    raise ValueError(
                        f"指定されたデータ型に従って解析できませんでした。指定されたデータ型: {data_type}"
                    )
            self._column_types = data_types
        else:
            # データから自動で解析する
            column_types = []
            for i, column in enumerate(self._transposed):
                try:
                    # column に小数点が含まれている場合は float に変換する
                    # ひとつも小数点が含まれていない場合は int に変換する
                    if any("." in x for x in column):
                        columns = [float(x) for x in column]
                        column_types.append("float")
                    else:
                        columns = [int(x) for x in column]
                        column_types.append("int")
                    self._transposed[i] = columns
                except ValueError:
                    # int に変換できない値がある場合は str として扱う
                    column_types.append("str")
            self._column_types = column_types

        # bodies にデータ型を適用する
        self._bodies = [list(x) for x in zip(*self._transposed)]


def read(
    file_path: str | Path, line_break_chars: list[str] = [], wrap_length: int = 0
) -> list[str]:
    """
    ファイルを読み込んで、行ごとに分割したリストを返す。

    Parameters
    ----------
    file_path : str | Path
        読み込むファイルのパス
    line_break_chars : list[str], optional
        行の区切り文字として扱う文字のリスト, by default []
    wrap_length : int, optional
        1行が指定した文字数を超えた場合に折り返す文字数。 0 の場合は折り返さない, by default 0

    Returns
    -------
    list[str]
        ファイルの内容を行ごとに分割したリスト

    Raises
    ------
    UnicodeDecodeError
        utf-8, shift_jis, or ISO-8859-1 のいずれのエンコーディングでもファイルを読み込めなかった場合
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    # よく使われるエンコードでファイルの読み込みを試す
    encodings = ["utf-8-sig", "shift_jis", "ISO-8859-1"]
    for encoding in encodings:
        try:
            with file_path.open("r", encoding=encoding) as file:
                content = file.read()
                if line_break_chars:
                    for char in line_break_chars:
                        content = content.replace(char, "\n")
                lines = content.splitlines()
                if wrap_length > 0:
                    wrapped_lines = []
                    for line in lines:
                        while len(line) > wrap_length:
                            wrapped_lines.append(line[:wrap_length])
                            line = line[wrap_length:]
                        wrapped_lines.append(line)
                    lines = wrapped_lines
                return lines
        except UnicodeDecodeError as e:
            print(f"Failed to read the file with encoding: {encoding}")
            last_exception = e
            continue  # 次のエンコーディングを試す
    else:
        raise UnicodeDecodeError(
            (
                last_exception.encoding
                if isinstance(last_exception, UnicodeDecodeError)
                else "unknown"
            ),
            (
                last_exception.object
                if isinstance(last_exception, UnicodeDecodeError)
                else b""
            ),
            (
                last_exception.start
                if isinstance(last_exception, UnicodeDecodeError)
                else -1
            ),
            (
                last_exception.end
                if isinstance(last_exception, UnicodeDecodeError)
                else -1
            ),
            "Unable to read the file with utf-8, shift_jis, or ISO-8859-1 encodings.",
        )
