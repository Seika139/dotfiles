import csv
from pathlib import Path


class FileScribe:
    """
    ファイルを読み書きするための基底クラス。
    Scribe は日本語で「書記官」を意味する。
    """

    def read(self, filepath: str | Path) -> None:
        """
        メジャーなエンコーディング（utf-8, shift_jis, ISO-8859-1）でファイルの読み込みを試す。
        ファイルが見つからない場合、エラーを投げる。
        読み込んだファイルの内容は self._content に格納される。

        Parameters
        ----------
        filepath : str | Path
            読み込むファイルのパス

        Raises
        ------
        FileNotFoundError
            ファイルが見つからない場合
        UnicodeDecodeError
            utf-8, shift_jis, or ISO-8859-1 のいずれのエンコーディングでもファイルを読み込めなかった場合
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        filepath = filepath.resolve()

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        self._filepath: Path = filepath

        # よく使われるエンコードでファイルの読み込みを試す
        encodings = ["utf-8", "utf-8-sig", "shift_jis", "ISO-8859-1"]
        for encoding in encodings:
            try:
                with self._filepath.open("r", encoding=encoding) as file:
                    self._content: str = file.read()
                    self._encoding: str = encoding
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

    def write(self, filepath: str | Path, content: str, append: bool = False) -> None:
        """
        filepath に content を utf-8 エンコーディングで書き込む。
        指定したファイルが存在しない場合、新規作成する。
        ファイルが存在する場合は上書きする。
        上書きではなく追記したい場合は append を True にする。

        Parameters
        ----------
        filepath : str | Path
            書き込むファイルのパス
        content : str
            書き込む内容
        append : bool, optional
            追記モードで書き込むかどうか, by default False
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        filepath = filepath.resolve()
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
        self._filepath = filepath
        mode = "a" if append else "w"
        self._encoding = "utf-8"
        with self._filepath.open(mode, encoding=self._encoding) as file:
            file.write(content)
        self._content = content

    @property
    def filepath(self) -> Path:
        """
        このインスタンスが扱うファイルのパスを返す。

        Returns
        -------
        Path
            ファイルのパス
        """
        if not hasattr(self, "_filepath"):
            raise ValueError("Attribute '_filepath' is not set.")
        return self._filepath

    @property
    def content(self) -> str:
        """
        読み込んだファイルの内容を文字列として返す。

        Returns
        -------
        str
            ファイルの内容
        """
        if not hasattr(self, "_content"):
            raise ValueError("Attribute '_content' is not set.")
        return self._content

    @property
    def encoding(self) -> str:
        """
        ファイルのエンコーディングを返す。

        Returns
        -------
        str
            ファイルのエンコーディング
        """
        if not hasattr(self, "_encoding"):
            raise ValueError("Attribute '_encoding' is not set.")
        return self._encoding


