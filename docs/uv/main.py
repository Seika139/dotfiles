import sys
from pathlib import Path


def main():
    version: str = sys.version.split()[0]
    prefix: str = Path(sys.prefix).as_posix()
    print(f"Python Version: {version}")
    print(f"Python Prefix : {prefix}")


if __name__ == "__main__":
    main()
