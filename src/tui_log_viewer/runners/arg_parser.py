import argparse
from collections.abc import Sequence
from pathlib import Path


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CLI utility to display log files with follow."
    )
    parser.add_argument("INPUT", type=Path, help="Directory or log file")
    parser.add_argument(
        "-e",
        "--engine",
        type=str,
        required=True,
        help="Engine to use, log or tui",
        choices=["log", "tui"],
    )
    parser.add_argument("-n", type=int, help="Number of lines to parse", default=10)
    parser.add_argument(
        "-f", "--follow", action="store_true", help="Follow log entries"
    )

    args = parser.parse_args(argv)

    if args.engine == "log":
        if not args.INPUT.is_file():
            parser.error("INPUT must be an existing log file when using --engine log")
        if args.INPUT.suffix.lower() != ".log":
            parser.error("INPUT must have a .log extension when using --engine log")
    elif args.engine == "tui":
        if not args.INPUT.is_dir():
            parser.error("INPUT must be an existing directory when using --engine tui")

    return args