class CSVScribe(FileScribe):
    """
    CSV ファイルを読み書きするためのクラス。
    """

    def read(
        self,
        file_path: str | Path,
        header_rows: int,
        delimiter: str = ",",
        data_types: list[str] | None = None,
    ):
        """
        CSV ファイルを読み込む。
        ヘッダー行の行数を指定する。
        ヘッダー行が複数行ある場合は、行ごとにリストに格納する。
        データ型を指定することで、各列のデータ型を解析する。

        Parameters
        ----------
        file_path : str | Path
            読み込むファイルのパス
        header_rows : int
            ヘッダー行の行数
        delimiter : str, optional
            csv の場合はデフォルトのままで良い。"\t" を指定すれば tsv ファイルとして読み込める, by default ","
        data_types : list[str] | None, optional
            各列のデータ型を定義して渡すことができる, by default None
        """
        super().read(file_path)

        self._header_rows: int = header_rows
        with self._filepath.open("r", encoding=self._encoding) as file:
            reader = csv.reader(file, delimiter=delimiter)
            matrix = [[c for c in row] for row in reader]

        # 行ごとに列数が異なる場合はエラーを投げる
        if not all(len(row) == len(matrix[0]) for row in matrix):
            raise ValueError("Number of columns in each row is different.")

        # ヘッダー行の行方向からなるリスト
        self._headers: list[list[str]] = matrix[: self._header_rows]

        # ボディ（csvの中身）の行方向からなるリスト
        self._bodies: list[list] = matrix[self._header_rows :]

        # 列方向の行列を作成する
        self._transposed: list[list] = [list(x) for x in zip(*self._bodies)]

        self._row_count: int = len(self._bodies)  # データ行数
        self._column_count: int = len(self._transposed)  # 列数
        self._delimiter: str = delimiter

        self._parse_data_type(data_types)

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

    def write(
        self,
        filepath: str | Path,
        headers: list[list[str]] = [],
        bodies: list[list] = [],
        delimiter: str = ",",
        data_types: list[str] | None = None,
    ) -> None:
        """
        新規の csv ファイルを作成する。
        ヘッダー行とボディ行を指定することができる。
        ヘッダー行が複数行ある場合は、行ごとにリストに格納する。

        Parameters
        ----------
        filepath : str | Path
            作成するファイルのパス
        headers : list[list[str]], optional
            ヘッダー行からなるリスト, by default []
        bodies : list[list], optional
            ボディ行からなるリスト, by default []
        delimiter : str, optional
            "\t" を指定すれば tsv ファイルとして保存できる, by default ","
        data_types : list[str] | None, optional
            各列のデータ型を定義して渡すことができる, by default None
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        filepath = filepath.resolve()
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
        self._filepath = filepath

        # headers と bodies が list[list] であることを確認する
        if not all(isinstance(row, list) for row in headers) or not all(
            isinstance(row, list) for row in bodies
        ):
            raise ValueError("headers と bodies は list[list] である必要があります。")

        # ヘッダーとボディの列数が一致しているかチェックする
        if headers and bodies:
            if not all(len(headers[0]) == len(row) for row in bodies) or not all(
                len(headers[0]) == len(row) for row in headers
            ):
                raise ValueError("全てのデータについて列数を揃えてください。")
        matrix = headers + bodies
        self._encoding = "utf-8"
        with self._filepath.open("w", encoding=self._encoding) as file:
            writer = csv.writer(file, delimiter=delimiter, lineterminator="\n")
            writer.writerows(matrix)
        self._content = "\n".join([delimiter.join(row) for row in matrix])
        self._headers = headers
        self._bodies = bodies
        self._transposed = [list(x) for x in zip(*bodies)]
        self._row_count = len(bodies)
        self._column_count = len(bodies[0])
        self._delimiter = delimiter
        self._parse_data_type(data_types)

    def append(
        self,
        filepath: str | Path,
        matrix: list[list],
        header_rows: int | None = None,
    ) -> None:
        """
        既存の csv ファイルにデータを追記する。
        追記するデータの列数やデータ型が既存の csv と一致しているかチェックする。

        Parameters
        ----------
        filepath : str | Path
            追記するファイルのパス
        matrix : list[list]
            追記するデータ
        header_rows : int | None, optional
            一度も write していないインスタンスであれば、header_rows を指定する必要がある, by default None
        delimiter : str, optional
            _description_, by default ","

        Raises
        ------
        ValueError
            _description_
        ValueError
            _description_
        ValueError
            _description_
        ValueError
            _description_
        """
        if self._header_rows is None:
            if header_rows is None:
                raise ValueError("Attribute '_header_rows' is not set.")
            self._header_rows = header_rows
        self.read(filepath, self._header_rows)

        if not all(isinstance(row, list) for row in matrix):
            raise ValueError("matrix は list[list] である必要があります。")

        if not all(len(row) == self._column_count for row in matrix):
            raise ValueError("既存の csv と列数が一致しません。")

        # matrix の転置行列の各行を self._column_types に従って解析する
        transposed_matrix = [list(x) for x in zip(*matrix)]
        for i, column in enumerate(transposed_matrix):
            try:
                if self._column_types[i] == "int":
                    transposed_matrix[i] = [int(x) for x in column]
                elif self._column_types[i] == "float":
                    transposed_matrix[i] = [float(x) for x in column]
            except ValueError:
                raise ValueError(
                    f"既存の csv とデータ型が一致しません。列 {i} のデータ型: {self._column_types[i]}"
                )
        matrix = [list(x) for x in zip(*transposed_matrix)]

        with self._filepath.open("a", encoding=self._encoding) as file:
            writer = csv.writer(file, delimiter=self._delimiter, lineterminator="\n")
            writer.writerows(matrix)
        self._content += "\n" + "\n".join([self._delimiter.join(row) for row in matrix])
        self._bodies += matrix
        self._transposed = [list(x) for x in zip(*self._bodies)]
        self._row_count += len(matrix)

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
            raise ValueError("Attribute '_headers' is not set.")
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
            raise ValueError("Attribute '_bodies' is not set.")
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
            raise ValueError("Attribute '_transposed' is not set")
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
            raise ValueError("Attribute '_row_count' is not set.")
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
            raise ValueError("Attribute '_column_count' is not set.")
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
            raise ValueError("Attribute '_column_types' is not set.")
        return self._column_types

    @property
    def delimiter(self) -> str:
        """
        ファイルの区切り文字を返す。csv の場合は "," がデフォルト。

        Returns
        -------
        str
            csv ファイルの区切り文字
        """
        if not hasattr(self, "_delimiter"):
            raise ValueError("Attribute '_delimiter' is not set.")
        return self._delimiter
