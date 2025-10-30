class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    DEFAULT = "\033[0m"


class ColorPrinter:
    def __init__(self, color: str = Colors.DEFAULT):
        self.color = color

    def set_color(self, color: str) -> None:
        self.color = color

    def __call__(self, msg: str) -> None:
        print(f"{self.color}{msg}{Colors.DEFAULT}")
